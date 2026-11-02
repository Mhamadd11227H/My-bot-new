import os
import sqlite3
import time

# ═══════════════════════════════════════
# داتابەیسی ئابووری (zero coin ی هەموو کەسێک)
# هەموو یارییەکان و تایبەتمەندییەکانی داهاتوو ئەم یەک داتابەیسە بەکار دەهێنن.
# فەرمانە گشتییەکان: get_user, get_balance, add_coins, spend_coins
# ═══════════════════════════════════════

START_BALANCE = 500  # دراوی یەکەم جار کە کەسێک دەست پێ دەکات

# فایلی economy.db لەناو فۆڵدەری سەرەکی بوتەکە دروست دەبێت
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "economy.db")
db = sqlite3.connect(DB_PATH)
db.execute(
    "CREATE TABLE IF NOT EXISTS users ("
    "user_id INTEGER PRIMARY KEY, "
    "coins INTEGER NOT NULL DEFAULT 0, "
    "last_daily REAL NOT NULL DEFAULT 0, "
    "streak INTEGER NOT NULL DEFAULT 0)"
)
db.execute(
    "CREATE TABLE IF NOT EXISTS transfer_log ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "from_id INTEGER NOT NULL, to_id INTEGER NOT NULL, "
    "amount INTEGER NOT NULL, ts REAL NOT NULL)"
)
db.commit()

# زانیاری کەسێک وەردەگرێت (ئەگەر نوێ بێت، دروستی دەکات)
def get_user(user_id):
    row = db.execute(
        "SELECT coins, last_daily, streak FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row is None:
        db.execute("INSERT INTO users (user_id, coins) VALUES (?, ?)", (user_id, START_BALANCE))
        db.commit()
        return START_BALANCE, 0.0, 0
    return row

# دراو زیاد یان کەم دەکات (بۆ کەمکردن ژمارەی سالب بنووسە)
def add_coins(user_id, amount):
    get_user(user_id)
    db.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
    db.commit()

# دراو لە کەسێکەوە دەنێرێت بۆ کەسێکی تر. یەک مامەڵەی ئەتۆمییە:
# یان هەردووکیان دەگۆڕێن، یان هیچیان. دراو نە دروست دەبێت نە دەفەوتێت
# دەگەڕێنێتەوە True ئەگەر سەرکەوتوو بوو، False ئەگەر دراوی پێویست نەبوو
def transfer_coins(from_id, to_id, amount):
    if amount <= 0 or from_id == to_id:
        return False
    get_user(from_id)
    get_user(to_id)
    if db.in_transaction:
        db.commit()
    db.execute("BEGIN IMMEDIATE")
    try:
        cur = db.execute(
            "UPDATE users SET coins = coins - ? WHERE user_id = ? AND coins >= ?",
            (amount, from_id, amount),
        )
        if cur.rowcount != 1:
            db.rollback()
            return False
        db.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, to_id))
        db.execute(
            "INSERT INTO transfer_log (from_id, to_id, amount, ts) VALUES (?, ?, ?, ?)",
            (from_id, to_id, amount, time.time()),
        )
        db.commit()
    except BaseException:
        db.rollback()
        raise
    return True

# باڵانسی کەسێک دەگەڕێنێتەوە (ئەگەر نوێ بێت، دروستی دەکات)
def get_balance(user_id):
    return get_user(user_id)[0]

# دراو دەکێشێتەوە (بۆ کڕین، یاری، خزمەتگوزاری...). ئەگەر دراوی پێویست نەبوو، هیچ ناکات
# و False دەگەڕێنێتەوە. ئەمە یەک مامەڵەی ئەتۆمییە، بۆیە باڵانس هەرگیز سالب نابێت
def spend_coins(user_id, amount):
    if amount <= 0:
        return False
    get_user(user_id)
    cur = db.execute(
        "UPDATE users SET coins = coins - ? WHERE user_id = ? AND coins >= ?",
        (amount, user_id, amount),
    )
    db.commit()
    return cur.rowcount == 1

# بڕی شەرت دەخوێنێتەوە و دەیپشکنێت
# دەگەڕێنێتەوە (بڕ, هەڵە). ئەگەر هەڵە نەبوو، هەڵە = None
# هەڵەکان: invalid, no_cash, too_low, too_high, insufficient, no_last
def parse_bet(text, balance, min_bet, max_bet, last_bet=0):
    text = text.strip().lower().replace(",", "")
    if text in ("all", "max", "هەموو"):
        amount = min(balance, max_bet)       # هەموو دراوەکانت (تا زۆرترین شەرت)
    elif text in ("half", "نیوە"):
        amount = min(balance // 2, max_bet)  # نیوەی دراوەکانت
    elif text in ("double", "x2"):
        if last_bet <= 0:
            return None, "no_last"
        amount = last_bet * 2                # دوو ئەوەندەی شەرتی پێشووت
    else:
        try:
            amount = int(text)
        except ValueError:
            return None, "invalid"

    if balance <= 0:
        return None, "no_cash"
    if amount < min_bet:                     # ئەمە سالب و سفریش دەگرێتەوە
        return None, "too_low"
    if amount > max_bet:
        return None, "too_high"
    if amount > balance:
        return None, "insufficient"
    return amount, None
  
