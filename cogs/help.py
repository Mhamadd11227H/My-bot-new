import os

import discord
from discord.ext import commands

from utils import (
    make_embed, BOT_NAME, PREFIX, EXTRA_PREFIXES, CURRENCY,
    E_EGGPLANT, E_GRAPE, E_ORANGE, E_CHERRY, E_DIAMOND,
)

# نرخ و cooldownا ڕاوکرنێ ژ hunt_data.py دهێتە وەرگرتن (ئەگەر نەبیت: ١٠ و ١٥)
try:
    from . import hunt_data as _HD
    HUNT_COST, HUNT_COOLDOWN = _HD.HUNT_COST, _HD.HUNT_COOLDOWN
except Exception:
    HUNT_COST, HUNT_COOLDOWN = 10, 15

# ═══════════════════════════════════════
# بەشێ ١: ڕێکخستن (ل ڤێرە دەستکاری بکە)
# ═══════════════════════════════════════

# GIFا هەمی لاپەڕان. ئەگەر نەڤێت: None
# ئاگەهدار بە: لینکێن cdn.discordapp.com دەم هەنە (ex=...) و پشتی ماوەیەکێ ناکار دبن.
# چارەسەریا هەمیشەیی: GIF ل GitHub بار بکە و لینکێ raw بکار بینە، بۆ نموونە:
# "https://raw.githubusercontent.com/Mhamadd11227H/My-bot-new/main/zero.gif"
GIF_URL = (
    "https://cdn.discordapp.com/attachments/1535963966130622515/1537670836050202696/"
    "zero_bot_neon_animated.gif?ex=6a81dd4f&is=6a808bcf&hm=f240b7bcd96096c6456901a297d5a99926ef47a7c37595cc65a9f9f0bcb0b960&"
)

# وێنەیێ هەمی لاپەڕان. ڕیزبەندی:
# ١. ئەو وێنەیێ ب فەرمانا  z media set help <ناڤ>  دیاری کری (باشترین ڕێک)
# ٢. فایلا zero.gif ئەگەر ل تەنیشت bot.py یان د ناڤ cogs دا هاتبیتە دانان
# ٣. GIF_URL ی سەرەوە
try:
    from media_store import slot_file
except Exception:
    slot_file = lambda slot: None

def _find_gif():
    here = os.path.dirname(os.path.abspath(__file__))
    for folder in (here, os.path.dirname(here)):
        path = os.path.join(folder, "zero.gif")
        if os.path.isfile(path):
            return path
    return None

def current_media():
    """(path, filename) یێ وێنەیێ نوکە، یان (None, None)"""
    found = slot_file("help")
    if found:
        return found
    path = _find_gif()
    return (path, "zero.gif") if path else (None, None)

def gif_source():
    path, filename = current_media()
    return f"attachment://{filename}" if path else GIF_URL

# دوگمەیا سێرڤەرێ ساپۆرتێ (ئەگەر نەڤێت: None)
SUPPORT_URL = "https://discord.gg/GK6WZbxuUK"

# دوگمەیا زێدەکرنا بوتی. ئایدیا بوتی خۆکارە، ژ بەر هندێ هەمیشە بوتێ نوکە زێدە دکەت
# ڕێپێدان: 8 = Administrator. بۆ ڕێپێدانا کێمتر ژمارەکا دی دانە
INVITE_PERMISSIONS = 8

DIVIDER = "─" * 18

# ناڤ و وەسفێ کورت بۆ لاپەڕا سەرەکی (ب هێلەک). بەشێ نوی؟ ل ڤێرە ژی زێدە بکە
HOME_INFO = {
    "general": ("گشتی", "فەرمانێن سادە"),
    "info":    ("زانیاری", "ئەندام و سێرڤەر"),
    "economy": ("ئابووری و بانک", "دراڤ، daily و بانک"),
    "hunt":    ("ڕاوکرن", "ئاژەل و Huntbot"),
    "games":   ("یاری", "یاریێن ب دراڤ"),
    "music":   ("میوزیک", "گۆرانی، ڕیزا گۆرانیان و کۆنتڕۆل"),
    "cards":   ("کارتی ئەنیمی", "سندوق، کڕین، مارکێت و جەنگ"),
    "setup":   ("ڕێکخستن", "Welcome و Invite و Left"),
    "mod":     ("مۆدەراسیۆن", "تەنێ بۆ بەرپرسان"),
}

