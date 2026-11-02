import discord
from discord.ext import commands

from utils import make_embed, BOT_NAME, PREFIX, EXTRA_PREFIXES, CURRENCY

# ═══════════════════════════════════════
# بەشی ١: ڕێکخستنەکان (لێرە دەستکاری بکە)
# ═══════════════════════════════════════

# GIF ی هەموو لاپەڕەکان. ئەگەر نەتەوێت: None
# ئاگادار بە: لینکەکانی cdn.discordapp.com کاتیان هەیە (ex=...) و دوای ماوەیەک ناکار دەکەن.
# چارەسەری هەمیشەیی: GIF لە GitHub باربکە و لینکی raw ی بەکاربهێنە، بۆ نموونە:
# "https://raw.githubusercontent.com/Mhamadd11227H/My-bot-new/main/zero.gif"
GIF_URL = (
    "https://cdn.discordapp.com/attachments/1535963966130622515/1537670836050202696/"
    "zero_bot_neon_animated.gif?ex=6a81dd4f&is=6a808bcf&hm=f240b7bcd96096c6456901a297d5a99926ef47a7c37595cc65a9f9f0bcb0b960&"
)

# دوگمەی سێرڤەری ساپۆرت (ئەگەر نەتەوێت: None)
SUPPORT_URL = "https://discord.gg/GK6WZbxuUK"

# دوگمەی زیادکردنی بوت. ئایدی بوت خۆکارە، بۆیە هەمیشە بوتی ئێستا زیاد دەکات
# ڕێگەپێدانەکان: 8 = Administrator. بۆ ڕێگەی کەمتر ژمارەیەکی تر دابنێ
INVITE_PERMISSIONS = 8

DIVIDER = "───────────────────────────"

# ═══════════════════════════════════════
# بەشی ٢: لیستی بەشەکان و فەرمانەکان
# تەنها ئەو فەرمانانەی لە بوتەکەدا هەن. فەرمانی نوێ؟ لێرە زیادی بکە
# {p} = هێمای فەرمان (z)
# ═══════════════════════════════════════
CATEGORIES = {
    "general": {
        "emoji": "🌟",
        "title": "گشتی",
        "desc": "فەرمانە سادە و بەسوودەکان",
        "color": 0x5865F2,
        "commands": [
            ("{p} help", "ئەم مینیوەیە دەکاتەوە (`{p} h` یان `{p} یارمەتی`)"),
            ("{p} ping", "خێرایی بوتەکە پیشان دەدات"),
            ("{p} سڵاو", "سڵاو لە بوتەکە بکە"),
        ],
    },
    "info": {
        "emoji": "📊",
        "title": "زانیاری",
        "desc": "زانیاری ئەندام و سێرڤەر",
        "color": 0x9B59B6,
        "commands": [
            ("{p} user", "زانیاری خۆت پیشان دەدات"),
            ("{p} user @کەس", "زانیاری ئەندامێکی تر"),
            ("{p} server", "زانیاری سێرڤەرەکە"),
        ],
    },
    "economy": {
        "emoji": "💰",
        "title": "ئابووری و دراو",
        "desc": f"{CURRENCY}ی خۆت ببینە، وەریبگرە و بینێرە",
        "color": 0x2ECC71,
        "commands": [
            ("{p} cash", f"باڵانسی {CURRENCY}ی خۆت (`{{p}} bal` / `{{p}} money` / `{{p}} دراو`)"),
            ("{p} daily", f"{CURRENCY}ی ڕۆژانە وەربگرە (هەر ٢٤ کاتژمێر جارێک)"),
            ("{p} send @کەس <بڕ>", f"{CURRENCY} بنێرە بۆ کەسێکی تر، دوای دڵنیابوونەوە (`{{p}} give` / `{{p}} pay`)"),
            ("{p} send @کەس all", "هەموو دراوەکانت بنێرە (`half` = نیوەی)"),
        ],
    },
    "games": {
        "emoji": "🎰",
        "title": "یاری",
        "desc": f"سلۆت و سەر یان پشت بە {CURRENCY}",
        "color": 0xF1C40F,
        "commands": [
            ("{p} slots <بڕ>", "سلۆت یاری بکە (`{p} s` / `{p} slot` / `{p} سلۆت`)"),
            ("{p} slots all", "هەموو دراوەکانت شەرت بکە (`half` = نیوەی، `double` = دوو ئەوەندەی پێشوو)"),
            ("{p} slots stats", "ئاماری سلۆتی خۆت (`{p} slots stats @کەس` بۆ کەسێکی تر)"),
            ("{p} slots history", "مێژووی یارییەکانت"),
            ("{p} slots leaderboard", "لیستی پێشەنگانی سلۆت (`lb` / `top`)"),
            ("{p} slots help", "خشتەی بردنەوە و جاکپۆت"),
            ("{p} cf <بڕ> <heads/tails>", "سەر یان پشت (`{p} cf 100 h` = سەر، `t` = پشت. `coinflip` / `flip` / `coin` یش کار دەکەن)"),
        ],
    },
    "mod": {
        "emoji": "🛡️",
        "title": "مۆدەراسیۆن",
        "desc": "تەنها بۆ بەڕێوەبەران (ڕێگەی پێویستە)",
        "color": 0xE74C3C,
        "commands": [
            ("{p} kick @کەس <هۆکار>", "ئەندامێک دەردەکات"),
            ("{p} ban @کەس <هۆکار>", "ئەندامێک بلۆک دەکات"),
            ("{p} unban <ناو>", "بلۆکی کەسێک لادەبات"),
            ("{p} clear <ژمارە>", "چەند نامەیەک دەسڕێتەوە (١ تا ١٠٠)"),
            ("{p} slots config", "ڕێکخستنەکانی سلۆت بگۆڕە (ڕێگەی Manage Server)"),
        ],
    },
}

