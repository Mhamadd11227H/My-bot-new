import os

import discord
from discord.ext import commands

from utils import (
    make_embed, BOT_NAME, PREFIX, EXTRA_PREFIXES, CURRENCY,
    E_EGGPLANT, E_GRAPE, E_ORANGE, E_CHERRY, E_DIAMOND,
)

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

# باشترین چارەسەر: فایلی zero.gif لەناو فۆڵدەری بوتەکە دابنێ (لەتەنیشت bot.py یان لەناو cogs)
# بوتەکە خۆی دەیبینێتەوە و وەک فایل دەینێرێت، بۆیە هەرگیز لینکەکەی ناکوژێتەوە.
# ئەگەر فایلەکە نەبوو، GIF_URL ی سەرەوە بەکاردێت
def _find_gif():
    here = os.path.dirname(os.path.abspath(__file__))
    for folder in (here, os.path.dirname(here)):
        path = os.path.join(folder, "zero.gif")
        if os.path.isfile(path):
            return path
    return None

GIF_FILE = _find_gif()

def gif_source():
    return "attachment://zero.gif" if GIF_FILE else GIF_URL

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
        "desc": "فەرمانێن سادە و بسوود",
        "color": 0x5865F2,
        "commands": [
            ("{p} help", "ئەڤ مینیۆیێ ڤەدکەت (`{p} h` یان `{p} یارمەتی`)"),
            ("{p} ping", "خێراییا بوتی نیشان ددەت"),
            ("{p} سڵاو", "سلاڤێ ل بوتی بکە"),
        ],
    },
    "info": {
        "emoji": "📊",
        "title": "زانیاری",
        "desc": "زانیاریێن ئەندام و سێرڤەری",
        "color": 0x9B59B6,
        "commands": [
            ("{p} user", "زانیاریێن خوە نیشان ددەت"),
            ("{p} user @کەس", "زانیاریێن ئەندامەکێ دی نیشان ددەت"),
            ("{p} server", "زانیاریێن سێرڤەری نیشان ددەت"),
        ],
    },
    "economy": {
        "emoji": "💰",
        "title": "ئابووری و دراو",
        "desc": f"{CURRENCY}ا خوە ببینە، وەربگرە و بنێرە",
        "color": 0x2ECC71,
        "commands": [
            ("{p} cash", f"ژمارا {CURRENCY}ا تە نیشان ددەت (`{{p}} bal` / `{{p}} money` / `{{p}} دراو`)"),
            ("{p} daily", f"{CURRENCY}ا ڕۆژانە وەربگرە، هەر ٢٤ دەمژمێران جارەکێ"),
            ("{p} send @کەس <بڕ>", f"{CURRENCY} بۆ کەسەکێ بنێرە، پشتی دڵنیابوونێ (`{{p}} give` / `{{p}} pay`)"),
            ("{p} send @کەس all", "هەمی دراوێن خوە بنێرە (`half` = نیڤا وان)"),
        ],
    },
    "games": {
        "emoji": "🎰",
        "title": "یاری",
        "desc": "یاریێن ب دراو. یاریەکێ هەلبژێرە و یاسایێن وێ ببینە",
        "color": 0xF1C40F,
        "commands": [
            ("{p} slots <بڕ>", "سلۆتێ یاری بکە (`{p} s` / `{p} slot` / `{p} سلۆت`)"),
            ("{p} slots all", "هەمی دراوێن خوە شەرت بکە (`half` = نیڤا وان، `double` = دوو ئەوەندەیێ جارا بەری)"),
            ("{p} slots stats", "ئاماریێ سلۆتا خوە (`{p} slots stats @کەس` بۆ کەسەکێ دی)"),
            ("{p} slots history", "مێژوویا یاریێن تە"),
            ("{p} slots leaderboard", "لیستا پێشەنگێن سلۆتێ (`lb` / `top`)"),
            ("{p} slots help", "خشتەیا بردنێ و جاکپۆتێ"),
            ("{p} cf <بڕ> <h/t>", "سەر یان پشت (`{p} cf 100 h` = سەر، `t` = پشت. `coinflip` / `flip` / `coin` ژی کار دکەن)"),
        ],
    },
    "setup": {
        "emoji": "⚙️",
        "title": "ڕێکخستنا سێرڤەری",
        "desc": "Welcome، Invite و Left ب ڕەنگ و وێنەیێ خوە",
        "color": 0xE91E63,
        "commands": [
            ("{p} setup", "ژوورەکا نهێنی چێدکەت کو تەنێ خودانێ سێرڤەری دبینیت (`{p} panel` ژی کار دکەت)"),
            ("{p} invites", "ژمارا ئەو کەسێن تە بانگهێشت کرین (`{p} invites @کەس` بۆ کەسەکێ دی)"),
        ],
    },
    "mod": {
        "emoji": "🛡️",
        "title": "مۆدەراسیۆن",
        "desc": "تەنێ بۆ بەرپرسان (مۆڵەت پێدڤییە)",
        "color": 0xE74C3C,
        "commands": [
            ("{p} kick @کەس <هۆکار>", "ئەندامەکی ژ سێرڤەری دەردئێخت"),
            ("{p} ban @کەس <هۆکار>", "ئەندامەکی بلۆک دکەت"),
            ("{p} unban <ناڤ>", "بلۆکا کەسەکی لادبەت"),
            ("{p} clear <ژمارە>", "چەند نامەیان ددەتە ژێبرن (١ تا ١٠٠)"),
            ("{p} slots config", "ڕێکخستنێن سلۆتێ بگۆڕە (مۆڵەتا Manage Server)"),
        ],
    },
    "music": {
    "emoji": "🎵",
    "title": "میوزیک",
    "desc": "گۆرانی لە YouTube بلێ",
    "color": 0x1DB954,
    "commands": [
        ("{p} play <گۆرانی>", "گۆرانی بلێ (`{p} p`)"),
        ("{p} pause / resume", "ڕایبگرە / بەردەوامی بکە"),
        ("{p} skip", "گۆرانی دواتر"),
        ("{p} queue", "ڕیزی گۆرانییەکان"),
        ("{p} np", "گۆرانی ئێستا"),
        ("{p} volume <1-100>", "دەنگ بگۆڕە"),
        ("{p} loop / shuffle", "دووبارەکردنەوە / تێکەڵکردن"),
        ("{p} stop / leave", "بوەستێنە / بوت دەربکە"),
    ],
 },
}