def home_title(key):
    return HOME_INFO.get(key, (CATEGORIES[key]["title"], ""))[0]

def home_short(key):
    return HOME_INFO.get(key, ("", CATEGORIES[key]["desc"]))[1]

# ═══════════════════════════════════════
# بەشێ ٢: لیستا بەشان و فەرمانان
# تەنێ ئەو فەرمانێن د بوتی دا هەین. فەرمانەکا نوی؟ ل ڤێرە زێدە بکە
# {p} = هێمایا فەرمانێ (z)
# ═══════════════════════════════════════
CATEGORIES = {
    "general": {
        "emoji": "🌟",
        "title": "گشتی",
        "desc": "فەرمانێن سادە و بسوود",
        "color": 0x5865F2,
        "commands": [
            ("{p} help", "ئەڤ مینیۆیێ ڤەدکەت (`{p} یارمەتی`)"),
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
            ("{p} bank", "بانکا شاهانە ڤەکە ب دوگمە: دانان، دەرئینان، قازانج، ئاست (`{p} بانک`)"),
            ("{p} dep <بڕ>", f"{CURRENCY} بخە بانکێ، هەر ٢٤ دەمژمێران ٪١٠ قازانج (`all` / `half`)"),
            ("{p} with <بڕ>", f"{CURRENCY} ژ بانکێ دەرئینە (`all` / `half`)"),
            ("{p} bank me @کەس", "کارتا بانکێ یا خوە یان یا کەسەکێ دی نیشان ددەت"),
            ("{p} bank top", "دەوڵەمەندترین ل بانکێ نیشان ددەت"),
            ("{p} bank history", "مێژوویا مامەلەیێن بانکا تە نیشان ددەت"),
        ],
    },
    "hunt": {
        "emoji": "🐾",
        "title": "ڕاوکرن (Zero Hunt)",
        "desc": "ئاژەل ڕاو بکە، کۆم بکە، بفرۆشە و Huntbota خوە بهێز بکە",
        "color": 0x9B59B6,
        "commands": [
            ("{p} hunt", "ئاژەلەکێ ڕاو بکە (`{p} h` / `{p} catch`). نرخ: ١٠ دراو، ١٥ چرکە cooldown"),
            ("{p} zoo", "باخچەیا ئاژەلێن تە (`{p} zoo rare` / `{p} zoo display` / `{p} zoo search <ناڤ>`)"),
            ("{p} sell <ئاژەل/rarity/all>", "ئاژەلان بفرۆشە (`{p} sell wolf 3` / `{p} sell common` / `{p} sell all`)"),
            ("{p} sacrifice <ئاژەل/rarity/all>", "ئاژەلان بکە essence (`{p} essence` بۆ دیتنا بڕێ وێ)"),
            ("{p} lock <ئاژەل>", "ئاژەلەکێ ژ فرۆتنێ بپارێزە (`{p} unlock` بۆ لابرنێ)"),
            ("{p} team", "تیما تە. XP وەردگرن (`{p} team add wolf` / `{p} team remove wolf` / `{p} rename wolf ناڤ`)"),
            ("{p} gems", "gemێن تە (`{p} use <id>` چالاک دکەت، `{p} geminfo <id>`)"),
            ("{p} lootbox", "lootboxێن تە (`{p} lootbox open` / `{p} lootbox history`)"),
            ("{p} inventory", "هەمی تشتێن تە و buffێن چالاک (`{p} bag` / `{p} buffs`)"),
            ("{p} huntbot", "بوتێ ڕاوکرنێ یێ ئۆفلاین (`{p} hb start` / `{p} hb upgrade <stat>` / `{p} hb claim`)"),
            ("{p} owodex <ئاژەل>", "ئینسایکلۆپیدیایا ئاژەلان"),
            ("{p} huntstats", "ئاماریێن ڕاوکرنا تە (`{p} hs`)"),
            ("{p} huntlb", "لیستا پێشەنگێن ڕاوکرنێ (`{p} hlb`)"),
            ("{p} events", "eventێن چالاک (Halloween، Christmas، ...)"),
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
    "music": {
        "emoji": "🎶",
        "title": "میوزیک (Zero Music)",
        "desc": "گۆرانیان ژ YouTube و TikTok ل ڤۆیسێ لێدە، ب دوگمە و ڕیزا گۆرانیان",
        "color": 0x7B2FF7,
        "commands": [
            ("{p} play <ناڤ/لینک>", "گۆرانیەکێ لێددەت یان دکەتە ڕیزێ (`{p} p`). چەند دێڕ = چەند گۆرانی"),
            ("{p} menu", "داشبۆردا هونەرمەندان: هونەرمەندەک و گۆرانیەکێ هەلبژێرە (`{p} songs` / `{p} artists`)"),
            ("{p} join", "بوتی دئینیتە ناڤ ڤۆیسا تە (`{p} j`)"),
            ("{p} pause / {p} resume", "گۆرانیێ ڕادگریت / بەردەوام دکەت"),
            ("{p} skip", "گۆرانیێ دپەڕینیت (`{p} sk` / `{p} next`)"),
            ("{p} stop", "میوزیکێ ڕادگریت و بوت دچیتە دەر (`{p} leave` / `{p} dc`)"),
            ("{p} previous", "گۆرانیا بەری نوکە، یان دوبارە ژ دەستپێکێ ئەگەر پتر ژ ٥ چرکەیان هاتبیتە لێدان (`{p} prev` / `{p} back`)"),
            ("{p} jump <ژمارە>", "ڕاستەخۆ بچە سەر گۆرانیەکێ ل ڕیزێ (`{p} skipto 3`)"),
            ("{p} seek <دەم>", "بپەڕە چرکەیەکێ: `{p} seek 1:30` / `{p} seek +30` / `{p} seek -15`"),
            ("{p} playlist", "کتێبخانەیا تە: Favorites و Recently Played و لیستێن تە، ب دوگمە (`{p} pl`)"),
            ("{p} pl create <ناڤ>", "لیستەکا نوی چێدکەت (هەر کەسەک هەتا ١٠ لیستان)"),
            ("{p} pl add <ناڤ/ژمارە>", "گۆرانیا نوکە دکەتە ناڤ لیستێ (یان دوگمەیا 💾 ل پلەیەرێ)"),
            ("{p} pl play <ناڤ/ژمارە>", "هەمی لیستێ لێددەت (`{p} pl shuffle` بۆ تێکەلکرنێ)"),
            ("{p} pl remove <ناڤ> <ژمارە>", "گۆرانیەکێ ژ لیستێ لادبەت. `{p} pl delete <ناڤ>` هەمی لیستێ ژێدبەت"),
            ("{p} like", "گۆرانیا نوکە دکەتە / لادبەت ژ ❤️ Favorites (یان دوگمەیا ❤️). `{p} likes` بۆ لیستێ"),
            ("{p} recent", "دویماهیک گۆرانیێن تە (Recently Played)"),
            ("{p} loop", "دوبارەکرنەڤە: ناچالاک ← گۆرانی ← ڕیز (`{p} loop song` / `queue` / `off`)"),
            ("{p} volume <1-150>", "دەنگی دگۆڕیت (`{p} vol 50`). بێ ژمارە = دەنگێ نوکە"),
            ("{p} queue", "ڕیزێ لاپەڕە ب لاپەڕە نیشان ددەت (`{p} q`)"),
            ("{p} nowplaying", "گۆرانیا نوکە نیشان ددەت (`{p} np`)"),
            ("{p} shuffle", "ڕیزێ تێکەل دکەت (`{p} mix`)"),
            ("{p} removesong <ژمارە>", "گۆرانیەکێ ژ ڕیزێ لادبەت (`{p} rs 3`)"),
            ("{p} clearqueue", "هەمی ڕیزێ پاقژ دکەت (`{p} cq`)"),
        ],
    },
    "cards": {
        "emoji": "🎴",
        "title": "کارتی ئەنیمی (Zero Cards)",
        "desc": "کارتی ئەنیمی کۆبکەرەوە، بەهێزیان بکە و لە جەنگدا بەکاریان بێنە",
        "color": 0x9B59B6,
        "commands": [
            ("{p} cards", "مێنیوی سەرەکی کارتان ب دوگمە: سندوق، کڕین، کارتێن من، مارکێت (`{p} card` / `{p} gacha`)"),
            ("{p} pull", "ڕاستەوخۆ فرۆشگەها سندوقان ڤەدکەت (Bronze / Gold / Diamond / Legendary)"),
            ("{p} mycards", "کارتێن تە. کارتەکێ هەلبژێرە بۆ بەهێزکرن، پیشاندان، بەخشین، فرۆتن، سڕینەوە (`{p} mc`)"),
            ("{p} showcard <ئایدی>", "کارتەکا خوە ل چاتێ پیشان ددەت (`{p} scard`)"),
            ("{p} cardmarket", "مارکێتا کارتان نیشان ددەت (`{p} cm`)"),
            ("{p} cardsell <ئایدی> <نرخ>", "کارتەکێ دکەیتە مارکێتێ بۆ فرۆتنێ (`{p} csell`)"),
            ("{p} cardunsell <ئایدی>", "کارتەکێ ژ مارکێتێ لادبەت (`{p} cunsell`)"),
            ("{p} buycard <ئایدیا مارکێتێ>", "کارتەکێ ژ مارکێتێ دکڕیت (`{p} cbuy`)"),
            ("{p} cardbattle @کەس <گرەو>", f"جەنگی کارتان لەگەڵ هاوڕێیەک، ب گرەو یان بێ گرەو (`{{p}} cbattle`)"),
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
}

# ═══════════════════════════════════════
# بەشێ ٢.٥: لیستا یاریان (ئەو لیستا پشتی کلیککرنێ ل "یاری" دیار دبیت)
# یاریەکا نوی؟ تەنێ بلۆکەکا نوی ل ڤێرە زێدە بکە، لیست ب خۆکار نوی دبیتەڤە
# "sections" = لیستا (ناڤێ بەشی، دەق). هەر دەقەک نابیت ژ ١٠٠٠ پیتان پتر بیت
# {p} = هێمایا فەرمانێ
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
                "`{p} cf سەر 100` ── ڕیزا نڤیسینێ ژی گرنگ نینە، هەردوو کار دکەن\n"
                "⏱️ ناڤبەرا دوو یاریان دڤێت چەند چرکەیەکان چاڤەڕێ بکەی",
            ),
        ],
    },
}


