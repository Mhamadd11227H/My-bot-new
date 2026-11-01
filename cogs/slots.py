import asyncio
import os
import random
import sqlite3
import time

import discord
from discord.ext import commands
from utils import PREFIX

# ═══════════════════════════════════════
# بەشی ١: ڕێکخستنەکان (لێرە دەستکاری بکە)
# ═══════════════════════════════════════

CURRENCY = "Z"          # ناوی دراو (لە هەموو نامەکان دەردەکەوێت)

START_BALANCE = 500     # دراوی یەکەم جار کە کەسێک دەست پێ دەکات
DAILY_BASE = 250        # دراوی ڕۆژانە (ڕۆژی یەکەم)
DAILY_STREAK_BONUS = 50 # زیادەی هەر ڕۆژێکی بەردەوام
DAILY_MAX = 5000        # زۆرترین دراوی ڕۆژانە
DAILY_COOLDOWN = 24 * 60 * 60  # ٢٤ کاتژمێر (بە چرکە)

MAX_BET = 50_000        # زۆرترین شەرت لە یەک جار (بۆ هەموو یارییەکان)
COOLDOWN = 8            # چەند چرکە چاوەڕێ بکەیت لەنێوان دوو یاری
SPIN_TIME = 3           # چەند چرکە سلۆت دەسووڕێتەوە پێش پیشاندانی ئەنجام

# ئەگەری بردنەوە لە سلۆت (٠.٦٠ = ٦٠٪). بردنەوە تەنها بە ٣ هێمای وەک یەک دەبێت.
# ئاگاداربە: لەگەڵ ژمارەکانی خوارەوە، ٠.٦٠ واتە یاریزان لە ناوەندیدا
# لە هەر شەرتێک ٪١٥٠ دەگەڕێتەوە (دراو زۆر زیاد دەبێت).
# بۆ ئەوەی نزیکەی ٪٩٠ بێت: WIN_CHANCE = 0.36
WIN_CHANCE = 0.60

# ئیمۆجی دراو لە یارییەکان (وەک 💵 لە OwO). دەتوانیت بیگۆڕیت بە ئیمۆجی خۆت: "<:ناو:ئایدی>"
CASH_EMOJI = "💵"

# ڕووی دراوەکە لە coinflip
HEADS_EMOJI = "🟡"
TAILS_EMOJI = "⚪"

# ئەو نووسینانەی لە سلۆت و coinflip دەردەکەون (وەک OwO). دەتوانیت بیانکەیت بە کوردی
TXT_BET = "bet"
TXT_WON = "and won"
TXT_NOTHING = "and won nothing... :c"
TXT_SPENT = "spent"
TXT_CHOSE = "and chose"
TXT_SPINS = "The coin spins..."
TXT_FLIP_WON = "and you won"
TXT_FLIP_LOST = "and you lost it all... :c"

# ئیمۆجییەکان. ئەگەر وەک نووسین (<:emoji_9:...>) دەرکەوتن، بوتەکە لەو سێرڤەرەدا
# نییە کە ئیمۆجییەکانی تێدایە. ئیمۆجییەکان لە سێرڤەرەکەی خۆت باربکە و ئایدییەکان بگۆڕە
SPIN_EMOJI = "<a:emoji_72:1536441649947869234>"

E_EGGPLANT = "<:emoji_9:1535300687288737895>"
E_GRAPE    = "<:emoji_13:1535301374252945499>"
E_ORANGE   = "<:emoji_9:1535300678497341462>"
E_CHERRY   = "<:emoji_12:1535301118362521681>"
E_DIAMOND  = "<:emoji_14:1535303848963612672>"

SLOT_ITEMS = [E_EGGPLANT, E_GRAPE, E_ORANGE, E_CHERRY, E_DIAMOND]
WEIGHTS    = [35,         25,      20,       12,       8]  # ئەگەری دەرکەوتن

