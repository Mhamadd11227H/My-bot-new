import os

import discord
from discord.ext import commands

from utils import (
    make_embed, BOT_NAME, PREFIX, EXTRA_PREFIXES, CURRENCY,
    E_EGGPLANT, E_GRAPE, E_ORANGE, E_CHERRY, E_DIAMOND,
)

# نرخ و cooldown ی ڕاوکردن لە hunt_data.py وەردەگیرێت (ئەگەر نەبوو: ١٠ و ١٥)
try:
    from . import hunt_data as _HD
    HUNT_COST, HUNT_COOLDOWN = _HD.HUNT_COST, _HD.HUNT_COOLDOWN
except Exception:
    HUNT_COST, HUNT_COOLDOWN = 10, 15

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

# وێنەی هەموو لاپەڕەکان. ڕیزبەندی:
# ١. ئەو وێنەیەی بە فەرمانی  z media set help <ناو>  دیاریت کردووە (باشترین ڕێگا)
# ٢. فایلی zero.gif ئەگەر لەتەنیشت bot.py یان لەناو cogs دانرابوو
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
    """(path, filename) ی وێنەی ئێستا، یان (None, None)"""
    found = slot_file("help")
    if found:
        return found
    path = _find_gif()
    return (path, "zero.gif") if path else (None, None)

def gif_source():
    path, filename = current_media()
    return f"attachment://{filename}" if path else GIF_URL

# دوگمەی سێرڤەری ساپۆرت (ئەگەر نەتەوێت: None)
SUPPORT_URL = "https://discord.gg/GK6WZbxuUK"

# دوگمەی زیادکردنی بوت. ئایدی بوت خۆکارە، بۆیە هەمیشە بوتی ئێستا زیاد دەکات
# ڕێگەپێدانەکان: 8 = Administrator. بۆ ڕێگەی کەمتر ژمارەیەکی تر دابنێ
INVITE_PERMISSIONS = 8

DIVIDER = "─" * 18

# ناڤ و وەسفێ کورت بۆ لاپەڕەی سەرەکی (ب هێڵەک). بەشێ نوی؟ لێرە ژی زێدە بکە
HOME_INFO = {
    "general": ("گشتی", "فەرمانێن سادە"),
    "info":    ("زانیاری", "ئەندام و سێرڤەر"),
    "economy": ("ئابووری و بانک", "دراڤ، daily و بانک"),
    "hunt":    ("ڕاوکردن", "ئاژەل و Huntbot"),
    "games":   ("یاری", "یاریێن ب دراڤ"),
    "music":   ("میوزیک", "گۆرانی، ڕیزبەندی و کۆنتڕۆڵ"),
    "setup":   ("ڕێکخستن", "Welcome و Invite و Left"),
    "mod":     ("مۆدەراسیۆن", "تەنێ بۆ بەرپرسان"),
}

def home_title(key):
    return HOME_INFO.get(key, (CATEGORIES[key]["title"], ""))[0]