# ═══════════════════════════════════════
# بەشێ ٢.٦: ڕێنمایا ڕاوکرنێ (پشتی کلیککرنێ ل "ڕاوکرن" دیار دبیت)
# هەر لاپەڕەکێ چەند بلۆکێن ڕوون هەنە: (ناڤ، دەق)
# {p} = هێمایا فەرمانێ. لاپەڕەکا نوی؟ تەنێ بلۆکەکا نوی زێدە بکە
# ═══════════════════════════════════════
HUNT_QUICKSTART = (
    "١️⃣ `{p} hunt` ── ئاژەلەکێ ڕاو بکە 🐾\n"
    "٢️⃣ `{p} zoo` ── سەیری کۆمکرنا خوە بکە 🏞️\n"
    "٣️⃣ `{p} sell all` ── بفرۆشە و دراو وەربگرە 💰"
)

HUNT_PAGES = {
    "start": {
        "emoji": "🚀",
        "title": "دەستپێکرن",
        "short": "ڕاوکرن و دیتنا ئاژەلێن تە",
        "color": 0x2ECC71,
        "sections": [
            (
                "🐾 ڕاوکرن",
                "`{p} hunt`\n"
                "┕ ئاژەلەکێ هەرەمەکی ڕاو دکەی (کورت: `{p} h`)\n"
                f"┕ نرخ: **{HUNT_COST}** دراو ── چاڤەڕێ: **{HUNT_COOLDOWN}** چرکە",
            ),
            (
                "🏞️ باخچەیا ئاژەلێن تە",
                "`{p} zoo`\n"
                "┕ هەمی ئاژەلێن خوە دبینی\n"
                "`{p} zoo rare`\n"
                "┕ تەنێ ئاژەلێن دەگمەن (ناڤێ rarity بنڤیسە)\n"
                "`{p} zoo search wolf`\n"
                "┕ ل دویف ئاژەلەکی بگەڕە\n"
                "`{p} zoo display`\n"
                "┕ لیستەکا کورت، ڕیزکری ل دویف rarity",
            ),
            (
                "📖 ئینسایکلۆپیدیا",
                "`{p} owodex wolf`\n"
                "┕ زانیاریێن تەمام دەربارێ ئاژەلەکی",
            ),
        ],
    },
    "sell": {
        "emoji": "💰",
        "title": "فرۆتن و پاراستن",
        "short": "ئاژەلان بفرۆشە، بکە essence یان بپارێزە",
        "color": 0xF1C40F,
        "sections": [
            (
                "💵 فرۆتن",
                "`{p} sell wolf 3`\n"
                "┕ ٣ دانە wolf دفرۆشیت\n"
                "`{p} sell common`\n"
                "┕ هەمی ئاژەلێن common\n"
                "`{p} sell all`\n"
                "┕ هەمی ئاژەل (ژ بلی ئەوێن lock کری)",
            ),
            (
                "💠 Essence",
                "`{p} sacrifice wolf`\n"
                "┕ ئاژەلی دکەتە essence ب جهێ دراوی (کورت: `{p} sac`)\n"
                "`{p} essence`\n"
                "┕ بڕێ essenceا خوە دبینی\n"
                "💡 essence بۆ باشکرنا Huntbotی دهێتە بکارئینان",
            ),
            (
                "🔒 پاراستن",
                "`{p} lock wolf`\n"
                "┕ ئاژەل نەکەڤیتە ناڤ `sell all`\n"
                "`{p} unlock wolf`\n"
                "┕ دوبارە دشێی بفرۆشی",
            ),
        ],
    },
    "team": {
        "emoji": "⚔️",
        "title": "تیما ئاژەلان",
        "short": "ئاژەلێ دلخوازا خوە بخە ناڤ تیمێ و XP وەربگرە",
        "color": 0xE67E22,
        "sections": [
            (
                "📖 تیم چیە؟",
                "ئەو ئاژەلێن تو دکەیە ناڤ تیما خوە، دگەل هەر ڕاوکرنەکێ **XP** وەردگرن و بهێز دبن",
            ),
            (
                "🛠️ فەرمان",
                "`{p} team`\n"
                "┕ تیما خوە دبینی\n"
                "`{p} team add wolf`\n"
                "┕ ئاژەلەکێ دکەتە ناڤ تیمێ\n"
                "`{p} team remove wolf`\n"
                "┕ ژ تیمێ دەردئینیت\n"
                "`{p} rename wolf ناڤێ-نوی`\n"
                "┕ ناڤێ ئاژەلێ خوە دگۆڕی",
            ),
        ],
    },
    "items": {
        "emoji": "💎",
        "title": "Gem و Lootbox",
        "short": "گەنجینە و ئامرازێن تایبەتێن تە",
        "color": 0x9B59B6,
        "sections": [
            (
                "💎 Gem",
                "`{p} gems`\n"
                "┕ gemێن خوە دبینی\n"
                "`{p} use <id>`\n"
                "┕ gemەکێ چالاک دکەت (id ژ `{p} gems` دبینی)\n"
                "`{p} geminfo <id>`\n"
                "┕ زانیاریێن gemەکێ",
            ),
            (
                "🎁 Lootbox",
                "`{p} lootbox`\n"
                "┕ بۆکسێن خوە دبینی\n"
                "`{p} lootbox open`\n"
                "┕ بۆکسەکێ ڤەدکەی و خەلاتان وەردگری\n"
                "`{p} lootbox history`\n"
                "┕ دویماهیک خەلاتێن تە",
            ),
            (
                "🎒 تشتێن تە",
                "`{p} inventory`\n"
                "┕ هەمی تشتێن خوە (کورت: `{p} bag`)\n"
                "`{p} buffs`\n"
                "┕ تەنێ buffێن چالاک",
            ),
        ],
    },
    "huntbot": {
        "emoji": "🤖",
        "title": "Huntbot",
        "short": "بوتەک کو د ئۆفلاینیا تە دا ڕاو دکەت",
        "color": 0x3498DB,
        "sections": [
            (
                "📖 Huntbot چیە؟",
                "بوتەکە ئاژەلان ڕاو دکەت **تەنانەت دەمێ تو ئۆفلاینی**. تو دنێری، پاشی ئاژەلان وەردگری",
            ),
            (
                "🚀 چەوا بکاردئینم؟",
                "١️⃣ `{p} hb start` ── بوتی دنێری بۆ ڕاوێ\n"
                "٢️⃣ چاڤەڕێ بکە هەتا تەمام دبیت\n"
                "٣️⃣ `{p} hb claim` ── ئاژەلان وەردگری",
            ),
            (
                "🔧 باشکرن",
                "`{p} hb upgrade`\n"
                "┕ لیستا باشکرنان و نرخێن وان\n"
                "`{p} hb upgrade <stat>`\n"
                "┕ بەشەکێ باش دکەت ب **essence** 💠",
            ),
        ],
    },
    "stats": {
        "emoji": "📈",
        "title": "ئامار و Event",
        "short": "ئامار، لیستا پێشەنگان و eventێن چالاک",
        "color": 0xE74C3C,
        "sections": [
            (
                "📊 ئامار",
                "`{p} huntstats`\n"
                "┕ ئاماریێن ڕاوکرنا خوە (کورت: `{p} hs`)",
            ),
            (
                "🏆 پێشەنگ",
                "`{p} huntlb`\n"
                "┕ باشترین ڕاوکەر (کورت: `{p} hlb`)",
            ),
            (
                "🎃 Event",
                "`{p} events`\n"
                "┕ eventێن چالاک (Halloween، Christmas ...)",
            ),
        ],
    },
}

