import asyncio
import math
import random
import sqlite3
import time
import types

import discord
from discord.ext import commands

from database import db, get_user, parse_bet
from utils import (
    PREFIX, CURRENCY, CASH_EMOJI, SPIN_EMOJI,
    E_EGGPLANT, E_GRAPE, E_ORANGE, E_CHERRY, E_DIAMOND,
    PURPLE, GOLD, make_embed, bet_error_text,
)

# ═══════════════════════════════════════
# بەشی ١: ڕێکخستنەکان (لێرە دەستکاری بکە)
# ═══════════════════════════════════════

# ئەمانە بەهای بنەڕەتین. ئەدمین دەتوانێت بیانگۆڕێت بە فەرمانی:
# !slots config <ناو> <بەها>   (نموونە: !slots config max_bet 100000)
# گۆڕانکارییەکان لە داتابەیس هەڵدەگیرێن
DEFAULT_CONFIG = {
    "min_bet": 1,             # کەمترین شەرت
    "max_bet": 50_000,        # زۆرترین شەرت
    "cooldown": 8,            # چەند چرکە چاوەڕێ بکەیت لەنێوان دوو سلۆت
    "jackpot_enabled": 1,     # جاکپۆتی پەرەسەندوو: 1 = چالاک، 0 = ناچالاک
    "jackpot_percent": 0.5,   # چەند سەدی هەر شەرتێک دەچێتە ناو جاکپۆت
}
# سنووری ئەو بەهایانەی ئەدمین دەتوانێت دایانبنێت (کەمترین، زۆرترین)
CONFIG_LIMITS = {
    "min_bet": (1, 1_000_000_000),
    "max_bet": (1, 1_000_000_000),
    "cooldown": (0, 3600),
    "jackpot_enabled": (0, 1),
    "jackpot_percent": (0, 20),
}

SPIN_STEP = 1           # چەند چرکە لەنێوان هەر هێمایەک کە دەوەستێت (چەپ، ڕاست، ناوەڕاست)
SPIN_BUTTONS = False    # دوگمەی خێرا (دووبارە، دوو ئەوەندە، نیوە) لەژێر ئەنجامەکە
SHOW_DETAILS = True     # هێڵی چوارەم: چەند ئەوەندە، قازانج و باڵانس
HISTORY_PER_PAGE = 5    # چەند یاری لە هەر لاپەڕەیەکی history

# ─── جاکپۆتی پەرەسەندوو (جیاوازە لە ٥ ئاستی بردنەوە) ───
JACKPOT_CHANCE = 0.0002  # ئەگەری هەر سلۆتێک (0.0002 = ٪٠.٠٢ = ١ لە ٥٠٠٠)
JACKPOT_MIN_BET = 100    # کەمترین شەرت بۆ ئەوەی بتوانێت جاکپۆت ببات
JACKPOT_SEED = 1000      # جاکپۆت لە چەند دەست پێ دەکات (دوای هەر بردنەوە)
JACKPOT_EMOJI = "7️⃣"    # هێمای تایبەتی جاکپۆت (تەنها لە کاتی بردنەوەی جاکپۆت دەردەکەوێت)

# ئەو نووسینانەی لە سلۆت دەردەکەون (وەک OwO). دەتوانیت بیانکەیت بە کوردی
TXT_BET = "bet"
TXT_WON = "and won"
TXT_NOTHING = "and won nothing... :c"

# ═══════════════════════════════════════
# بەشی ٢: خشتەی بردنەوە و ئەگەرەکان
# ═══════════════════════════════════════

# هەر ڕیزێک: (ناو، ئیمۆجی، چەند ئەوەندەی شەرت، ئەگەر بە سەدی)
# ناوەکان (eggplant, heart...) تەنها کلیلی ناوخۆیین و لە مێژووی داتابەیس هەڵدەگیرێن،
# بۆیە مەیانگۆڕە. ئەوەی یاریزان دەیبینێت ئیمۆجییەکەیە (utils.py):
# eggplant=E_EGGPLANT، heart=E_GRAPE، cherry=E_ORANGE، cowoncy=E_CHERRY، owo=E_DIAMOND
# ئیمۆجی ڕیزێک بگۆڕیت، تەنها ستوونی دووەم لەو ڕیزە بگۆڕە
SYMBOLS = [
    ("eggplant", E_EGGPLANT, 1, 20.0),
    ("heart",    E_GRAPE,    2, 20.0),
    ("cherry",   E_ORANGE,   3, 5.0),
    ("cowoncy",  E_CHERRY,   4, 2.5),
    ("owo",      E_DIAMOND,  10, 1.0),
]
# دۆڕان = ١٠٠ − کۆی ئەگەرەکانی سەرەوە (واتە ٪٥١.٥)

