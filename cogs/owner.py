import discord
from discord.ext import commands

from database import add_coins, get_balance
from utils import CURRENCY, CASH_EMOJI

# ═══════════════════════════════════════
# فەرمانە نهێنییەکانی خاوەن (تەنها تۆ)
# - لە !help دا نییە
# - ئەگەر کەسێکی تر بنووسێت، بوت هیچ وەڵام نادات (وەک ئەوەی فەرمانەکە نەبێت)
# - نامەی فەرمانەکە دەسڕێتەوە و ئەنجامەکە لە DM دا بۆ تۆ دەنێرێت
# خاوەن = ئەو ئەکاونتەی کە بوتەکەی لە Discord Developer Portal دروست کردووە
# ═══════════════════════════════════════

MAX_ADD = 10**15  # زۆرترین بڕ بۆ یەک جار (بۆ ڕێگری لە هەڵە)

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # !addcoins 1000000  ->  دراو بۆ خۆت زیاد دەکات
    @commands.command(name="addcoins", hidden=True)
    @commands.is_owner()
    async def addcoins(self, ctx, amount: int):
        # نامەی فەرمانەکە بسڕەوە تا کەس نەیبینێت (پێویستی بە ڕێگەی Manage Messages هەیە)
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass

        if amount < 1 or amount > MAX_ADD:
            text = f"❌ بڕەکە دەبێت لە نێوان `1` و `{MAX_ADD:,}` بێت."
        else:
            add_coins(ctx.author.id, amount)
            text = (
                f"{CASH_EMOJI} **{amount:,} {CURRENCY}** زیاد کرا.\n"
                f"باڵانسی نوێ: **{get_balance(ctx.author.id):,} {CURRENCY}**"
            )

        # ئەنجامەکە تەنها بۆ خۆت، لە DM دا
        try:
            await ctx.author.send(text)
        except discord.Forbidden:
            # DM داخراوە: کورت نیشان دەدرێت و خۆی دەسڕێتەوە
            await ctx.send(text, delete_after=3)

async def setup(bot):
    await bot.add_cog(Owner(bot))
  