# ═══════════════════════════════════════
# بەشێ ٣: کارت
# ═══════════════════════════════════════

# هێمایێن بکارهاتی بۆ نیشاندانێ (z · zero)
def prefixes_text():
    names = [PREFIX] + [p for p in EXTRA_PREFIXES if p.lower() != PREFIX.lower()]
    return " · ".join(f"`{n} `" for n in names)

def render(text):
    return text.replace("{p}", PREFIX)

# کارتا لاپەڕا سەرەکی
def home_embed(ctx, invite_url):
    total = sum(len(c["commands"]) for c in CATEGORIES.values())
    name = discord.utils.escape_markdown(ctx.author.display_name)
    cats = "\n".join(
        f"{c['emoji']} **{home_title(k)}** ─ {home_short(k)}" for k, c in CATEGORIES.items()
    )
    names = " ‧ ".join(f"`{n}`" for n in [PREFIX] + [p for p in EXTRA_PREFIXES if p.lower() != PREFIX.lower()])
    embed = make_embed(
        f"{BOT_NAME} ─ ناڤەندا یارمەتیێ",
        (
            f"👋 سلاڤ **{name}**!\n"
            f"ژ لیستا خوارێ **بەشەکێ هەلبژێرە** دا فەرمانێن وێ ببینی.\n\n"
            f"{DIVIDER}\n{cats}\n{DIVIDER}\n\n"
            f"🚀 **دەستپێک:** `{PREFIX} daily` ‧ `{PREFIX} bank` ‧ `{PREFIX} slots 100`\n"
            f"🔑 **هێما:** {names}"
        ),
        color=0x5865F2,
        ctx=ctx,
    )
    embed.set_author(name=f"{BOT_NAME} • یارمەتی", icon_url=ctx.bot.user.display_avatar.url)
    embed.add_field(name="⚡ خێرایی", value=f"`{round(ctx.bot.latency * 1000)}ms`")
    embed.add_field(name="📌 فەرمان", value=f"`{total}`")
    if ctx.guild:
        embed.add_field(name="👥 ئەندام", value=f"`{ctx.guild.member_count}`")
    src = gif_source()
    if src:
        embed.set_image(url=src)
    return embed