# کاتێک دەدۆڕێت، هێماکان بەم ئەگەرە پیشان دەدرێن (هەمان ڕیزبەندی SYMBOLS)
LOSS_DISPLAY_WEIGHTS = [35, 28, 20, 12, 5]

# پشکنینی خشتەکە و هەژمارکردنی گەڕانەوەی چاوەڕوانکراو (RTP)
def validate_table():
    if any(p < 0 for _, _, _, p in SYMBOLS):
        raise ValueError("ئەگەر نابێت سالب بێت")
    total = sum(p for _, _, _, p in SYMBOLS)
    if total > 100 + 1e-9:
        raise ValueError(f"کۆی ئەگەرەکان لە ١٠٠٪ زیاترە: {total}")
    loss = round(100 - total, 6)
    rtp = sum(m * p / 100 for _, _, m, p in SYMBOLS)
    return loss, rtp

LOSS_PERCENT, BASE_RTP = validate_table()

KEY_EMOJI = {key: emoji for key, emoji, _, _ in SYMBOLS}
KEY_EMOJI["jackpot"] = JACKPOT_EMOJI

# ژمارە هەڵبژێرەری ئاسایشی (os.urandom) نەک random ی ئاسایی
rng = random.SystemRandom()

# سلۆتەکە دەسووڕێنێت. دەگەڕێنێتەوە: هێماکان، چەند ئەوەندە، ئایا جاکپۆتە
def roll_outcome(jackpot_possible):
    # ١) جاکپۆت: ئەگەرێکی جیاوازە و لە ٥ ئاستەکە جیایە
    if jackpot_possible and rng.random() < JACKPOT_CHANCE:
        return {"keys": ["jackpot"] * 3, "mult": 0, "jackpot": True}

    # ٢) ئاستەکانی بردنەوە: ٣ هێمای وەک یەک
    roll = rng.random() * 100
    acc = 0.0
    for key, _, mult, percent in SYMBOLS:
        acc += percent
        if roll < acc:
            return {"keys": [key] * 3, "mult": mult, "jackpot": False}

    # ٣) دۆڕان: هەرگیز ٣ هێمای وەک یەک نابێت (دوو هێمای وەک یەکیش دۆڕانە)
    keys = [s[0] for s in SYMBOLS]
    while True:
        picked = rng.choices(keys, weights=LOSS_DISPLAY_WEIGHTS, k=3)
        if not (picked[0] == picked[1] == picked[2]):
            return {"keys": picked, "mult": 0, "jackpot": False}

# ═══════════════════════════════════════
# بەشی ٣: داتابەیس (هەمان داتابەیسی ئابووری)
# ═══════════════════════════════════════

db.executescript(f"""
CREATE TABLE IF NOT EXISTS slot_stats (
    user_id INTEGER PRIMARY KEY,
    spins INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    total_bet INTEGER NOT NULL DEFAULT 0,
    total_payout INTEGER NOT NULL DEFAULT 0,
    total_winnings INTEGER NOT NULL DEFAULT 0,
    total_losses INTEGER NOT NULL DEFAULT 0,
    biggest_win INTEGER NOT NULL DEFAULT 0,
    biggest_loss INTEGER NOT NULL DEFAULT 0,
    win_streak INTEGER NOT NULL DEFAULT 0,
    best_streak INTEGER NOT NULL DEFAULT 0,
    best_multiplier INTEGER NOT NULL DEFAULT 0,
    last_bet INTEGER NOT NULL DEFAULT 0,
    last_spin REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS slot_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    bet INTEGER NOT NULL,
    symbols TEXT NOT NULL,
    multiplier INTEGER NOT NULL,
    payout INTEGER NOT NULL,
    net INTEGER NOT NULL,
    ts REAL NOT NULL,
    jackpot INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_slot_history_user ON slot_history (user_id, id);
CREATE TABLE IF NOT EXISTS slot_jackpot (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    amount INTEGER NOT NULL
);
INSERT OR IGNORE INTO slot_jackpot (id, amount) VALUES (1, {int(JACKPOT_SEED)});
CREATE TABLE IF NOT EXISTS slot_jackpot_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    bet INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS slot_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
""")