# ═══════════════════════════════════════
# بەشی ٢.٥: لیستی یارییەکان (ئەو لیستەی دوای کلیککردن لە "یاری" دەردەکەوێت)
# یاری نوێ؟ تەنها بلۆکێکی نوێ لێرە زیاد بکە، لیستەکە خۆکار نوێ دەبێتەوە
# "sections" = لیستی (ناوی بەش، دەق). هەر دەقێک نابێت لە ١٠٠٠ پیت زیاتر بێت
# {p} = هێمای فەرمان
# ═══════════════════════════════════════
_SLOT_TABLE = (
    f"{E_EGGPLANT * 3} ── **x1** (تەنێ شەرتێ خوە وەردگریڤە) ── ٪٢٠\n"
    f"{E_GRAPE * 3} ── **x2** ── ٪٢٠\n"
    f"{E_ORANGE * 3} ── **x3** ── ٪٥\n"
    f"{E_CHERRY * 3} ── **x4** ── ٪٢.٥\n"
    f"{E_DIAMOND * 3} ── **x10** ── ٪١"
)

GAMES = {
    "slots": {
        "emoji": "🎰",
        "title": "سلۆت",
        "short": "سێ هێما دزڤڕن. ئەگەر هەر سێ وەک ئێک بن، تو دبەی!",
        "color": 0xF1C40F,
        "sections": [
            (
                "📖 چەوا دهێتە یاریکرن؟",
                "١️⃣ بنڤیسە `{p} slots 100` (١٠٠ = بڕێ شەرتێ، دشێی بگۆڕی)\n"
                "٢️⃣ سێ هێما دزڤڕن\n"
                "٣️⃣ ئەگەر **هەر سێ هێمایێن وەک ئێک** هاتن، تو دبەی\n"
                "٤️⃣ ئەگەر نە، شەرتێ تە دچیت",
            ),
            (
                "⚠️ گرنگ",
                "دوو هێمایێن وەک ئێک **تەنێ** دۆڕانە. دڤێت هەر سێ وەک ئێک بن",
            ),
            (
                "💎 خشتەیا بردنێ (هێما ── چەند ئەوەندە ── ئەگەر)",
                _SLOT_TABLE,
            ),
            (
                "👑 جاکپۆت",
                "٧️⃣٧️⃣٧️⃣ ئەگەر دەرکەڤت، **هەمی پارەیێ ناڤ جاکپۆتێ** دبەی!\n"
                "🎯 ئەگەر: ١ ژ ٥٠٠٠\n"
                "💵 دڤێت شەرتێ تە لانیکەم `١٠٠` بیت\n"
                "📈 ژ هەر شەرتەکێ پارچەیەکا بچووک دچیتە ناڤ جاکپۆتێ\n"
                "👀 بۆ دیتنا بڕێ جاکپۆتێ: `{p} slots help`",
            ),
            (
                "⚡ شەرتکرنا خێرا",
                "`{p} slots all` ── هەمی دراوێن خوە\n"
                "`{p} slots half` ── نیڤا دراوێن خوە\n"
                "`{p} slots double` ── دوو ئەوەندەیێ شەرتێ جارا بەری",
            ),
            (
                "📊 فەرمانێن دی یێن سلۆتێ",
                "`{p} slots stats` ── ئاماریێ تە\n"
                "`{p} slots history` ── مێژوویا یاریێن تە\n"
                "`{p} slots leaderboard` ── لیستا پێشەنگان\n"
                "⏱️ ناڤبەرا دوو یاریان دڤێت چەند چرکەیەکان چاڤەڕێ بکەی",
            ),
        ],
    },
    "coinflip": {
        "emoji": "🪙",
        "title": "سەر یان پشت",
        "short": "تو سەر یان پشتێ هەلدبژێری. ئەگەر ڕاست بوو، دبەی!",
        "color": 0x3498DB,
        "sections": [
            (
                "📖 چەوا دهێتە یاریکرن؟",
                "١️⃣ بنڤیسە `{p} cf 100 h`\n"
                "٢️⃣ `h` = سەر 🟡 ، `t` = پشت ⚪\n"
                "٣️⃣ دراو دزڤڕیت و دەرئەنجام دهێتە نیشاندان\n"
                "٤️⃣ ئەگەر هەلبژارتنا تە ڕاست بوو، تو دبەی",
            ),
            (
                "💰 بردن و دۆڕان",
                "✅ ئەگەر ڕاست بوو: **x2** (شەرتێ خوە دوو ئەوەندە وەردگری)\n"
                "❌ ئەگەر خەلەت بوو: شەرتێ تە دچیت\n"
                "🎲 ئەگەر: ٪٥٠ بۆ سەر و ٪٥٠ بۆ پشت",
            ),
            (
                "✏️ ناڤێن جودا",
                "سەر: `h` ، `head` ، `heads` ، `سەر`\n"
                "پشت: `t` ، `tail` ، `tails` ، `پشت`\n"
                "ئەگەر تو نەنڤیسی، خۆکار **سەر** دهێتە هەلبژارتن",
            ),
            (
                "⚡ شەرتکرنا خێرا",
                "`{p} cf all h` ── هەمی دراوێن خوە\n"
                "`{p} cf half t` ── نیڤا دراوێن خوە",
            ),
            (
                "📌 نموونە",
                "`{p} cf 500 t` ── ٥٠٠ شەرت لسەر پشتێ\n"
                "`{p} cf سەر 100` ── ڕیزبەندی ژی بەلاڤ نینە، هەردوو کار دکەن\n"
                "⏱️ ناڤبەرا دوو یاریان دڤێت چەند چرکەیەکان چاڤەڕێ بکەی",
            ),
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
    src = gif_source()
    if src:
        embed.set_image(url=src)
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
    src = gif_source()
    if src:
        embed.set_image(url=src)
    return embed

# کارتی لیستی یارییەکان (دوای کلیک لە "یاری")
def games_overview_embed(ctx):
    c = CATEGORIES["games"]
    games_list = "\n".join(
        f"{g['emoji']} **{g['title']}** ── {g['short']}" for g in GAMES.values()
    )
    embed = make_embed(
        f"{c['emoji']}  {c['title']}",
        (
            f"> {c['desc']}\n{DIVIDER}\n"
            f"🎮 **یاریێن هەین**\n{games_list}\n{DIVIDER}\n"
            "👇 **یاریەکێ ژ لیستا خوارێ هەلبژێرە** بۆ دیتنا یاسا و چەوانیا یاریکرنێ"
        ),
        color=c["color"],
        ctx=ctx,
    )
    embed.set_author(name=f"{BOT_NAME} • ناوەندی یارمەتی", icon_url=ctx.bot.user.display_avatar.url)
    src = gif_source()
    if src:
        embed.set_image(url=src)
    return embed

# کارتی یاسای هەر یارییەک
def game_embed(ctx, key):
    g = GAMES[key]
    embed = make_embed(
        f"{g['emoji']}  {g['title']}",
        f"> {g['short']}",
        color=g["color"],
        ctx=ctx,
    )
    for name, value in g["sections"]:
        embed.add_field(name=name, value=render(value), inline=False)
    embed.set_author(name=f"{BOT_NAME} • یاسای یاری", icon_url=ctx.bot.user.display_avatar.url)
    src = gif_source()
    if src:
        embed.set_image(url=src)
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
        elif key == "games":
            embed = games_overview_embed(view.ctx)
        else:
            embed = category_embed(view.ctx, key)
        # لیستی یارییەکان تەنها لە بەشی "یاری" دەردەکەوێت
        view.show_game_menu(key == "games")
        await interaction.response.edit_message(embed=embed, view=view)

# لیستی دووەم: ناوی یارییەکان (تەنها دوای کلیک لە بەشی یاری دەردەکەوێت)
class GameSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="هەمی یاری", value="all", emoji="📋", description="گەڕان بۆ لیستا یاریان"
            )
        ]
        for key, g in GAMES.items():
            options.append(
                discord.SelectOption(label=g["title"], value=key, emoji=g["emoji"], description=g["short"][:100])
            )
        super().__init__(placeholder="🎮 یاریەکێ هەلبژێرە...", min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        key = self.values[0]
        if key == "all":
            embed = games_overview_embed(view.ctx)
        else:
            embed = game_embed(view.ctx, key)
        await interaction.response.edit_message(embed=embed, view=view)

class HelpView(discord.ui.View):
    def __init__(self, ctx, invite_url):
        super().__init__(timeout=180)  # دوای ٣ خولەک ناچالاک دەبێت
        self.ctx = ctx
        self.invite_url = invite_url
        self.message = None
        self.game_select = None  # لیستی یارییەکان (تەنها لە بەشی یاری)

        self.add_item(CategorySelect())
        # دوگمەکانی لینک (ڕیزی سێیەم، چونکە ڕیزی دووەم بۆ لیستی یارییەکانە)
        self.add_item(discord.ui.Button(label="زیادکردنی بوت", url=invite_url, emoji="🤖", row=2))
        if SUPPORT_URL:
            self.add_item(discord.ui.Button(label="سێرڤەری ساپۆرت", url=SUPPORT_URL, emoji="💬", row=2))

    # لیستی یارییەکان پیشان بدە یان بیشارەوە
    def show_game_menu(self, show):
        if show and self.game_select is None:
            self.game_select = GameSelect()
            self.add_item(self.game_select)
        elif not show and self.game_select is not None:
            self.remove_item(self.game_select)
            self.game_select = None

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
        file = discord.File(GIF_FILE, filename="zero.gif") if GIF_FILE else None
        view.message = await ctx.send(embed=home_embed(ctx, invite_url), view=view, file=file)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))

