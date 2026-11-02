import asyncio
import random
import time

import discord
from discord.ext import commands

from database import db, get_user, add_coins, parse_bet, transfer_coins
from utils import (
    PREFIX, CURRENCY, CASH_EMOJI, SPIN_EMOJI, HEADS_EMOJI, TAILS_EMOJI, bet_error_text,
)

# ═══════════════════════════════════════
# بەشی ١: ڕێکخستنەکان (لێرە دەستکاری بکە)
# ═══════════════════════════════════════

DAILY_MIN = 10000         # کەمترین دراوی ڕۆژانە
DAILY_MAX = 20000         # زۆرترین دراوی ڕۆژانە (هەر جارێک ژمارەیەکی هەڕەمەکی لەنێوانیان)
DAILY_COOLDOWN = 24 * 60 * 60  # ٢٤ کاتژمێر (بە چرکە)

# سنووری شەرت و چاوەڕێکردن بۆ coinflip (سلۆت ڕێکخستنی خۆی هەیە)
FLIP_MIN_BET = 1
FLIP_MAX_BET = 50_000
FLIP_COOLDOWN = 8

# ئەو نووسینانەی لە coinflip دەردەکەون (وەک OwO). دەتوانیت بیانکەیت بە کوردی
TXT_SPENT = "spent"
TXT_CHOSE = "and chose"
TXT_SPINS = "The coin spins..."
TXT_FLIP_WON = "and you won"
TXT_FLIP_LOST = "and you lost it all... :c"

# ناوە جیاوازەکانی سەر و پشت دەکات بە یەک ناو
SIDES = {
    "h": "heads", "head": "heads", "heads": "heads", "سەر": "heads",
    "t": "tails", "tail": "tails", "tails": "tails", "پشت": "tails",
}

# ═══════════════════════════════════════
# بەشی ٢: فەرمانەکان
# ═══════════════════════════════════════

# ═══════════════════════════════════════
# دڵنیابوونەوە لە ناردنی دراو (دوگمە)
# تەنها ناردەر دەتوانێت کلیک بکات. دوای ٣٠ چرکە خۆی هەڵدەوەشێتەوە
# ═══════════════════════════════════════

SEND_CONFIRM_TIMEOUT = 30