def home_short(key):
    return HOME_INFO.get(key, ("", CATEGORIES[key]["desc"]))[1]

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
        "title": "ڕاوکردن (Zero Hunt)",
        "desc": "ئاژەڵ ڕاو بکە، کۆیان بکەرەوە، بیانفرۆشە و Huntbot ی خۆت زیاد بکە",
        "color": 0x9B59B6,
        "commands": [
            ("{p} hunt", "ئاژەڵێک ڕاو بکە (`{p} h` / `{p} catch`). نرخ: ١٠ دراو، ١٥ چرکە cooldown"),
            ("{p} zoo", "باخچەی ئاژەڵەکانت (`{p} zoo rare` / `{p} zoo display` / `{p} zoo search <ناو>`)"),
            ("{p} sell <ئاژەڵ/rarity/all>", "ئاژەڵ بفرۆشە (`{p} sell wolf 3` / `{p} sell common` / `{p} sell all`)"),
            ("{p} sacrifice <ئاژەڵ/rarity/all>", "ئاژەڵ بکە essence (`{p} essence` بۆ بینینی بڕەکەی)"),
            ("{p} lock <ئاژەڵ>", "ئاژەڵێک بپارێزە لە فرۆشتن (`{p} unlock` بۆ لابردنی)"),
            ("{p} team", "تیمی پێت. XP وەردەگرن (`{p} team add wolf` / `{p} team remove wolf` / `{p} rename wolf ناو`)"),
            ("{p} gems", "gem ەکانت (`{p} use <id>` چالاکی دەکات، `{p} geminfo <id>`)"),
            ("{p} lootbox", "lootbox ەکانت (`{p} lootbox open` / `{p} lootbox history`)"),
            ("{p} inventory", "هەموو شتەکانت و buff ە چالاکەکان (`{p} bag` / `{p} buffs`)"),
            ("{p} huntbot", "بۆتی ڕاوکردنی ئۆفلاین (`{p} hb start` / `{p} hb upgrade <stat>` / `{p} hb claim`)"),
            ("{p} owodex <ئاژەڵ>", "ئینسایکلۆپیدیای ئاژەڵەکان"),
            ("{p} huntstats", "ئاماری ڕاوکردنت (`{p} hs`)"),
            ("{p} huntlb", "لیستی پێشەنگی ڕاوکردن (`{p} hlb`)"),
            ("{p} events", "event ە چالاکەکان (Halloween، Christmas، ...)"),
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
        "desc": "گۆرانی لە YouTube و TikTok لێبدە لە ڤۆیس، ب دوگمە و ڕیزبەندی",
        "color": 0x7B2FF7,
        "commands": [
            ("{p} play <ناو/لینک>", "گۆرانییەک لێدەدات یان دەیخاتە ڕیزبەندی (`{p} p`). چەند دێڕ = چەند گۆرانی"),
            ("{p} menu", "داشبۆردی هونەرمەندان: هونەرمەندێک و گۆرانییەک هەڵبژێرە (`{p} songs` / `{p} artists`)"),
            ("{p} join", "بوت دەهێنیتە ناو ڤۆیسەکەت (`{p} j`)"),
            ("{p} pause / {p} resume", "گۆرانی دەوەستێنێت / بەردەوامی دەکات"),
            ("{p} skip", "گۆرانی دەپەڕێنێت (`{p} sk` / `{p} next`)"),
            ("{p} stop", "میوزیک ڕادەگرێت و بوت دەچێتە دەرەوە (`{p} leave` / `{p} dc`)"),
            ("{p} previous", "گۆرانی پێشوو، یان دووبارە لە سەرەتاوە ئەگەر زیاتر لە ٥ چرکە لێدرابێت (`{p} prev` / `{p} back`)"),
            ("{p} jump <ژمارە>", "ڕاستەوخۆ بچۆ سەر گۆرانییەک لە ڕیزبەندی (`{p} skipto 3`)"),
            ("{p} seek <کات>", "بپەڕێ بۆ چرکەیەک: `{p} seek 1:30` / `{p} seek +30` / `{p} seek -15`"),
            ("{p} playlist", "کتێبخانەی خۆت: Favorites و Recently Played و لیستەکانت، ب دوگمە (`{p} pl`)"),
            ("{p} pl create <ناو>", "لیستێکی نوێ دروست دەکات (هەر کەسێک تا ١٠ لیست)"),
            ("{p} pl add <ناو/ژمارە>", "گۆرانی ئێستا دەخاتە ناو لیست (یان دوگمەی 💾 لە پلەیەر)"),
            ("{p} pl play <ناو/ژمارە>", "هەموو لیستەکە لێدەدات (`{p} pl shuffle` بۆ تێکەڵ)"),
            ("{p} pl remove <ناو> <ژمارە>", "گۆرانییەک لە لیست لادەبات. `{p} pl delete <ناو>` هەموو لیستەکە دەسڕێتەوە"),
            ("{p} like", "گۆرانی ئێستا دەخاتە / لادەبات لە ❤️ Favorites (یان دوگمەی ❤️). `{p} likes` بۆ لیستەکە"),
            ("{p} recent", "کۆتا گۆرانییەکانی تۆ (Recently Played)"),
            ("{p} loop", "دووبارەکردنەوە: ناچالاک ← گۆرانی ← ڕیزبەندی (`{p} loop song` / `queue` / `off`)"),
            ("{p} volume <1-150>", "دەنگ دەگۆڕێت (`{p} vol 50`). بێ ژمارە = دەنگی ئێستا"),
            ("{p} queue", "ڕیزبەندی پەڕە بە پەڕە نیشان دەدات (`{p} q`)"),
            ("{p} nowplaying", "گۆرانی ئێستا نیشان دەدات (`{p} np`)"),
            ("{p} shuffle", "ڕیزبەندی تێکەڵ دەکات (`{p} mix`)"),
            ("{p} removesong <ژمارە>", "گۆرانییەک لە ڕیزبەندی لادەبات (`{p} rs 3`)"),
            ("{p} clearqueue", "هەموو ڕیزبەندی پاک دەکاتەوە (`{p} cq`)"),
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
# بەشی ٢.٦: ڕێنمایی ڕاوکردن (دوای کلیککردن لە "ڕاوکردن" دەردەکەوێت)
# هەر لاپەڕەیەک چەند بلۆکێکی ڕوونی هەیە: (ناو، دەق)
# {p} = هێمای فەرمان. لاپەڕەی نوێ؟ تەنها بلۆکێکی نوێ زیاد بکە
# ═══════════════════════════════════════
HUNT_QUICKSTART = (
    "١️⃣ `{p} hunt` ── ئاژەڵێک ڕاو بکە 🐾\n"
    "٢️⃣ `{p} zoo` ── سەیری کۆکراوەکانت بکە 🏞️\n"
    "٣️⃣ `{p} sell all` ── بیانفرۆشە و دراو وەربگرە 💰"
)

HUNT_PAGES = {
    "start": {
        "emoji": "🚀",
        "title": "دەستپێکردن",
        "short": "ڕاوکردن و بینینی ئاژەڵەکانت",
        "color": 0x2ECC71,
        "sections": [
            (
                "🐾 ڕاوکردن",
                "`{p} hunt`\n"
                "┕ ئاژەڵێکی هەڕەمەکی ڕاو دەکەیت (کورت: `{p} h`)\n"
                f"┕ نرخ: **{HUNT_COST}** دراو ── چاوەڕێی: **{HUNT_COOLDOWN}** چرکە",
            ),
            (
                "🏞️ باخچەی ئاژەڵەکانت",
                "`{p} zoo`\n"
                "┕ هەموو ئاژەڵەکانت دەبینیت\n"
                "`{p} zoo rare`\n"
                "┕ تەنها ئاژەڵە دەگمەنەکان (ناوی rarity بنووسە)\n"
                "`{p} zoo search wolf`\n"
                "┕ بەدوای ئاژەڵێکدا بگەڕێ\n"
                "`{p} zoo display`\n"
                "┕ لیستێکی کورت، ڕیزکراو بەپێی rarity",
            ),
            (
                "📖 ئینسایکلۆپیدیا",
                "`{p} owodex wolf`\n"
                "┕ زانیاری تەواو دەربارەی ئاژەڵێک",
            ),
        ],
    },
    "sell": {
        "emoji": "💰",
        "title": "فرۆشتن و پاراستن",
        "short": "ئاژەڵەکان بفرۆشە، بیکە essence یان بیپارێزە",
        "color": 0xF1C40F,
        "sections": [
            (
                "💵 فرۆشتن",
                "`{p} sell wolf 3`\n"
                "┕ ٣ دانە wolf دەفرۆشێت\n"
                "`{p} sell common`\n"
                "┕ هەموو ئاژەڵە common ەکان\n"
                "`{p} sell all`\n"
                "┕ هەموو ئاژەڵەکان (جگە لەوانەی lock کراون)",
            ),
            (
                "💠 Essence",
                "`{p} sacrifice wolf`\n"
                "┕ ئاژەڵەکە دەکات بە essence بەجیاتی دراو (کورت: `{p} sac`)\n"
                "`{p} essence`\n"
                "┕ بڕی essence ی خۆت دەبینیت\n"
                "💡 essence بۆ باشکردنی Huntbot بەکاردێت",
            ),
            (
                "🔒 پاراستن",
                "`{p} lock wolf`\n"
                "┕ ئاژەڵەکە ناکەوێتە ناو `sell all`\n"
                "`{p} unlock wolf`\n"
                "┕ دووبارە دەتوانرێت بفرۆشرێت",
            ),
        ],
    },
    "team": {
        "emoji": "⚔️",
        "title": "تیمی ئاژەڵەکان",
        "short": "ئاژەڵی دڵخوازت بخە ناو تیم و XP وەربگرە",
        "color": 0xE67E22,
        "sections": [
            (
                "📖 تیم چییە؟",
                "ئەو ئاژەڵانەی دەیانخەیتە ناو تیمەکەت، لەگەڵ هەر ڕاوکردنێک **XP** وەردەگرن و بەهێز دەبن",
            ),
            (
                "🛠️ فەرمانەکان",
                "`{p} team`\n"
                "┕ تیمەکەت دەبینیت\n"
                "`{p} team add wolf`\n"
                "┕ ئاژەڵێک دەخاتە ناو تیم\n"
                "`{p} team remove wolf`\n"
                "┕ لە تیم دەری دەهێنێت\n"
                "`{p} rename wolf ناوی-نوێ`\n"
                "┕ ناوی ئاژەڵەکەت دەگۆڕیت",
            ),
        ],
    },
    "items": {
        "emoji": "💎",
        "title": "Gem و Lootbox",
        "short": "گەنجینە و ئامرازە تایبەتەکانت",
        "color": 0x9B59B6,
        "sections": [
            (
                "💎 Gem",
                "`{p} gems`\n"
                "┕ gem ەکانت دەبینیت\n"
                "`{p} use <id>`\n"
                "┕ gem ێک چالاک دەکات (id لە `{p} gems` دەبینیت)\n"
                "`{p} geminfo <id>`\n"
                "┕ زانیاری gem ێک",
            ),
            (
                "🎁 Lootbox",
                "`{p} lootbox`\n"
                "┕ بۆکسەکانت دەبینیت\n"
                "`{p} lootbox open`\n"
                "┕ بۆکسێک دەکەیتەوە و خەڵات وەردەگریت\n"
                "`{p} lootbox history`\n"
                "┕ دوایین خەڵاتەکانت",
            ),
            (
                "🎒 شتەکانت",
                "`{p} inventory`\n"
                "┕ هەموو شتەکانت (کورت: `{p} bag`)\n"
                "`{p} buffs`\n"
                "┕ تەنها buff ە چالاکەکان",
            ),
        ],
    },
    "huntbot": {
        "emoji": "🤖",
        "title": "Huntbot",
        "short": "بۆتێک کە لە ئۆفلاینیشدا بۆت ڕاو دەکات",
        "color": 0x3498DB,
        "sections": [
            (
                "📖 Huntbot چییە؟",
                "بۆتێکە ئاژەڵ ڕاو دەکات **تەنانەت کاتێک تۆ ئۆفلاینیت**. دەینێریت، دواتر ئاژەڵەکان وەردەگریتەوە",
            ),
            (
                "🚀 چۆن بەکاری دەهێنم؟",
                "١️⃣ `{p} hb start` ── بۆتەکە دەنێریت بۆ ڕاو\n"
                "٢️⃣ چاوەڕێ بکە تا تەواو دەبێت\n"
                "٣️⃣ `{p} hb claim` ── ئاژەڵەکان وەردەگریت",
            ),
            (
                "🔧 باشکردن",
                "`{p} hb upgrade`\n"
                "┕ لیستی باشکردنەکان و نرخیان\n"
                "`{p} hb upgrade <stat>`\n"
                "┕ بەشێک باش دەکات بە **essence** 💠",
            ),
        ],
    },
    "stats": {
        "emoji": "📈",
        "title": "ئامار و Event",
        "short": "ئامار، لیستی پێشەنگ و event ە چالاکەکان",
        "color": 0xE74C3C,
        "sections": [
            (
                "📊 ئامار",
                "`{p} huntstats`\n"
                "┕ ئاماری ڕاوکردنی خۆت (کورت: `{p} hs`)",
            ),
            (
                "🏆 پێشەنگەکان",
                "`{p} huntlb`\n"
                "┕ باشترین ڕاوکەرەکان (کورت: `{p} hlb`)",
            ),
            (
                "🎃 Event",
                "`{p} events`\n"
                "┕ event ە چالاکەکان (Halloween، Christmas ...)",
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
    name = discord.utils.escape_markdown(ctx.author.display_name)
    cats = "\n".join(
        f"{c['emoji']} **{home_title(k)}** ─ {home_short(k)}" for k, c in CATEGORIES.items()
    )
    names = " ‧ ".join(f"`{n}`" for n in [PREFIX] + [p for p in EXTRA_PREFIXES if p.lower() != PREFIX.lower()])
    embed = make_embed(
        f"{BOT_NAME} ─ ناوەندی یارمەتی",
        (
            f"👋 سڵاو **{name}**!\n"
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

# کارتی هەر بەشێک
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

# کارتی سەرەکی ڕاوکردن (دوای کلیک لە "ڕاوکردن")
def hunt_overview_embed(ctx):
    c = CATEGORIES["hunt"]
    pages = "\n".join(
        f"{p['emoji']} **{p['title']}** ── {p['short']}" for p in HUNT_PAGES.values()
    )
    embed = make_embed(
        f"{c['emoji']}  ڕاوکردن (Zero Hunt)",
        (
            "> ئاژەڵ ڕاو بکە، کۆیان بکەرەوە، بیانفرۆشە و بەهێزتر ببە ✨\n"
            f"{DIVIDER}"
        ),
        color=c["color"],
        ctx=ctx,
    )
    embed.add_field(name="⚡ دەستپێکی خێرا", value=render(HUNT_QUICKSTART), inline=False)
    embed.add_field(name="📂 بەشەکان", value=pages, inline=False)
    embed.add_field(
        name="👇 چۆن بەکاری بهێنم؟",
        value="لە لیستی خوارەوە بەشێک هەڵبژێرە بۆ بینینی فەرمانەکان بە ڕوونی",
        inline=False,
    )
    embed.set_author(name=f"{BOT_NAME} • ناوەندی یارمەتی", icon_url=ctx.bot.user.display_avatar.url)
    src = gif_source()
    if src:
        embed.set_image(url=src)
    return embed

# کارتی هەر لاپەڕەیەکی ڕاوکردن
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
    embed.set_author(name=f"{BOT_NAME} • ڕێنمایی ڕاوکردن", icon_url=ctx.bot.user.display_avatar.url)
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
                discord.SelectOption(
                    label=home_title(key), value=key, emoji=c["emoji"],
                    description=f"{home_short(key)} • {len(c['commands'])} فەرمان"[:100],
                )
            )
        super().__init__(placeholder="📂 بەشێک هەڵبژێرە...", min_values=1, max_values=1, options=options, row=0)

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
        # لیستی دووەم تەنها لە بەشی "یاری" و "ڕاوکردن" دەردەکەوێت
        view.show_sub_menu(key if key in ("games", "hunt") else None)
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

# لیستی دووەم بۆ ڕاوکردن
class HuntSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="سەرەتای ڕاوکردن", value="all", emoji="🏠", description="گەڕانەوە بۆ کارتی سەرەکی"
            )
        ]
        for key, p in HUNT_PAGES.items():
            options.append(
                discord.SelectOption(label=p["title"], value=key, emoji=p["emoji"], description=p["short"][:100])
            )
        super().__init__(placeholder="🐾 بەشێکی ڕاوکردن هەڵبژێرە...", min_values=1, max_values=1, options=options, row=1)

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
        super().__init__(timeout=180)  # دوای ٣ خولەک ناچالاک دەبێت
        self.ctx = ctx
        self.invite_url = invite_url
        self.message = None
        self.sub_select = None   # لیستی دووەم (یارییەکان یان بەشەکانی ڕاوکردن)
        self.sub_kind = None

        self.add_item(CategorySelect())
        # دوگمەکانی لینک (ڕیزی سێیەم، چونکە ڕیزی دووەم بۆ لیستی یارییەکانە)
        self.add_item(discord.ui.Button(label="زیادکردنی بوت", url=invite_url, emoji="🤖", row=2))
        if SUPPORT_URL:
            self.add_item(discord.ui.Button(label="سێرڤەری ساپۆرت", url=SUPPORT_URL, emoji="💬", row=2))

    # لیستی دووەم پیشان بدە یان بیشارەوە (kind: "games" / "hunt" / None)
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

