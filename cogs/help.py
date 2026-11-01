import discord
from discord.ext import commands
from utils import make_embed, BOT_NAME, PREFIX

# ═══════════════════════════════════════
# بەشی ١: ئیمۆجییەکان (لێرە دەستکاری بکە)
# ═══════════════════════════════════════

# ئێستا ئیمۆجی ئاسایین. بۆ ئەوەی بیانکەیت بە جوڵاو، هەر یەکێک بگۆڕە بە
# کۆدی ئیمۆجییەکە، بۆ نموونە: "<a:star:123456789012345678>"
EMOJI = {
    "wave": "👋",
    "star": "✨",
    "arrow": "➜",
    "home": "🏠",
    "close": "✖️",
    "general": "🌟",
    "info": "📊",
    "mod": "🛡️",
    "speed": "⚡",
    "commands": "📌",
    "members": "👥",
    "folder": "📂",
}

# بانەر: لینکی وێنە یان GIF کە لە سەرەوەی لاپەڕەی سەرەکی دەردەکەوێت.
# ئەگەر نەتەوێت، بیهێڵەرەوە None
BANNER_URL = None
# نموونە:
# BANNER_URL = "https://raw.githubusercontent.com/Mhamadd11227H/My-bot-new/main/banner.gif"

# هێڵی جیاکەرەوە
DIVIDER = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"

# ═══════════════════════════════════════
# بەشی ٢: لیستی بەشەکان و فەرمانەکان
# فەرمانی نوێ؟ لێرە زیادی بکە
# color: ڕەنگی کارتی ئەو بەشە
# ═══════════════════════════════════════
HELP_CATEGORIES = {
    "general": {
        "emoji": EMOJI["general"],
        "name": "گشتی",
        "desc": "فەرمانە سادە و بەسوودەکان",
        "color": 0x5865F2,  # شین
        "commands": [
            ("!ping", "خێرایی بوتەکە پیشان دەدات"),
            ("!سڵاو", "سڵاو لە بوتەکە بکە"),
            ("!help", "ئەم مینیوەیە دەکاتەوە"),
        ],
    },
    "info": {
        "emoji": EMOJI["info"],
        "name": "زانیاری",
        "desc": "زانیاری ئەندام و سێرڤەر",
        "color": 0x9B59B6,  # مۆر
        "commands": [
            ("!user", "زانیاری خۆت پیشان دەدات"),
            ("!user @کەس", "زانیاری ئەندامێکی تر"),
            ("!server", "زانیاری سێرڤەرەکە"),
        ],
    },
    "mod": {
        "emoji": EMOJI["mod"],
        "name": "مۆدەراسیۆن",
        "desc": "تەنها بۆ بەڕێوەبەران (ڕێگەی پێویستە)",
        "color": 0xE74C3C,  # سوور
        "commands": [
            ("!kick @کەس هۆکار", "ئەندامێک دەردەکات"),
            ("!ban @کەس هۆکار", "ئەندامێک بلۆک دەکات"),
            ("!unban ناو", "بلۆکی کەسێک لادەبات"),
            ("!clear ژمارە", "چەند نامەیەک دەسڕێتەوە"),
        ],
    },
}

# ═══════════════════════════════════════
# بەشی ٣: کارتەکان
# ═══════════════════════════════════════

# کارتی لاپەڕەی سەرەکی
def home_embed(ctx):
    total = sum(len(c["commands"]) for c in HELP_CATEGORIES.values())
    embed = make_embed(
        f"{EMOJI['star']} ناوەندی یارمەتی",
        f"سڵاو {ctx.author.mention} {EMOJI['wave']}\n"
        f"من **{BOT_NAME}**م\n"
        f"{DIVIDER}\n"
        "بەشێک لە لیستی خوارەوە هەڵبژێرە بۆ بینینی فەرمانەکان",
        ctx=ctx,
    )
    # ناوی بوت و وێنەکەی لە سەرەوەی کارتەکە
    embed.set_author(
        name=f"{BOT_NAME} • ناوەندی یارمەتی",
        icon_url=ctx.bot.user.display_avatar.url,
    )
    embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)

    # لیستی بەشەکان: ناو + ڕوونکردنەوە بە شێوەی quote
    sections = "\n".join(
        f"{c['emoji']} **{c['name']}**\n> {c['desc']}"
        for c in HELP_CATEGORIES.values()
    )
    embed.add_field(name=f"{EMOJI['folder']} بەشەکان", value=sections, inline=False)
    embed.add_field(name=f"{EMOJI['speed']} خێرایی", value=f"`{round(ctx.bot.latency * 1000)}ms`")
    embed.add_field(name=f"{EMOJI['commands']} فەرمان", value=f"`{total}`")
    embed.add_field(name=f"{EMOJI['members']} ئەندامان", value=f"`{ctx.guild.member_count}`")

    # بانەر (ئەگەر دانرابێت)
    if BANNER_URL:
        embed.set_image(url=BANNER_URL)
    return embed

# کارتی هەر بەشێک
def category_embed(ctx, key):
    c = HELP_CATEGORIES[key]
    embed = make_embed(
        f"{c['emoji']} {c['name']}",
        f"> {c['desc']}\n{DIVIDER}",
        color=c["color"],  # ڕەنگی تایبەتی ئەو بەشە
        ctx=ctx,
    )
    embed.set_author(
        name=f"{BOT_NAME} • ناوەندی یارمەتی",
        icon_url=ctx.bot.user.display_avatar.url,
    )
    # هەر فەرمانێک: ناو + ڕوونکردنەوە بە شێوەی quote
    lines = "\n\n".join(
        f"{EMOJI['arrow']} **`{cmd.replace('!', PREFIX, 1)}`**\n> {text}" for cmd, text in c["commands"]
    )
    embed.add_field(name="فەرمانەکان", value=lines, inline=False)
    embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
    return embed

# ═══════════════════════════════════════
# بەشی ٤: لیست و دوگمەکان
# ═══════════════════════════════════════

# لیستی هەڵبژاردن (Dropdown)
def help_options():
    return [
        discord.SelectOption(
            label=c["name"], value=key, emoji=c["emoji"], description=c["desc"]
        )
        for key, c in HELP_CATEGORIES.items()
    ]

class HelpView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=120)  # دوای ٢ خولەک ناچالاک دەبێت
        self.ctx = ctx
        self.message = None

    # تەنها خاوەنی !help دەتوانێت بەکاری بهێنێت
    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                f"❌ ئەم مینیوەیە بۆ کەسێکی ترە. خۆت `{PREFIX}help` بنووسە.", ephemeral=True
            )
            return False
        return True

    @discord.ui.select(placeholder="📂 بەشێک هەڵبژێرە...", options=help_options())
    async def pick(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.edit_message(
            embed=category_embed(self.ctx, select.values[0]), view=self
        )

    @discord.ui.button(label="سەرەکی", emoji=EMOJI["home"], style=discord.ButtonStyle.primary)
    async def home(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=home_embed(self.ctx), view=self)

    @discord.ui.button(label="داخستن", emoji=EMOJI["close"], style=discord.ButtonStyle.danger)
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

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
    