class SendConfirmView(discord.ui.View):
    def __init__(self, ctx, member, amount):
        super().__init__(timeout=SEND_CONFIRM_TIMEOUT)
        self.ctx, self.member, self.amount = ctx, member, amount
        self.message = None
        self.done = False  # ڕێگری لە دووبارە کلیککردن

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ ئەم دوگمانە بۆ کەسێکی ترە.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="دڵنیام", emoji="✅", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.done:
            return
        self.done = True
        self.stop()
        name = discord.utils.escape_markdown(self.ctx.author.display_name)
        # مامەڵەکە لێرە ئەنجام دەدرێت (ئەتۆمی). ئەگەر لەم ماوەیەدا دراوەکەت خەرج کردبێت، سەرناکەوێت
        if transfer_coins(self.ctx.author.id, self.member.id, self.amount):
            text = f"{CASH_EMOJI} | **{name}** sent **{self.amount:,} {CURRENCY}** to {self.member.mention}!"
            await interaction.response.edit_message(content=text, view=None)
        else:
            text = f"⚠️ | **{name}**، دراوی پێویستت نییە، ناردنەکە ڕاگیرا."
            await interaction.response.edit_message(content=text, view=None)

    @discord.ui.button(label="پاشگەزبوونەوە", emoji="✖️", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.done:
            return
        self.done = True
        self.stop()
        name = discord.utils.escape_markdown(self.ctx.author.display_name)
        await interaction.response.edit_message(content=f"❌ | **{name}**، ناردنەکە هەڵوەشێنرایەوە.", view=None)

    async def on_timeout(self):
        if self.done or not self.message:
            return
        self.done = True
        name = discord.utils.escape_markdown(self.ctx.author.display_name)
        try:
            await self.message.edit(content=f"⏱️ | **{name}**، کاتەکە تەواو بوو، ناردنەکە هەڵوەشێنرایەوە.", view=None)
        except discord.HTTPException:
            pass

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_flip = {}  # دوایین جاری هەر کەس coinflip ی کرد

    # !cash: بڕی دراوەکەت پیشان دەدات (بە شێوازی OwO)
    @commands.command(name="cash", aliases=["bal", "money", "دراو"])
    async def cash(self, ctx):
        coins, _, _ = get_user(ctx.author.id)
        name = discord.utils.escape_markdown(ctx.author.display_name)
        await ctx.send(f"{CASH_EMOJI} | **{name}**, you currently have __**{coins:,} {CURRENCY}!**__")

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
        amount = random.SystemRandom().randint(DAILY_MIN, DAILY_MAX)

        db.execute(
            "UPDATE users SET coins = coins + ?, last_daily = ?, streak = ? WHERE user_id = ?",
            (amount, now, streak, uid),
        )
        db.commit()
        await ctx.send(
            f"🎁 | **{name}**، **{amount:,} {CURRENCY}**ی ڕۆژانەت وەرگرت!\n"
            f"🔥 ڕۆژی **{streak}**ـەمینی بەردەوامی"
        )

    # !send @کەس 100  (یان: !give / !pay). all و half یش کار دەکەن
    @commands.command(name="send", aliases=["give", "pay"])
    async def send(self, ctx, member: discord.Member, amount: str):
        uid = ctx.author.id
        name = discord.utils.escape_markdown(ctx.author.display_name)
        example = f"`{PREFIX}send @کەس 100`"

        if member.bot:
            await ctx.send(f"❌ | **{name}**، ناتوانیت دراو بنێریت بۆ بوت!")
            return
        if member.id == uid:
            await ctx.send(f"❌ | **{name}**، ناتوانیت دراو بنێریت بۆ خۆت!")
            return

        coins, _, _ = get_user(uid)
        text = amount.strip().lower().replace(",", "")
        if text in ("all", "max", "هەموو"):
            number = coins
        elif text in ("half", "نیوە"):
            number = coins // 2
        else:
            try:
                number = int(text)
            except ValueError:
                await ctx.send(f"❌ | **{name}**، بڕەکە دەبێت ژمارە بێت (یان `all` / `half`)! نموونە: {example}")
                return

        if number < 1:
            await ctx.send(f"❌ | **{name}**، بڕەکە دەبێت لانیکەم **1 {CURRENCY}** بێت! نموونە: {example}")
            return
        if number > coins:
            await ctx.send(f"⚠️ | **{name}**، دراوی پێویستت نییە! (باڵانسی تۆ: `{coins:,} {CURRENCY}`)")
            return

        # پرسیاری دڵنیابوونەوە (بێ mention، تا وەرگر ئاگادار نەکرێتەوە پێش ئەوەی تۆ دڵنیا بیت)
        target = discord.utils.escape_markdown(member.display_name)
        view = SendConfirmView(ctx, member, number)
        view.message = await ctx.send(
            f"⚠️ | **{name}**، دڵنیایت دەتەوێت **{number:,} {CURRENCY}** بنێریت بۆ **{target}**؟",
            view=view,
            allowed_mentions=discord.AllowedMentions.none(),
        )

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

        amount, err = parse_bet(bet, coins, FLIP_MIN_BET, FLIP_MAX_BET)
        if err:
            await ctx.send(bet_error_text(err, name, FLIP_MIN_BET, FLIP_MAX_BET, coins, "cf 100 heads"))
            return

        wait = FLIP_COOLDOWN - (time.time() - self.last_flip.get(uid, 0))
        if wait > 0:
            await ctx.send(f"⏱️ | **{name}**، **{wait:.1f}** چرکەی تر چاوەڕێ بکە!", delete_after=4)
            return
        self.last_flip[uid] = time.time()

        outcome = random.SystemRandom().choice(["heads", "tails"])
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
    await bot.add_cog(Economy(bot))
  
