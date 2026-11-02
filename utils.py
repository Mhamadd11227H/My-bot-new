import discord

# ناوی بوتەکە (لە فووتەری کارتەکان)
BOT_NAME = "Zero Bot"

# هێمای فەرمانەکان. تەنها لێرە بیگۆڕە، لە هەموو شوێنێک دەگۆڕێت
# نموونە: "z" یان "!z"
PREFIX = "z"

# هێماکانی تر کە بوتەکە پێیان وەڵام دەداتەوە (پیتی گەورە و بچووک جیاناکرێنەوە)
# نموونە: zero cash، Zero cash، ZERO cash
EXTRA_PREFIXES = ["zero"]

# ڕەنگەکان. دەتوانیت کۆدی هێکس بگۆڕیت
MAIN = 0x5865F2      # شین (زانیاری)
SUCCESS = 0x2ECC71   # سەوز (سەرکەوتن)
ERROR = 0xE74C3C     # سوور (هەڵە)
WARN = 0xF1C40F      # زەرد (ئاگاداری)

# ئەم فەرمانە هەموو کارتەکان دروست دەکات
def make_embed(title, description=None, color=MAIN, ctx=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=discord.utils.utcnow(),
    )
    if ctx:
        embed.set_footer(
            text=f"داواکراوە لەلایەن {ctx.author.display_name} • {BOT_NAME}",
            icon_url=ctx.author.display_avatar.url,
        )
    else:
        embed.set_footer(text=BOT_NAME)
    return embed

# ═══════════════════════════════════════
# دراو و ئیمۆجییەکانی یارییەکان
# ═══════════════════════════════════════

CURRENCY = "zero coin"  # ناوی دراو. تەنها لێرە بیگۆڕە، لە هەموو شوێنێک (help، cash، daily، یارییەکان) دەگۆڕێت
CASH_EMOJI = "💵"       # ئیمۆجی دراو لە یارییەکان. دەتوانیت بیگۆڕیت بە "<:ناو:ئایدی>"

# ئیمۆجییەکان. ئەگەر وەک نووسین (<:emoji_9:...>) دەرکەوتن، بوتەکە لەو سێرڤەرەدا
# نییە کە ئیمۆجییەکانی تێدایە. ئیمۆجییەکان لە سێرڤەرەکەی خۆت باربکە و ئایدییەکان بگۆڕە
SPIN_EMOJI = "<a:emoji_72:1536441649947869234>"

E_EGGPLANT = "<:emoji_9:1535300687288737895>"
E_GRAPE    = "<:emoji_13:1535301374252945499>"
E_ORANGE   = "<:emoji_9:1535300678497341462>"
E_CHERRY   = "<:emoji_12:1535301118362521681>"
E_DIAMOND  = "<:emoji_14:1535303848963612672>"

# ڕووی دراوەکە لە coinflip
HEADS_EMOJI = "🟡"
TAILS_EMOJI = "⚪"

# ڕەنگەکانی تێمی کازینۆ
PURPLE = 0x7B2FF7    # مۆر
GOLD = 0xFFC700      # زێڕین

# پەیامی هەڵە بۆ شەرتی هەڵە (هەموو یارییەکان بەکاری دەهێنن)
# err: ئەو کۆدەی parse_bet (لە database.py) دەیگەڕێنێتەوە
def bet_error_text(err, name, min_bet, max_bet, balance, example):
    texts = {
        "invalid": f"❌ | **{name}**، بڕی شەرتەکە دەبێت ژمارە بێت (یان `all` / `half` / `double`)! نموونە: `{PREFIX}{example}`",
        "no_cash": f"⚠️ | **{name}**، دراوت نییە! `{PREFIX}daily` بنووسە بۆ وەرگرتنی دراو.",
        "too_low": f"❌ | **{name}**، کەمترین شەرت **{min_bet:,} {CURRENCY}**ـە!",
        "too_high": f"⚠️ | **{name}**، زۆرترین شەرت **{max_bet:,} {CURRENCY}**ـە!",
        "insufficient": f"⚠️ | **{name}**، دراوی پێویستت نییە! (باڵانسی تۆ: `{balance:,} {CURRENCY}`)",
        "no_last": f"❌ | **{name}**، هێشتا شەرتی پێشووت نییە بۆ `double`. بڕێک بنووسە.",
    }
    return texts.get(err, "❌ هەڵەیەک ڕوویدا.")