# ─── ڕێکخستنەکان (ئەدمین) ───
def get_cfg(key):
    default = DEFAULT_CONFIG[key]
    row = db.execute("SELECT value FROM slot_config WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    try:
        value = float(row[0])
    except ValueError:
        return default
    return int(value) if isinstance(default, int) else value

def set_cfg(key, value):
    db.execute(
        "INSERT INTO slot_config (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )
    db.commit()

def get_jackpot():
    return db.execute("SELECT amount FROM slot_jackpot WHERE id = 1").fetchone()[0]

def get_last_bet(user_id):
    row = db.execute("SELECT last_bet FROM slot_stats WHERE user_id = ?", (user_id,)).fetchone()
    return row[0] if row else 0

def get_last_spin(user_id):
    row = db.execute("SELECT last_spin FROM slot_stats WHERE user_id = ?", (user_id,)).fetchone()
    return row[0] if row else 0

class SpinError(Exception):
    pass

# ═══════════════════════════════════════
# بەشی ٤: مامەڵەی سلۆت (Transaction)
# هەموو شتەکان (دراو، جاکپۆت، ئامار، مێژوو) لە یەک مامەڵەدان:
# یان هەموویان دەنووسرێن، یان هیچیان. دراو نە دروست دەبێت نە دەفەوتێت
# ═══════════════════════════════════════

def commit_spin(uid, bet, outcome, contribution):
    now = time.time()
    if db.in_transaction:
        db.commit()
    db.execute("BEGIN IMMEDIATE")  # قفڵکردنی داتابەیس: ناهێڵێت دوو مامەڵە پێکەوە بن
    try:
        row = db.execute("SELECT coins FROM users WHERE user_id = ?", (uid,)).fetchone()
        if row is None or row[0] < bet:
            raise SpinError("insufficient")
        balance = row[0]

        # جاکپۆت: بەشێک لە شەرتەکە دەچێتە ناو جاکپۆت
        pool = get_jackpot() + contribution
        jackpot_hit = outcome["jackpot"]
        if jackpot_hit:
            payout = pool          # هەموو جاکپۆتەکە
            pool = int(JACKPOT_SEED)  # جاکپۆت دەست پێدەکاتەوە (تەنها یەک جار دەدرێت)
            db.execute(
                "INSERT INTO slot_jackpot_log (user_id, bet, amount, ts) VALUES (?, ?, ?, ?)",
                (uid, bet, payout, now),
            )
        else:
            payout = bet * outcome["mult"]
        db.execute("UPDATE slot_jackpot SET amount = ? WHERE id = 1", (pool,))

        net = payout - bet
        new_balance = balance - bet + payout
        db.execute("UPDATE users SET coins = ? WHERE user_id = ?", (new_balance, uid))

        # ئامار
        db.execute("INSERT OR IGNORE INTO slot_stats (user_id) VALUES (?)", (uid,))
        (spins, wins, total_bet, total_payout, total_winnings, total_losses,
         biggest_win, biggest_loss, streak, best_streak, best_mult) = db.execute(
            "SELECT spins, wins, total_bet, total_payout, total_winnings, total_losses, "
            "biggest_win, biggest_loss, win_streak, best_streak, best_multiplier "
            "FROM slot_stats WHERE user_id = ?", (uid,)
        ).fetchone()

        won = payout > 0                       # هەر ٣ هێمای وەک یەک = بردنەوە
        eff_mult = payout // bet               # چەند ئەوەندەی شەرت (بۆ جاکپۆتیش)
        streak = streak + 1 if won else 0
        db.execute(
            "UPDATE slot_stats SET spins=?, wins=?, total_bet=?, total_payout=?, "
            "total_winnings=?, total_losses=?, biggest_win=?, biggest_loss=?, "
            "win_streak=?, best_streak=?, best_multiplier=?, last_bet=?, last_spin=? "
            "WHERE user_id=?",
            (
                spins + 1, wins + (1 if won else 0),
                total_bet + bet, total_payout + payout,
                total_winnings + (net if net > 0 else 0),
                total_losses + (-net if net < 0 else 0),
                max(biggest_win, net if net > 0 else 0),
                max(biggest_loss, -net if net < 0 else 0),
                streak, max(best_streak, streak), max(best_mult, eff_mult),
                bet, now, uid,
            ),
        )

        # مێژوو
        db.execute(
            "INSERT INTO slot_history (user_id, bet, symbols, multiplier, payout, net, ts, jackpot) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (uid, bet, ",".join(outcome["keys"]), eff_mult, payout, net, now, 1 if jackpot_hit else 0),
        )
        db.commit()
    except BaseException:
        db.rollback()
        raise
    return {
        "payout": payout, "net": net, "balance": new_balance,
        "mult": eff_mult, "jackpot": jackpot_hit, "pool": pool,
    }

# ═══════════════════════════════════════
# بەشی ٥: خوێندنەوەی داتا (ئامار، مێژوو، لیستی پێشەنگان)
# ═══════════════════════════════════════

def fetch_stats(user_id):
    return db.execute(
        "SELECT spins, wins, total_bet, total_payout, total_winnings, total_losses, "
        "biggest_win, biggest_loss, win_streak, best_streak, best_multiplier, last_spin "
        "FROM slot_stats WHERE user_id = ?", (user_id,)
    ).fetchone()

def count_history(user_id):
    return db.execute("SELECT COUNT(*) FROM slot_history WHERE user_id = ?", (user_id,)).fetchone()[0]

def fetch_history_page(user_id, offset, limit):
    return db.execute(
        "SELECT id, bet, symbols, multiplier, payout, net, ts, jackpot FROM slot_history "
        "WHERE user_id = ? ORDER BY id DESC LIMIT ? OFFSET ?", (user_id, limit, offset)
    ).fetchall()

# هەر پۆلێک: (ئیمۆجی، ناو، SQL، جۆری ژمارە)
LB_CATEGORIES = {
    "richest": ("👑", "Richest Slots Players",
                "SELECT s.user_id, u.coins FROM slot_stats s JOIN users u ON u.user_id = s.user_id "
                "ORDER BY u.coins DESC LIMIT 10", "cash"),
    "total_wins": ("💰", "Biggest Total Wins",
                   "SELECT user_id, total_winnings FROM slot_stats WHERE total_winnings > 0 "
                   "ORDER BY total_winnings DESC LIMIT 10", "cash"),
    "biggest_win": ("🏆", "Biggest Single Win",
                    "SELECT user_id, biggest_win FROM slot_stats WHERE biggest_win > 0 "
                    "ORDER BY biggest_win DESC LIMIT 10", "cash"),
    "spins": ("🎰", "Most Spins",
              "SELECT user_id, spins FROM slot_stats ORDER BY spins DESC LIMIT 10", "num"),
    "net": ("📈", "Highest Net Profit",
            "SELECT user_id, total_payout - total_bet AS net FROM slot_stats "
            "WHERE total_payout - total_bet > 0 ORDER BY net DESC LIMIT 10", "cash"),
}

def cells_text(keys_text):
    return " ".join(KEY_EMOJI.get(k, "❔") for k in keys_text.split(","))

def signed(n):
    return f"{'+' if n >= 0 else '-'}{CASH_EMOJI} {abs(n):,}"

# ═══════════════════════════════════════
# بەشی ٦: شێوەی نامەکان
# ═══════════════════════════════════════

# شێوەی نامەی سلۆت: ڕێک وەک OwO (تێکستی ئاسایی)
# line3 و line4: نووسینی ئەنجام (لە کاتی سووڕانەوە بەتاڵە)
def slots_text(cells, name, bet, line3="", line4=""):
    row = " ".join(cells)
    return (
        "**`___SLOTS___`**\n"
        f"` ` {row} ` ` {name} {TXT_BET} {CASH_EMOJI} {bet:,}\n"
        f"`|          |` {line3}\n"
        f"`|          |` {line4}"
    ).rstrip()

# نووسینی ئەنجامی کۆتایی (هێڵی سێیەم و چوارەم)
def result_lines(outcome, res):
    if outcome["jackpot"]:
        line3 = f"and won the **JACKPOT** {CASH_EMOJI} {res['payout']:,}!! 🎰"
    elif res["payout"] > 0:
        line3 = f"{TXT_WON} {CASH_EMOJI} {res['payout']:,}"
    else:
        line3 = TXT_NOTHING
    if not SHOW_DETAILS:
        return line3, ""
    parts = []
    if res["payout"] > 0:
        parts.append(f"**x{res['mult']}**")
    parts.append(f"net {signed(res['net'])}")
    parts.append(f"💳 {CASH_EMOJI} {res['balance']:,}")
    return line3, " • ".join(parts)

def stats_embed(ctx, member, s):
    (spins, wins, total_bet, total_payout, total_winnings, total_losses,
     biggest_win, biggest_loss, streak, best_streak, best_mult, last_spin) = s
    net = total_payout - total_bet
    rate = (wins / spins * 100) if spins else 0
    embed = make_embed(f"🎰 Slots Statistics — {member.display_name}", color=PURPLE, ctx=ctx)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="🎲 یاری", value=f"`{spins:,}`")
    embed.add_field(name="📊 ڕێژەی بردنەوە", value=f"`{rate:.1f}%`")
    embed.add_field(name="🔥 بردنەوەی بەردەوام", value=f"`{streak}` (باشترین `{best_streak}`)")
    embed.add_field(name="💵 کۆی شەرتەکان", value=f"{CASH_EMOJI} `{total_bet:,}`")
    embed.add_field(name="💰 کۆی پارەی وەرگیراو", value=f"{CASH_EMOJI} `{total_payout:,}`")
    embed.add_field(name="📈 قازانجی پاک", value=signed(net))
    embed.add_field(name="🏆 کۆی بردنەوەکان", value=f"{CASH_EMOJI} `{total_winnings:,}`")
    embed.add_field(name="💔 کۆی دۆڕانەکان", value=f"{CASH_EMOJI} `{total_losses:,}`")
    embed.add_field(name="✨ گەورەترین چەند ئەوەند", value=f"`x{best_mult}`")
    embed.add_field(name="🥇 گەورەترین بردنەوە", value=f"{CASH_EMOJI} `{biggest_win:,}`")
    embed.add_field(name="🥀 گەورەترین دۆڕان", value=f"{CASH_EMOJI} `{biggest_loss:,}`")
    embed.add_field(name="🕒 دوایین یاری", value=f"<t:{int(last_spin)}:R>")
    return embed

def history_embed(ctx, page, pages, rows, total):
    embed = make_embed(f"📜 Slots History — {ctx.author.display_name}", color=PURPLE, ctx=ctx)
    if not rows:
        embed.description = "هێشتا هیچ یارییەکت نەکردووە."
        return embed
    lines = []
    for sid, bet, symbols, mult, payout, net, ts, jackpot in rows:
        tag = " 🎰 **JACKPOT**" if jackpot else ""
        lines.append(
            f"`#{sid}` {cells_text(symbols)}{tag}\n"
            f"╰ شەرت {CASH_EMOJI} `{bet:,}` → {CASH_EMOJI} `{payout:,}` (**x{mult}**) • {signed(net)} • <t:{int(ts)}:R>"
        )
    embed.description = "\n\n".join(lines)
    embed.set_footer(text=f"لاپەڕە {page + 1}/{pages} • {total:,} یاری")
    return embed

def help_embed(ctx):
    cfg = {k: get_cfg(k) for k in DEFAULT_CONFIG}
    embed = make_embed("🎰 Slots — یارمەتی", color=PURPLE, ctx=ctx)
    table = "\n".join(
        f"{emoji} {emoji} {emoji} ─ **x{mult}** ─ `{percent:g}%`" for _, emoji, mult, percent in SYMBOLS
    )
    table += f"\n❌ دۆڕان ─ `{LOSS_PERCENT:g}%`"
    embed.add_field(name="💎 خشتەی بردنەوە (٣ هێمای وەک یەک)", value=table, inline=False)
    embed.add_field(
        name="🕹️ فەرمانەکان",
        value=(
            f"`{PREFIX}slots <بڕ>` ─ یاری بکە (`{PREFIX}s` یان `{PREFIX}slot`)\n"
            f"`{PREFIX}slots all` ─ هەموو دراوەکانت\n"
            f"`{PREFIX}slots half` ─ نیوەی دراوەکانت\n"
            f"`{PREFIX}slots double` ─ دوو ئەوەندەی شەرتی پێشووت\n"
            f"`{PREFIX}slots stats` ─ ئاماری خۆت\n"
            f"`{PREFIX}slots history` ─ مێژووی یارییەکانت\n"
            f"`{PREFIX}slots leaderboard` ─ لیستی پێشەنگان"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚙️ سنوورەکان",
        value=f"شەرت: {CASH_EMOJI} `{cfg['min_bet']:,}` تا `{cfg['max_bet']:,}` • چاوەڕێکردن: `{cfg['cooldown']}s`",
        inline=False,
    )
    state = "چالاکە" if cfg["jackpot_enabled"] else "ناچالاکە"
    embed.add_field(
        name="🎰 جاکپۆتی پەرەسەندوو",
        value=(
            f"ئێستا: {CASH_EMOJI} **{get_jackpot():,}** ({state})\n"
            f"هەر شەرتێک `{cfg['jackpot_percent']:g}%` دەچێتە ناو جاکپۆت. "
            f"بۆ بردنەوەی پێویستە شەرتت لانیکەم `{JACKPOT_MIN_BET:,}` بێت"
        ),
        inline=False,
    )
    embed.set_footer(text=f"گەڕانەوەی چاوەڕوانکراو (RTP): {BASE_RTP * 100:.1f}% • یاری ئەکەیت بە دراوی یاری، نەک پارەی ڕاستەقینە")
    return embed

def config_embed(ctx):
    embed = make_embed("⚙️ Slots — ڕێکخستنەکان", color=GOLD, ctx=ctx)
    lines = [f"`{k}` = **{get_cfg(k):g}**  (بنەڕەت: {v:g})" for k, v in DEFAULT_CONFIG.items()]
    embed.add_field(name="بەهاکان", value="\n".join(lines), inline=False)
    embed.add_field(
        name="گۆڕین",
        value=f"`{PREFIX}slots config <ناو> <بەها>`\nنموونە: `{PREFIX}slots config max_bet 100000`",
        inline=False,
    )
    embed.set_footer(text=f"RTP: {BASE_RTP * 100:.2f}% • ئەگەری دۆڕان: {LOSS_PERCENT:g}%")
    return embed

# ═══════════════════════════════════════
# بەشی ٧: دوگمە و لیستەکان
# ═══════════════════════════════════════

# ناوی کەسێک لە ئایدییەکەیەوە دەدۆزێتەوە
async def resolve_name(bot, guild, user_id):
    member = guild.get_member(user_id) if guild else None
    if member:
        return member.display_name
    user = bot.get_user(user_id)
    if user is None:
        try:
            user = await bot.fetch_user(user_id)
        except discord.HTTPException:
            return f"User {user_id}"
    return user.display_name

# دوگمەکانی لەژێر سلۆت (ئەگەر SPIN_BUTTONS چالاک بێت)
class SpinView(discord.ui.View):
    def __init__(self, cog, author, bet):
        super().__init__(timeout=60)
        self.cog, self.author, self.bet = cog, author, bet
        self.message = None
        self.used = False

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ ئەم دوگمانە بۆ کەسێکی ترە.", ephemeral=True)
            return False
        if self.used:  # ڕێگری لە دووبارە کلیککردن
            await interaction.response.send_message("⏳ پێشتر کلیکت کردووە.", ephemeral=True)
            return False
        return True

    async def go(self, interaction, bet_text):
        self.used = True
        await interaction.response.defer()
        self.stop()
        try:
            await interaction.message.edit(view=None)
        except discord.HTTPException:
            pass
        await self.cog.start_spin(interaction.channel, interaction.user, bet_text)

    @discord.ui.button(label="Again", emoji="🔁", style=discord.ButtonStyle.primary)
    async def again(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.go(interaction, str(self.bet))

    @discord.ui.button(label="x2", emoji="⏫", style=discord.ButtonStyle.success)
    async def double(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.go(interaction, str(self.bet * 2))

    @discord.ui.button(label="½", emoji="➗", style=discord.ButtonStyle.secondary)
    async def half(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.go(interaction, str(max(self.bet // 2, 1)))

    async def on_timeout(self):
        if self.message and not self.used:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass

# لاپەڕەکانی history
class HistoryView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.page = 0
        self.message = None

    def build(self):
        total = count_history(self.ctx.author.id)
        pages = max(1, math.ceil(total / HISTORY_PER_PAGE))
        self.page = min(self.page, pages - 1)
        rows = fetch_history_page(self.ctx.author.id, self.page * HISTORY_PER_PAGE, HISTORY_PER_PAGE)
        return history_embed(self.ctx, self.page, pages, rows, total)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ ئەم مینیوەیە بۆ کەسێکی ترە.", ephemeral=True)
            return False
        return True

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        await interaction.response.edit_message(embed=self.build(), view=self)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await interaction.response.edit_message(embed=self.build(), view=self)

    @discord.ui.button(emoji="✖️", style=discord.ButtonStyle.danger)
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

# لیستی پێشەنگان لەگەڵ لیستی هەڵبژاردنی پۆل
class LeaderboardView(discord.ui.View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=120)
        self.cog, self.ctx = cog, ctx
        self.message = None

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ ئەم مینیوەیە بۆ کەسێکی ترە.", ephemeral=True)
            return False
        return True

    @discord.ui.select(
        placeholder="📂 پۆلێک هەڵبژێرە...",
        options=[
            discord.SelectOption(label=title, value=key, emoji=emoji)
            for key, (emoji, title, _, _) in LB_CATEGORIES.items()
        ],
    )
    async def pick(self, interaction: discord.Interaction, select: discord.ui.Select):
        embed = await self.cog.leaderboard_embed(self.ctx, select.values[0])
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

# ═══════════════════════════════════════
# بەشی ٨: فەرمانەکان
# ═══════════════════════════════════════

class SlotsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.busy = set()     # ئەوانەی ئێستا سلۆت دەکەن (ڕێگری لە دوو سلۆتی هاوکات)
        self.last_use = {}    # دوایین جاری هەر کەس سلۆتی کرد

    # ─── سلۆت: بەشی سەرەکی ───
    async def start_spin(self, channel, author, bet_text):
        uid = author.id
        name = discord.utils.escape_markdown(author.display_name)

        # ڕێگری لە دوو سلۆتی هاوکات (دەبێت پێش هەر await ێکی تر بێت)
        if uid in self.busy:
            await channel.send(f"⏳ | **{name}**، سلۆتەکەت هێشتا تەواو نەبووە!", delete_after=4)
            return
        self.busy.add(uid)
        try:
            min_bet, max_bet = get_cfg("min_bet"), get_cfg("max_bet")
            coins, _, _ = get_user(uid)

            # ١) شەرتەکە بپشکنە
            amount, err = parse_bet(bet_text, coins, min_bet, max_bet, get_last_bet(uid))
            if err:
                await channel.send(bet_error_text(err, name, min_bet, max_bet, coins, "slots 100"))
                return

            # ٢) چاوەڕێکردن (cooldown). تەنها لە یاری ڕاستەقینەدا حساب دەکرێت
            # دوایین سلۆت لە داتابەیسیش هەیە، بۆیە دوای ڕیستارتی بوت cooldown ناسڕێتەوە
            last = max(self.last_use.get(uid, 0), get_last_spin(uid))
            wait = get_cfg("cooldown") - (time.time() - last)
            if wait > 0:
                await channel.send(f"⏱️ | **{name}**، **{wait:.1f}** چرکەی تر چاوەڕێ بکە!", delete_after=4)
                return
            self.last_use[uid] = time.time()

            # ٣) ئەنجام دیاری بکە و مامەڵەکە تۆمار بکە (پێش ئانیمەیشن)
            jackpot_on = bool(get_cfg("jackpot_enabled"))
            outcome = roll_outcome(jackpot_on and amount >= JACKPOT_MIN_BET)
            contribution = int(amount * get_cfg("jackpot_percent") / 100) if jackpot_on else 0
            try:
                res = commit_spin(uid, amount, outcome, contribution)
            except SpinError:
                await channel.send(bet_error_text("insufficient", name, min_bet, max_bet, coins, "slots 100"))
                return
            except sqlite3.Error as error:
                print(f"هەڵەی داتابەیس لە سلۆت: {error}")
                await channel.send(f"❌ | **{name}**، هەڵەیەکی داتابەیس ڕوویدا. دراوەکانت نەگۆڕدران.")
                return
            if res["jackpot"]:
                print(f"🎰 JACKPOT: user={uid} bet={amount} payout={res['payout']}")

            # ٤) ئانیمەیشن و ئەنجام
            await self.animate(channel, author, name, amount, outcome, res)
        finally:
            self.busy.discard(uid)

    # ئانیمەیشن: وەک OwO. هەر سێ دەسووڕێن، چەپ دەوەستێت، پاشان ناوەڕاست و ڕاست پێکەوە،
    # و لە کۆتاییدا نووسینی ئەنجام. هیچ نیشانەیەک نییە کە پێشوەخت بردنەوە ئاشکرا بکات
    async def animate(self, channel, author, name, amount, outcome, res):
        left, mid, right = [KEY_EMOJI[k] for k in outcome["keys"]]
        spin = SPIN_EMOJI
        special = outcome["jackpot"] or outcome["mult"] == 10
        try:
            msg = await channel.send(slots_text([spin, spin, spin], name, amount))
            await asyncio.sleep(SPIN_STEP * 1.2)
            await msg.edit(content=slots_text([left, spin, spin], name, amount))
            await asyncio.sleep(SPIN_STEP)
            await msg.edit(content=slots_text([left, mid, right], name, amount))
            await asyncio.sleep(SPIN_STEP)
            line3, line4 = result_lines(outcome, res)
            view = None
            if SPIN_BUTTONS:
                view = SpinView(self, author, amount)
            await msg.edit(content=slots_text([left, mid, right], name, amount, line3, line4), view=view)
            if view:
                view.message = msg
        except discord.HTTPException:
            pass  # ئەگەر نامەکە سڕایەوە، کێشە نییە (دراوەکان پێشتر هەژمار کراون)

        # بردنەوەی تایبەت: کارتی جیاواز
        if special:
            await self.celebrate(channel, author, amount, outcome, res)

    async def celebrate(self, channel, author, amount, outcome, res):
        shim = types.SimpleNamespace(author=author)
        try:
            if outcome["jackpot"]:
                embed = make_embed("🎰✨ PROGRESSIVE JACKPOT ✨🎰", color=GOLD, ctx=shim)
                embed.description = (
                    f"👑 {author.mention} جاکپۆتی بەرد!!\n\n"
                    f"{JACKPOT_EMOJI} {JACKPOT_EMOJI} {JACKPOT_EMOJI}\n"
                    f"💰 کۆی بردنەوە: {CASH_EMOJI} **{res['payout']:,}**\n"
                    f"📈 قازانج: **{signed(res['net'])}**"
                )
            else:
                embed = make_embed(f"{E_DIAMOND} MAX WIN x10! {E_DIAMOND}", color=PURPLE, ctx=shim)
                embed.description = (
                    f"✨ {author.mention} سێ OwO ی هێنا!\n\n"
                    f"شەرت: {CASH_EMOJI} `{amount:,}` → {CASH_EMOJI} **{res['payout']:,}** (**x10**)\n"
                    f"📈 قازانج: **{signed(res['net'])}**"
                )
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    # ─── لیستی پێشەنگان ───
    async def leaderboard_embed(self, ctx, key):
        emoji, title, sql, kind = LB_CATEGORIES[key]
        rows = db.execute(sql).fetchall()
        embed = make_embed(f"{emoji} {title}", color=GOLD, ctx=ctx)
        if not rows:
            embed.description = "هێشتا کەس لەم لیستەدا نییە."
            return embed
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (uid, value) in enumerate(rows):
            medal = medals[i] if i < 3 else f"`#{i + 1}`"
            shown = f"{CASH_EMOJI} {value:,}" if kind == "cash" else f"{value:,}"
            nm = discord.utils.escape_markdown(await resolve_name(self.bot, ctx.guild, uid))
            lines.append(f"{medal} **{nm}** ─ {shown}")
        embed.description = "\n".join(lines)
        return embed

    # !slots <بڕ>  (یان all / half / double)
    @commands.group(name="slots", aliases=["slot", "sl", "s", "سلۆت"], invoke_without_command=True)
    async def slots(self, ctx, bet: str = "1"):
        await self.start_spin(ctx.channel, ctx.author, bet)

    # !slots stats [@کەس]
    @slots.command(name="stats", aliases=["stat", "st"])
    async def slots_stats(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        s = fetch_stats(member.id)
        if s is None:
            await ctx.send(f"📊 | **{discord.utils.escape_markdown(member.display_name)}** هێشتا سلۆتی یاری نەکردووە.")
            return
        await ctx.send(embed=stats_embed(ctx, member, s))

    # !slots history
    @slots.command(name="history", aliases=["log"])
    async def slots_history(self, ctx):
        view = HistoryView(ctx)
        view.message = await ctx.send(embed=view.build(), view=view)

    # !slots leaderboard
    @slots.command(name="leaderboard", aliases=["lb", "top"])
    async def slots_leaderboard(self, ctx):
        view = LeaderboardView(self, ctx)
        view.message = await ctx.send(embed=await self.leaderboard_embed(ctx, "richest"), view=view)

    # !slots help
    @slots.command(name="help", aliases=["info"])
    async def slots_help(self, ctx):
        await ctx.send(embed=help_embed(ctx))

    # !slots config [ناو] [بەها]  (تەنها بۆ ئەدمین)
    @slots.command(name="config", aliases=["settings"])
    @commands.has_permissions(manage_guild=True)
    async def slots_config(self, ctx, key: str = None, value: str = None):
        if key is None:
            await ctx.send(embed=config_embed(ctx))
            return
        key = key.lower()
        if key not in DEFAULT_CONFIG or value is None:
            await ctx.send(f"❌ بەکارهێنان: `{PREFIX}slots config <ناو> <بەها>`\nناوەکان: " +
                           ", ".join(f"`{k}`" for k in DEFAULT_CONFIG))
            return
        try:
            number = float(value)
        except ValueError:
            await ctx.send("❌ بەهاکە دەبێت ژمارە بێت.")
            return
        low, high = CONFIG_LIMITS[key]
        if not math.isfinite(number) or not (low <= number <= high):
            await ctx.send(f"❌ `{key}` دەبێت لە نێوان `{low:g}` و `{high:g}` بێت.")
            return
        if isinstance(DEFAULT_CONFIG[key], int):
            number = int(number)
        # کەمترین شەرت نابێت لە زۆرترین زیاتر بێت
        if key == "min_bet" and number > get_cfg("max_bet"):
            await ctx.send("❌ کەمترین شەرت نابێت لە زۆرترین شەرت زیاتر بێت.")
            return
        if key == "max_bet" and number < get_cfg("min_bet"):
            await ctx.send("❌ زۆرترین شەرت نابێت لە کەمترین شەرت کەمتر بێت.")
            return
        set_cfg(key, number)
        await ctx.send(embed=config_embed(ctx))

async def setup(bot):
    await bot.add_cog(SlotsCog(bot))