# شەرتەکە چەند ئەوەندە دەبێت (شەرتەکەی خۆشت تێدایە)
# نموونە: 3 = شەرتەکەت دەگەڕێتەوە + دوو ئەوەندەی شەرتەکە وەک قازانج
MULTIPLIERS = {
    E_EGGPLANT: 1.5,
    E_GRAPE: 2.0,
    E_ORANGE: 3.0,
    E_CHERRY: 4.0,
    E_DIAMOND: 5.0,
}

# ═══════════════════════════════════════
# بەشی ٢: داتابەیس (هەڵگرتنی دراوی هەموو کەسێک)
# ═══════════════════════════════════════

# فایلی economy.db لەناو فۆڵدەری سەرەکی بوتەکە دروست دەبێت
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "economy.db")
db = sqlite3.connect(DB_PATH)
db.execute(
    "CREATE TABLE IF NOT EXISTS users ("
    "user_id INTEGER PRIMARY KEY, "
    "coins INTEGER NOT NULL DEFAULT 0, "
    "last_daily REAL NOT NULL DEFAULT 0, "
    "streak INTEGER NOT NULL DEFAULT 0)"
)
db.commit()

# زانیاری کەسێک وەردەگرێت (ئەگەر نوێ بێت، دروستی دەکات)
def get_user(user_id):
    row = db.execute(
        "SELECT coins, last_daily, streak FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row is None:
        db.execute("INSERT INTO users (user_id, coins) VALUES (?, ?)", (user_id, START_BALANCE))
        db.commit()
        return START_BALANCE, 0.0, 0
    return row

# دراو زیاد یان کەم دەکات (بۆ کەمکردن ژمارەی سالب بنووسە)
def add_coins(user_id, amount):
    get_user(user_id)
    db.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
    db.commit()

# ═══════════════════════════════════════
# بەشی ٣: بیرکاری یارییەکان
# ═══════════════════════════════════════

# سلۆت: ٣ هێما دەکێشێت. دەگەڕێنێتەوە (هێماکان، چەند ئەوەندە)
# چەند ئەوەندە = 0 واتە دۆڕان
def roll_slots():
    if random.random() < WIN_CHANCE:
        chosen = random.choices(SLOT_ITEMS, weights=WEIGHTS, k=1)[0]
        return [chosen, chosen, chosen], MULTIPLIERS[chosen]
    # دۆڕان: هەرگیز ٣ هێمای وەک یەک نابێت (دوو هێمای وەک یەکیش دۆڕانە)
    while True:
        cells = random.choices(SLOT_ITEMS, weights=WEIGHTS, k=3)
        if not (cells[0] == cells[1] == cells[2]):
            return cells, 0

# سەر و پشت: ناوە جیاوازەکان دەکات بە یەک ناو
SIDES = {
    "h": "heads", "head": "heads", "heads": "heads", "سەر": "heads",
    "t": "tails", "tail": "tails", "tails": "tails", "پشت": "tails",
}
SIDE_NAMES = {"heads": "سەر", "tails": "پشت"}

# شێوەی نامەی سلۆت: ڕێک وەک OwO (تێکستی ئاسایی، بێ Embed)
# won = None: هێشتا دەسووڕێتەوە | 0: دۆڕان | ژمارە: بڕی بردنەوە
def slots_text(cells, name, bet, won=None):
    row = " ".join(cells)
    if won is None:
        result = ""
    elif won == 0:
        result = TXT_NOTHING
    else:
        result = f"{TXT_WON} {CASH_EMOJI} {won:,}"
    return (
        "**`___SLOTS___`**\n"
        f"` ` {row} ` ` {name} {TXT_BET} {CASH_EMOJI} {bet:,}\n"
        f"`|          |` {result}\n"
        "`|          |`"
    )

# ═══════════════════════════════════════
# بەشی ٤: فەرمانەکان
# ═══════════════════════════════════════

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_use = {}  # (یاری, کەس) -> دوایین جار

    # ماوەی چاوەڕێکردن (٠ = دەتوانێت یاری بکات)
    def cooldown_left(self, game, user_id):
        used = self.last_use.get((game, user_id), 0)
        return max(COOLDOWN - (time.time() - used), 0)

    # بڕی شەرتەکە دەخوێنێتەوە و دەیپشکنێت. ئەگەر هەڵە بوو None دەگەڕێنێتەوە
    async def read_bet(self, ctx, bet, coins, example):
        name = discord.utils.escape_markdown(ctx.author.display_name)
        if bet.lower() in ("all", "max", "هەموو"):
            amount = min(coins, MAX_BET)
        else:
            try:
                amount = int(bet.replace(",", ""))
            except ValueError:
                await ctx.send(f"❌ | **{name}**، بڕی شەرتەکە دەبێت ژمارە بێت! نموونە: `{PREFIX}{example}`")
                return None

        if coins <= 0:
            await ctx.send(f"⚠️ | **{name}**، دراوت نییە! `{PREFIX}daily` بنووسە بۆ وەرگرتنی دراو.")
            return None
        if amount <= 0:
            await ctx.send(f"❌ | **{name}**، بڕی شەرت دەبێت لە ٠ زیاتر بێت!")
            return None
        if amount > MAX_BET:
            await ctx.send(f"⚠️ | **{name}**، زۆرترین شەرت **{MAX_BET:,} {CURRENCY}**ـە!")
            return None
        if amount > coins:
            await ctx.send(f"⚠️ | **{name}**، **{amount:,} {CURRENCY}**ت نییە! (باڵانسی تۆ: `{coins:,} {CURRENCY}`)")
            return None
        return amount

    # !cash: بڕی دراوەکەت پیشان دەدات
    @commands.command(name="cash", aliases=["bal", "money", "دراو"])
    async def cash(self, ctx):
        coins, _, _ = get_user(ctx.author.id)
        name = discord.utils.escape_markdown(ctx.author.display_name)
        await ctx.send(f"💰 | **{name}**، ئێستا **{coins:,} {CURRENCY}**ت هەیە!")

    # !daily: دراوی ڕۆژانە. بەردەوامبوون پاداشتی زیاتر دەدات
    @commands.command(name="daily")
    async def daily(self, ctx):
        uid = ctx.author.id
        name = discord.utils.escape_markdown(ctx.author.display_name)
        coins, last, streak = get_user(uid)
        now = time.time()

        left = last + DAILY_COOLDOWN - now
        if left > 0:
            hours, rest = divmod(int(left), 3600)
            await ctx.send(f"⏳ | **{name}**، دەبێت **{hours}** کاتژمێر و **{rest // 60}** خولەک چاوەڕێ بکەیت!")
            return

        # ئەگەر زیاتر لە ٤٨ کاتژمێر تێپەڕیبێت، بەردەوامبوون دەستپێدەکاتەوە
        if now - last > DAILY_COOLDOWN * 2:
            streak = 0
        streak += 1
        amount = min(DAILY_BASE + DAILY_STREAK_BONUS * (streak - 1), DAILY_MAX)

        db.execute(
            "UPDATE users SET coins = coins + ?, last_daily = ?, streak = ? WHERE user_id = ?",
            (amount, now, streak, uid),
        )
        db.commit()
        await ctx.send(
            f"🎁 | **{name}**، **{amount:,} {CURRENCY}**ی ڕۆژانەت وەرگرت!\n"
            f"🔥 ڕۆژی **{streak}**ـەمینی بەردەوامی"
        )

    # !slots 100 یان !slots all
    @commands.command(name="slots", aliases=["slot", "sl", "s", "سلۆت"])
    async def slots(self, ctx, bet: str = "1"):
        uid = ctx.author.id
        name = discord.utils.escape_markdown(ctx.author.display_name)
        coins, _, _ = get_user(uid)

        # ١) شەرتەکە بپشکنە
        amount = await self.read_bet(ctx, bet, coins, "slots 100")
        if amount is None:
            return

        # ٢) چاوەڕێکردن (cooldown). تەنها لە یاری ڕاستەقینە حساب دەکرێت
        wait = self.cooldown_left("slots", uid)
        if wait > 0:
            await ctx.send(f"⏱️ | **{name}**، **{wait:.1f}** چرکەی تر چاوەڕێ بکە!", delete_after=4)
            return
        self.last_use[("slots", uid)] = time.time()

        # ٣) ئەنجامەکە دیاری بکە و دراوەکان هەرزوو بگۆڕە
        cells, mult = roll_slots()
        if mult:
            # max(...): بۆ شەرتی بچووک (وەک ١) قازانجەکە هەرگیز ٠ نەبێت
            winnings = max(int(amount * mult), amount + 1)
            add_coins(uid, winnings - amount)
        else:
            winnings = 0
            add_coins(uid, -amount)

        # ٤) ئانیمەیشن: سێ هێمای سووڕاو، پاشان ئەنجامەکە (وەک OwO)
        try:
            msg = await ctx.send(slots_text([SPIN_EMOJI] * 3, name, amount))
            await asyncio.sleep(SPIN_TIME)
            await msg.edit(content=slots_text(cells, name, amount, winnings))
        except discord.HTTPException:
            pass  # ئەگەر نامەکە سڕایەوە، کێشە نییە (دراوەکان پێشتر هەژمار کراون)

    # !coinflip 100 heads  (یان: !cf 100 پشت)
    @commands.command(name="coinflip", aliases=["cf", "flip", "coin"])
    async def coinflip(self, ctx, bet: str = "1", choice: str = None):
        uid = ctx.author.id
        name = discord.utils.escape_markdown(ctx.author.display_name)
        coins, _, _ = get_user(uid)

        # ئەگەر کەسەکە سەر/پشتی پێش ژمارە نووسی (!cf heads 100)، شوێنیان دەگۆڕین
        if bet.lower() in SIDES:
            bet, choice = (choice if choice else "1"), bet

        # سەر یان پشت (ئەگەر نەنووسرابوو: سەر)
        side = SIDES.get((choice or "heads").lower())
        if side is None:
            await ctx.send(f"❌ | **{name}**، تەنها `heads` (سەر) یان `tails` (پشت) بنووسە! نموونە: `{PREFIX}cf 100 heads`")
            return

        amount = await self.read_bet(ctx, bet, coins, "cf 100 heads")
        if amount is None:
            return

        wait = self.cooldown_left("coinflip", uid)
        if wait > 0:
            await ctx.send(f"⏱️ | **{name}**، **{wait:.1f}** چرکەی تر چاوەڕێ بکە!", delete_after=4)
            return
        self.last_use[("coinflip", uid)] = time.time()

        outcome = random.choice(["heads", "tails"])
        won = side == outcome
        add_coins(uid, amount if won else -amount)

        head_line = f"🪙 | **{name}** {TXT_SPENT} {CASH_EMOJI} {amount:,} {TXT_CHOSE} **{side}**"
        faces = {"heads": HEADS_EMOJI, "tails": TAILS_EMOJI}
        if won:
            result = f"{TXT_FLIP_WON} {CASH_EMOJI} {amount * 2:,}!!"
        else:
            result = TXT_FLIP_LOST

        try:
            msg = await ctx.send(f"{head_line}\n{TXT_SPINS} {SPIN_EMOJI}")
            await asyncio.sleep(2)
            await msg.edit(content=f"{head_line}\n{TXT_SPINS} {faces[outcome]} {result}")
        except discord.HTTPException:
            pass

async def setup(bot):
    await bot.add_cog(Gambling(bot))