# کارتا هەر بەشەکێ
def category_embed(ctx, key):
    c = CATEGORIES[key]
    lines = "\n\n".join(
        f"`{render(cmd)}`\n┕ {render(text)}" for cmd, text in c["commands"]
    )
    embed = make_embed(
        f"{c['emoji']}  {c['title']}",
        f"> {c['desc']}\n{DIVIDER}\n{lines}",
        color=c["color"],
        ctx=ctx,
    )
    embed.set_author(name=f"{BOT_NAME} • ناڤەندا یارمەتیێ", icon_url=ctx.bot.user.display_avatar.url)
    src = gif_source()
    if src:
        embed.set_image(url=src)
    return embed

# کارتا لیستا یاریان (پشتی کلیکێ ل "یاری")
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
    embed.set_author(name=f"{BOT_NAME} • ناڤەندا یارمەتیێ", icon_url=ctx.bot.user.display_avatar.url)
    src = gif_source()
    if src:
        embed.set_image(url=src)
    return embed

# کارتا سەرەکی یا ڕاوکرنێ (پشتی کلیکێ ل "ڕاوکرن")
def hunt_overview_embed(ctx):
    c = CATEGORIES["hunt"]
    pages = "\n".join(
        f"{p['emoji']} **{p['title']}** ── {p['short']}" for p in HUNT_PAGES.values()
    )
    embed = make_embed(
        f"{c['emoji']}  ڕاوکرن (Zero Hunt)",
        (
            "> ئاژەل ڕاو بکە، کۆم بکە، بفرۆشە و بهێزتر ببە ✨\n"
            f"{DIVIDER}"
        ),
        color=c["color"],
        ctx=ctx,
    )
    embed.add_field(name="⚡ دەستپێکا خێرا", value=render(HUNT_QUICKSTART), inline=False)
    embed.add_field(name="📂 بەش", value=pages, inline=False)
    embed.add_field(
        name="👇 چەوا بکاربینم؟",
        value="ژ لیستا خوارێ بەشەکێ هەلبژێرە بۆ دیتنا فەرمانان ب ڕوونی",
        inline=False,
    )
    embed.set_author(name=f"{BOT_NAME} • ناڤەندا یارمەتیێ", icon_url=ctx.bot.user.display_avatar.url)
    src = gif_source()
    if src:
        embed.set_image(url=src)
    return embed

