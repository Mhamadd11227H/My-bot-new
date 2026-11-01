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

COIN = "💰"            # نیشانەی دراو. دەتوانیت بیگۆڕیت بە ئیمۆجی جوڵاو: "<a:ناو:ئایدی>"
SPIN = "🎰"            # ئەو نیشانەیەی لە کاتی سووڕانەوە دەردەکەوێت

START_COINS = 500      # دراوی یەکەم جار کە کەسێک دەست پێ دەکات
DAILY_BASE = 250       # دراوی ڕۆژانە (ڕۆژی یەکەم)
DAILY_STREAK_BONUS = 50  # زیادەی هەر ڕۆژێکی بەردەوام
DAILY_MAX = 5000       # زۆرترین دراوی ڕۆژانە
DAILY_COOLDOWN = 24 * 60 * 60  # ٢٤ کاتژمێر (بە چرکە)

MAX_BET = 250_000      # زۆرترین شەرت لە یەک جار
SPIN_COOLDOWN = 8      # چەند چرکە دەبێت چاوەڕێ بکەیت لەنێوان دوو جار

# هێماکانی ماشێنەکە و ئەگەری دەرکەوتنیان
# (ژمارەی گەورەتر = زۆرتر دەردەکەوێت)
SYMBOLS = ["🍒", "🍋", "🍇", "🔔", "💎", "7️⃣"]
WEIGHTS = [30, 25, 20, 13, 8, 4]

# ئەگەر سێ هێمای وەک یەک هات، شەرتەکە چەند ئەوەندە دەبێت
PAYOUT_3 = {"🍒": 4, "🍋": 6, "🍇": 10, "🔔": 20, "💎": 40, "7️⃣": 150}

# ئەگەر تەنها دوو هێمای وەک یەک هات (شەرتەکەت دەگەڕێتەوە)
PAIR_PAYOUT = 1

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
        db.execute("INSERT INTO users (user_id, coins) VALUES (?, ?)", (user_id, START_COINS))
        db.commit()
        return START_COINS, 0.0, 0
    return row

# دراو زیاد یان کەم دەکات (بۆ کەمکردن ژمارەی سالب بنووسە)
def add_coins(user_id, amount):
    get_user(user_id)
    db.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
    db.commit()

# ═══════════════════════════════════════
# بەشی ٣: بیرکاری ماشێنەکە
# ═══════════════════════════════════════

# سێ هێما دەکێشێت و بڕی بردنەوە دیاری دەکات
def spin_result(bet):
    result = random.choices(SYMBOLS, weights=WEIGHTS, k=3)
    a, b, c = result
    if a == b == c:
        mult = PAYOUT_3[a]
    elif a == b or b == c or a == c:
        mult = PAIR_PAYOUT
    else:
        mult = 0
    return result, int(bet * mult)

# شێوەی نامەکە (وەک ماشێنی سلۆت)
def render(cells, name, bet, won=None, jackpot=False):
    row = " ".join(cells)
    line1 = f"`|` {row} `|`  **{name}** شەرتی {COIN} `{bet:,}` کرد"
    if won is None:
        line2 = "`|___________|`  ..."
    elif won == 0:
        line2 = "`|___________|`  و هەموو شتەکەی دۆڕاند 😢"
    elif jackpot:
        line2 = f"`|___________|`  و بردییەوە {COIN} `{won:,}` 🎉🎉 **JACKPOT!!**"
    else:
        line2 = f"`|___________|`  و بردییەوە {COIN} `{won:,}` !!"
    return f"**`___SLOTS___`**\n{line1}\n{line2}"

# ═══════════════════════════════════════
# بەشی ٤: فەرمانەکان
# ═══════════════════════════════════════

class SlotsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_spin = {}   # دوایین جاری هەر کەس سلۆتی کرد
        self.busy = set()     # ئەوانەی ئێستا سلۆت دەکەن

    # !cash: بڕی دراوەکەت پیشان دەدات
    @commands.command(name="cash", aliases=["bal", "money", "دراو"])
    async def cash(self, ctx):
        coins, _, _ = get_user(ctx.author.id)
        name = discord.utils.escape_markdown(ctx.author.display_name)
        await ctx.send(f"{COIN} | **{name}**، ئێستا **{coins:,}** دراوت هەیە!")

    # !daily: دراوی ڕۆژانە. بەردەوامبوون پاداشتی زیاتر دەدات
    @commands.command(name="daily")
    async def daily(self, ctx):
        uid = ctx.author.id
        name = discord.utils.escape_markdown(ctx.author.display_name)
        coins, last, streak = get_user(uid)
        now = time.time()

        # ئەگەر هێشتا ٢٤ کاتژمێر تێنەپەڕیوە
        left = last + DAILY_COOLDOWN - now
        if left > 0:
            hours, rest = divmod(int(left), 3600)
            minutes = rest // 60
            await ctx.send(f"⏳ | **{name}**، دەبێت **{hours}** کاتژمێر و **{minutes}** خولەک چاوەڕێ بکەیت!")
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
            f"🎁 | **{name}**، {COIN} **{amount:,}** دراوی ڕۆژانەت وەرگرت!\n"
            f"🔥 ڕۆژی **{streak}**ـەمینی بەردەوامی"
        )

    # !slots 100 یان !slots all: سلۆت یاری بکە
    @commands.command(name="slots", aliases=["slot", "s", "سلۆت"])
    async def slots(self, ctx, bet: str = "1"):
        uid = ctx.author.id
        name = discord.utils.escape_markdown(ctx.author.display_name)
        coins, _, _ = get_user(uid)

        # ١) بڕی شەرتەکە بخوێنەرەوە
        if bet.lower() in ("all", "هەموو"):
            amount = min(coins, MAX_BET)
        else:
            try:
                amount = int(bet.replace(",", ""))
            except ValueError:
                await ctx.send(f"🚫 | **{name}**، بڕەکە دەبێت ژمارە بێت! نموونە: `{PREFIX}slots 100`")
                return

        # ٢) پشکنینەکان
        if amount < 1:
            await ctx.send(f"🚫 | **{name}**، دراوت نییە! `{PREFIX}daily` بنووسە بۆ وەرگرتنی دراو.")
            return
        if amount > MAX_BET:
            await ctx.send(f"🚫 | **{name}**، زۆرترین شەرت {COIN} **{MAX_BET:,}**ـە!")
            return
        if amount > coins:
            await ctx.send(f"🚫 | **{name}**، دراوی پێویستت نییە! ئێستا **{coins:,}**ت هەیە.")
            return

        # ٣) چاوەڕێ (cooldown) بۆ ئەوەی کەس سپام نەکات
        now = time.time()
        wait = SPIN_COOLDOWN - (now - self.last_spin.get(uid, 0))
        if uid in self.busy or wait > 0:
            await ctx.send(f"⏳ | **{name}**، کەمێکی تر چاوەڕێ بکە!", delete_after=4)
            return

        self.busy.add(uid)
        self.last_spin[uid] = now
        try:
            # ٤) سەرەتا شەرتەکە دەکەمێتەوە، پاشان بردنەوە (ئەگەر هەبێت) دەدرێتەوە
            add_coins(uid, -amount)
            result, won = spin_result(amount)
            if won:
                add_coins(uid, won)
            jackpot = result[0] == result[1] == result[2] == "7️⃣"

            # ٥) ئانیمەیشنی سووڕانەوە: هێماکان یەک بە یەک دەردەکەون
            try:
                msg = await ctx.send(render([SPIN, SPIN, SPIN], name, amount))
                await asyncio.sleep(1)
                await msg.edit(content=render([result[0], SPIN, SPIN], name, amount))
                await asyncio.sleep(1)
                await msg.edit(content=render([result[0], result[1], SPIN], name, amount))
                await asyncio.sleep(1)
                await msg.edit(content=render(result, name, amount, won, jackpot))
            except discord.HTTPException:
                pass  # ئەگەر نامەکە سڕایەوە، کێشە نییە (دراوەکان پێشتر هەژمار کراون)
        finally:
            self.busy.discard(uid)

async def setup(bot):
    await bot.add_cog(SlotsCog(bot))
      