# ═══════════════════════════════════════
# بەشی ٣: کارتەکان
# ═══════════════════════════════════════

# هێما بەکارهێنراوەکان بۆ نیشاندان (z · zero)
def prefixes_text():
    names = [PREFIX] + [p for p in EXTRA_PREFIXES if p.lower() != PREFIX.lower()]
    return " · ".join(f"`{n} `" for n in names)

def render(text):
    return text.replace("{p}", PREFIX)

# کارتی لاپەڕەی سەرەکی
def home_embed(ctx, invite_url):
    total = sum(len(c["commands"]) for c in CATEGORIES.values())
    embed = make_embed(
        f"🌟✨  ڕێنمایی فەرمانەکانی {BOT_NAME}  ✨🌟",
        (
            f"**هێماکانی بەکارهێنان:** {prefixes_text()}\n"
            f"💡 *نموونە:* `{PREFIX} daily` یان `{PREFIX} slots 100`\n\n"
            f"{DIVIDER}\n"
            "📂 **بەشەکان**\n"
            + "\n".join(
                f"{c['emoji']} **{c['title']}** ── {c['desc']}  `{len(c['commands'])}`"
                for c in CATEGORIES.values()
            )
            + f"\n{DIVIDER}\n"
            f"🔗 **زیادکردنی بوت:** [کلیک بکە]({invite_url})\n"
            + (f"🛡️ **سێرڤەری ساپۆرت:** [کلیک بکە]({SUPPORT_URL})\n" if SUPPORT_URL else "")
        ),
        color=0x5865F2,
        ctx=ctx,
    )
    embed.set_author(name=f"{BOT_NAME} • ناوەندی یارمەتی", icon_url=ctx.bot.user.display_avatar.url)
    embed.add_field(name="⚡ خێرایی", value=f"`{round(ctx.bot.latency * 1000)}ms`")
    embed.add_field(name="📌 فەرمان", value=f"`{total}`")
    if ctx.guild:
        embed.add_field(name="👥 ئەندامان", value=f"`{ctx.guild.member_count}`")
    if GIF_URL:
        embed.set_image(url=GIF_URL)
    return embed

# کارتی هەر بەشێک
def category_embed(ctx, key):
    c = CATEGORIES[key]
    lines = "\n".join(
        f"▫️ **`{render(cmd)}`** ── {render(text)}" for cmd, text in c["commands"]
    )
    embed = make_embed(
        f"{c['emoji']}  {c['title']}",
        f"> {c['desc']}\n{DIVIDER}\n{lines}\n{DIVIDER}",
        color=c["color"],
        ctx=ctx,
    )
    embed.set_author(name=f"{BOT_NAME} • ناوەندی یارمەتی", icon_url=ctx.bot.user.display_avatar.url)
    if GIF_URL:
        embed.set_image(url=GIF_URL)
    return embed

# ═══════════════════════════════════════
# بەشی ٤: لیست و دوگمەکان
# ═══════════════════════════════════════

class CategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="لاپەڕەی سەرەکی", value="home", emoji="🏠", description="گەڕانەوە بۆ سەرەتا"
            )
        ]
        for key, c in CATEGORIES.items():
            options.append(
                discord.SelectOption(label=c["title"], value=key, emoji=c["emoji"], description=c["desc"])
            )
        super().__init__(placeholder="📂 بەشێک هەڵبژێرە...", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        key = self.values[0]
        if key == "home":
            embed = home_embed(view.ctx, view.invite_url)
        else:
            embed = category_embed(view.ctx, key)
        await interaction.response.edit_message(embed=embed, view=view)

class HelpView(discord.ui.View):
    def __init__(self, ctx, invite_url):
        super().__init__(timeout=180)  # دوای ٣ خولەک ناچالاک دەبێت
        self.ctx = ctx
        self.invite_url = invite_url
        self.message = None

        self.add_item(CategorySelect())
        # دوگمەکانی لینک (ڕیزی دووەم)
        self.add_item(discord.ui.Button(label="زیادکردنی بوت", url=invite_url, emoji="🤖", row=1))
        if SUPPORT_URL:
            self.add_item(discord.ui.Button(label="سێرڤەری ساپۆرت", url=SUPPORT_URL, emoji="💬", row=1))

    # تەنها خاوەنی help دەتوانێت بەکاری بهێنێت
    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                f"❌ ئەم مینیوەیە بۆ کەسێکی ترە. خۆت `{PREFIX} help` بنووسە.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            if not isinstance(item, discord.ui.Button) or item.url is None:
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

    # !help (یان !h یان !یارمەتی یان !commands)
    @commands.command(name="help", aliases=["h", "یارمەتی", "commands", "cmd", "cmds"])
    async def help_command(self, ctx):
        invite_url = (
            f"https://discord.com/oauth2/authorize?client_id={ctx.bot.user.id}"
            f"&permissions={INVITE_PERMISSIONS}&integration_type=0&scope=bot"
        )
        view = HelpView(ctx, invite_url)
        view.message = await ctx.send(embed=home_embed(ctx, invite_url), view=view)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
    
