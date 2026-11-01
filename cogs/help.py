import discord
from discord.ext import commands
from utils import make_embed, BOT_NAME

# ═══════════════════════════════════════
# لیستی بەشەکان و فەرمانەکان
# فەرمانی نوێ؟ لێرە زیادی بکە
# ═══════════════════════════════════════
HELP_CATEGORIES = {
    "general": {
        "emoji": "🌟",
        "name": "گشتی",
        "desc": "فەرمانە سادە و بەسوودەکان",
        "commands": [
            ("!ping", "خێرایی بوتەکە پیشان دەدات"),
            ("!سڵاو", "سڵاو لە بوتەکە بکە"),
            ("!help", "ئەم مینیوەیە دەکاتەوە"),
        ],
    },
    "info": {
        "emoji": "📊",
        "name": "زانیاری",
        "desc": "زانیاری ئەندام و سێرڤەر",
        "commands": [
            ("!user", "زانیاری خۆت پیشان دەدات"),
            ("!user @کەس", "زانیاری ئەندامێکی تر"),
            ("!server", "زانیاری سێرڤەرەکە"),
        ],
    },
    "mod": {
        "emoji": "🛡️",
        "name": "مۆدەراسیۆن",
        "desc": "تەنها بۆ بەڕێوەبەران (ڕێگەی پێویستە)",
        "commands": [
            ("!kick @کەس هۆکار", "ئەندامێک دەردەکات"),
            ("!ban @کەس هۆکار", "ئەندامێک بلۆک دەکات"),
            ("!unban ناو", "بلۆکی کەسێک لادەبات"),
            ("!clear ژمارە", "چەند نامەیەک دەسڕێتەوە"),
        ],
    },
}

# کارتی لاپەڕەی سەرەکی
def home_embed(ctx):
    total = sum(len(c["commands"]) for c in HELP_CATEGORIES.values())
    embed = make_embed(
        "✨ ناوەندی یارمەتی",
        f"سڵاو {ctx.author.mention} 👋\n"
        f"من **{BOT_NAME}**م. لە خوارەوە بەشێک هەڵبژێرە بۆ بینینی فەرمانەکان.",
        ctx=ctx,
    )
    embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
    sections = "\n".join(
        f"{c['emoji']} **{c['name']}** ─ {c['desc']}" for c in HELP_CATEGORIES.values()
    )
    embed.add_field(name="📂 بەشەکان", value=sections, inline=False)
    embed.add_field(name="⚡ خێرایی", value=f"`{round(ctx.bot.latency * 1000)}ms`")
    embed.add_field(name="📌 فەرمان", value=f"`{total}`")
    embed.add_field(name="👥 ئەندامان", value=f"`{ctx.guild.member_count}`")
    return embed

# کارتی هەر بەشێک
def category_embed(ctx, key):
    c = HELP_CATEGORIES[key]
    embed = make_embed(f"{c['emoji']} {c['name']}", c["desc"], ctx=ctx)
    lines = "\n\n".join(f"**`{cmd}`**\n╰ {text}" for cmd, text in c["commands"])
    embed.add_field(name="فەرمانەکان", value=lines, inline=False)
    embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
    return embed

# لیستی هەڵبژاردن (Dropdown)
def help_options():
    return [
        discord.SelectOption(
            label=c["name"], value=key, emoji=c["emoji"], description=c["desc"]
        )
        for key, c in HELP_CATEGORIES.items()
    ]

# دوگمە و لیستەکە
class HelpView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=120)  # دوای ٢ خولەک ناچالاک دەبێت
        self.ctx = ctx
        self.message = None

    # تەنها خاوەنی !help دەتوانێت بەکاری بهێنێت
    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "❌ ئەم مینیوەیە بۆ کەسێکی ترە. خۆت `!help` بنووسە.", ephemeral=True
            )
            return False
        return True

    @discord.ui.select(placeholder="📂 بەشێک هەڵبژێرە...", options=help_options())
    async def pick(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.edit_message(
            embed=category_embed(self.ctx, select.values[0]), view=self
        )

    @discord.ui.button(label="سەرەکی", emoji="🏠", style=discord.ButtonStyle.primary)
    async def home(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=home_embed(self.ctx), view=self)

    @discord.ui.button(label="داخستن", emoji="✖️", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

# ═══════════════════════════════════════
# Cog: بەشێکی جیاکراوەی بوتەکە
# ═══════════════════════════════════════
class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # !help (یان !h یان !یارمەتی)
    @commands.command(name="help", aliases=["h", "یارمەتی"])
    async def help_command(self, ctx):
        view = HelpView(ctx)
        view.message = await ctx.send(embed=home_embed(ctx), view=view)

# ئەم فەرمانە وا لە بوتەکە دەکات ئەم فایلە بخوێنێتەوە (هەمیشە پێویستە)
async def setup(bot):
    await bot.add_cog(HelpCog(bot))