# کارتا هەر لاپەڕەکا ڕاوکرنێ
def hunt_page_embed(ctx, key):
    p = HUNT_PAGES[key]
    embed = make_embed(
        f"{p['emoji']}  {p['title']}",
        f"> {p['short']}",
        color=p["color"],
        ctx=ctx,
    )
    for name, value in p["sections"]:
        embed.add_field(name=name, value=render(value), inline=False)
    embed.set_author(name=f"{BOT_NAME} • ڕێنمایا ڕاوکرنێ", icon_url=ctx.bot.user.display_avatar.url)
    return embed

# کارتا یاسایا هەر یاریەکێ
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
    embed.set_author(name=f"{BOT_NAME} • یاسایا یاریێ", icon_url=ctx.bot.user.display_avatar.url)
    src = gif_source()
    if src:
        embed.set_image(url=src)
    return embed

# ═══════════════════════════════════════
# بەشێ ٤: لیست و دوگمە
# ═══════════════════════════════════════

class CategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="لاپەڕا سەرەکی", value="home", emoji="🏠", description="زڤڕین بۆ دەستپێکێ"
            )
        ]
        for key, c in CATEGORIES.items():
            options.append(
                discord.SelectOption(
                    label=home_title(key), value=key, emoji=c["emoji"],
                    description=f"{home_short(key)} • {len(c['commands'])} فەرمان"[:100],
                )
            )
        super().__init__(placeholder="📂 بەشەکێ هەلبژێرە...", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        key = self.values[0]
        if key == "home":
            embed = home_embed(view.ctx, view.invite_url)
        elif key == "games":
            embed = games_overview_embed(view.ctx)
        elif key == "hunt":
            embed = hunt_overview_embed(view.ctx)
        else:
            embed = category_embed(view.ctx, key)
        # لیستا دووەم تەنێ ل بەشێن "یاری" و "ڕاوکرن" دیار دبیت
        view.show_sub_menu(key if key in ("games", "hunt") else None)
        await interaction.response.edit_message(embed=embed, view=view)

# لیستا دووەم: ناڤێن یاریان (تەنێ پشتی کلیکێ ل بەشێ یاری دیار دبیت)
class GameSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="هەمی یاری", value="all", emoji="📋", description="زڤڕین بۆ لیستا یاریان"
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

# لیستا دووەم بۆ ڕاوکرنێ
class HuntSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="دەستپێکا ڕاوکرنێ", value="all", emoji="🏠", description="زڤڕین بۆ کارتا سەرەکی"
            )
        ]
        for key, p in HUNT_PAGES.items():
            options.append(
                discord.SelectOption(label=p["title"], value=key, emoji=p["emoji"], description=p["short"][:100])
            )
        super().__init__(placeholder="🐾 بەشەکێ ڕاوکرنێ هەلبژێرە...", min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        key = self.values[0]
        if key == "all":
            embed = hunt_overview_embed(view.ctx)
        else:
            embed = hunt_page_embed(view.ctx, key)
        await interaction.response.edit_message(embed=embed, view=view)

class HelpView(discord.ui.View):
    def __init__(self, ctx, invite_url):
        super().__init__(timeout=180)  # پشتی ٣ خولەکان ناچالاک دبیت
        self.ctx = ctx
        self.invite_url = invite_url
        self.message = None
        self.sub_select = None   # لیستا دووەم (یاری یان بەشێن ڕاوکرنێ)
        self.sub_kind = None

        self.add_item(CategorySelect())
        # دوگمەیێن لینکێ (ڕیزا سیێ، چونکی ڕیزا دووێ بۆ لیستا یاریانە)
        self.add_item(discord.ui.Button(label="زێدەکرنا بوتی", url=invite_url, emoji="🤖", row=2))
        if SUPPORT_URL:
            self.add_item(discord.ui.Button(label="سێرڤەرێ ساپۆرتێ", url=SUPPORT_URL, emoji="💬", row=2))

    # لیستا دووەم نیشان بدە یان بشارەڤە (kind: "games" / "hunt" / None)
    def show_sub_menu(self, kind):
        if kind == self.sub_kind:
            return
        if self.sub_select is not None:
            self.remove_item(self.sub_select)
            self.sub_select = None
        if kind == "games":
            self.sub_select = GameSelect()
        elif kind == "hunt":
            self.sub_select = HuntSelect()
        if self.sub_select is not None:
            self.add_item(self.sub_select)
        self.sub_kind = kind

    # تەنێ خودانێ help دشێت بکاربینیت
    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                f"❌ ئەڤ مینیۆیە بۆ کەسەکێ دی یە. خوە `{PREFIX} help` بنڤیسە.", ephemeral=True
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
# Cog: بەشەکێ جوداکری یێ بوتی
# ═══════════════════════════════════════
class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # !help (یان !h یان !یارمەتی یان !commands)
    @commands.command(name="help", aliases=["یارمەتی", "commands", "cmd", "cmds"])
    async def help_command(self, ctx):
        invite_url = (
            f"https://discord.com/oauth2/authorize?client_id={ctx.bot.user.id}"
            f"&permissions={INVITE_PERMISSIONS}&integration_type=0&scope=bot"
        )
        view = HelpView(ctx, invite_url)
        path, filename = current_media()
        file = discord.File(path, filename=filename) if path else None
        view.message = await ctx.send(embed=home_embed(ctx, invite_url), view=view, file=file)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))

