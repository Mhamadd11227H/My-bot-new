"""
ZERO HUNT — لۆجیکی سەرەکی (بێ discord). هەموو کارە گرنگەکان لێرەن.
ئەم فایلە هەمان داتابەیسی database.py بەکاردێنێت (هەمان `db` و هەمان users.coins)،
بۆیە دراو هەرگیز دووبار نابێت و هەموو مامەڵەکان ئەتۆمین (BEGIN IMMEDIATE).
هیچ await ێک لەناو مامەڵەکاندا نییە، بۆیە race condition نابێت.
"""
import secrets
import time

from database import db, get_user
from . import hunt_data as D

rng = secrets.SystemRandom()  # ڕێکەوتی پارێزراو (cryptographically secure)


# ═══════════════════════════════════════
# داتابەیس: خشتەکان
# ═══════════════════════════════════════
db.executescript("""
CREATE TABLE IF NOT EXISTS animals (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, emoji TEXT NOT NULL, rarity TEXT NOT NULL,
    category TEXT NOT NULL, image TEXT, sell INTEGER NOT NULL, essence INTEGER NOT NULL,
    xp INTEGER NOT NULL, zoo INTEGER NOT NULL, description TEXT, event TEXT,
    pool TEXT NOT NULL, weight REAL NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS player_animals (
    user_id INTEGER NOT NULL, animal_id TEXT NOT NULL,
    qty INTEGER NOT NULL DEFAULT 0 CHECK (qty >= 0),
    total_caught INTEGER NOT NULL DEFAULT 0,
    locked INTEGER NOT NULL DEFAULT 0,
    xp INTEGER NOT NULL DEFAULT 0, level INTEGER NOT NULL DEFAULT 1,
    nickname TEXT, first_ts REAL NOT NULL DEFAULT 0, last_ts REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, animal_id)
);
CREATE INDEX IF NOT EXISTS idx_pa_user_qty ON player_animals (user_id, qty);
CREATE INDEX IF NOT EXISTS idx_pa_animal ON player_animals (animal_id);
CREATE TABLE IF NOT EXISTS player_zoo (
    user_id INTEGER NOT NULL, slot INTEGER NOT NULL, animal_id TEXT NOT NULL,
    PRIMARY KEY (user_id, slot), UNIQUE (user_id, animal_id)
);
CREATE TABLE IF NOT EXISTS hunt_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, ts REAL NOT NULL,
    animals TEXT NOT NULL, cost INTEGER NOT NULL, team_xp INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_hh_user ON hunt_history (user_id, ts);
CREATE TABLE IF NOT EXISTS hunt_stats (
    user_id INTEGER PRIMARY KEY,
    total_hunts INTEGER NOT NULL DEFAULT 0, total_animals INTEGER NOT NULL DEFAULT 0,
    z_spent INTEGER NOT NULL DEFAULT 0, z_earned_sell INTEGER NOT NULL DEFAULT 0,
    essence_earned INTEGER NOT NULL DEFAULT 0, biggest_session INTEGER NOT NULL DEFAULT 0,
    lootboxes INTEGER NOT NULL DEFAULT 0, gems_found INTEGER NOT NULL DEFAULT 0,
    hunt_time REAL NOT NULL DEFAULT 0, hunts_since_box INTEGER NOT NULL DEFAULT 0,
    boxes_today INTEGER NOT NULL DEFAULT 0, box_day TEXT NOT NULL DEFAULT '',
    checklist_day TEXT NOT NULL DEFAULT '', last_hunt REAL NOT NULL DEFAULT 0,
    last_daily_box REAL NOT NULL DEFAULT 0, highest_rank INTEGER NOT NULL DEFAULT -1
);
CREATE TABLE IF NOT EXISTS hunting_gems (
    tier TEXT PRIMARY KEY, name TEXT NOT NULL, emoji TEXT NOT NULL,
    animals INTEGER NOT NULL, durability INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS player_gems (
    gem_uid INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, tier TEXT NOT NULL,
    durability INTEGER NOT NULL, active INTEGER NOT NULL DEFAULT 0, ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pg_user ON player_gems (user_id, active);
CREATE TABLE IF NOT EXISTS active_buffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, kind TEXT NOT NULL,
    strength REAL NOT NULL, expires REAL NOT NULL, source TEXT,
    UNIQUE (user_id, kind)
);
CREATE TABLE IF NOT EXISTS player_items (
    user_id INTEGER NOT NULL, item TEXT NOT NULL,
    qty INTEGER NOT NULL DEFAULT 0 CHECK (qty >= 0), PRIMARY KEY (user_id, item)
);
CREATE TABLE IF NOT EXISTS player_essence (
    user_id INTEGER PRIMARY KEY, essence INTEGER NOT NULL DEFAULT 0 CHECK (essence >= 0)
);
CREATE INDEX IF NOT EXISTS idx_pe_ess ON player_essence (essence);
CREATE TABLE IF NOT EXISTS huntbot (
    user_id INTEGER PRIMARY KEY, start_ts REAL NOT NULL DEFAULT 0, end_ts REAL NOT NULL DEFAULT 0,
    hours REAL NOT NULL DEFAULT 0, animals INTEGER NOT NULL DEFAULT 0, essence INTEGER NOT NULL DEFAULT 0,
    xp INTEGER NOT NULL DEFAULT 0, bot_chance REAL NOT NULL DEFAULT 0, cost INTEGER NOT NULL DEFAULT 0,
    collected INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS huntbot_upgrades (
    user_id INTEGER NOT NULL, stat TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, stat)
);
CREATE TABLE IF NOT EXISTS lootboxes (
    user_id INTEGER NOT NULL, tier TEXT NOT NULL,
    qty INTEGER NOT NULL DEFAULT 0 CHECK (qty >= 0), PRIMARY KEY (user_id, tier)
);
CREATE TABLE IF NOT EXISTS lootbox_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, tier TEXT NOT NULL,
    reward TEXT NOT NULL, ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lh_user ON lootbox_history (user_id, ts);
CREATE TABLE IF NOT EXISTS hunting_events (
    key TEXT PRIMARY KEY, start_ts REAL NOT NULL, end_ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS collection_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, ts REAL NOT NULL,
    action TEXT NOT NULL, detail TEXT NOT NULL, amount INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ch_user ON collection_history (user_id, ts);
""")
db.commit()

# ئاژەڵەکان لە فایلی data دەخرێنە ناو داتابەیس (کۆد سەرچاوەی ڕاستییە)
for _a in D.ANIMALS.values():
    db.execute(
        "INSERT OR REPLACE INTO animals (id,name,emoji,rarity,category,image,sell,essence,xp,zoo,description,event,pool,weight) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (_a["id"], _a["name"], _a["emoji"], _a["rarity"], _a["category"], _a["image"], _a["sell"],
         _a["essence"], _a["xp"], _a["zoo"], _a["description"], _a["event"], _a["pool"], _a["weight"]),
    )
# gem ەکان: تەنها ئەگەر نەبن زیاد دەکرێن، بۆ ئەوەی گۆڕانکاری ئەدمین نەسڕدرێتەوە
for _t, _g in D.GEMS.items():
    db.execute("INSERT OR IGNORE INTO hunting_gems (tier,name,emoji,animals,durability) VALUES (?,?,?,?,?)",
               (_t, _g["name"], _g["emoji"], _g["animals"], _g["durability"]))
db.commit()


# ═══════════════════════════════════════
# یارمەتیدەرەکان
# ═══════════════════════════════════════
class Tx:
    """مامەڵەی ئەتۆمی: یان هەموو کارەکان دەکرێن، یان هیچ"""
    def __enter__(self):
        if db.in_transaction:
            db.commit()
        db.execute("BEGIN IMMEDIATE")

    def __exit__(self, et, ev, tb):
        if et:
            db.rollback()
        else:
            db.commit()
        return False


def today_key():
    return time.strftime("%Y-%m-%d", time.gmtime())


def ensure_user(uid):
    get_user(uid)
    db.execute("INSERT OR IGNORE INTO hunt_stats (user_id) VALUES (?)", (uid,))
    db.execute("INSERT OR IGNORE INTO player_essence (user_id) VALUES (?)", (uid,))
    db.execute("INSERT OR IGNORE INTO huntbot (user_id) VALUES (?)", (uid,))
    db.commit()


def _norm(text):
    return "".join(ch for ch in text.lower().strip() if ch.isalnum())


_LOOKUP = {}
for _a in D.ANIMALS.values():
    _LOOKUP[_norm(_a["name"])] = _a["id"]
    _LOOKUP[_norm(_a["id"])] = _a["id"]
    _LOOKUP[_a["emoji"]] = _a["id"]


def find_animal(text):
    """ناو، ئایدی یان ئیمۆجی. ئەگەر دەستپێکی یەک ئاژەڵ بوو، ئەویش دەدۆزێتەوە"""
    if not text:
        return None
    t = text.strip()
    if t in _LOOKUP:
        return D.ANIMALS[_LOOKUP[t]]
    n = _norm(t)
    if not n:
        return None
    if n in _LOOKUP:
        return D.ANIMALS[_LOOKUP[n]]
    hits = {aid for key, aid in _LOOKUP.items() if key.startswith(n) and key.isascii()}
    return D.ANIMALS[hits.pop()] if len(hits) == 1 else None


def search_animals(text):
    n = _norm(text)
    return [a for a in D.ANIMALS.values() if n in _norm(a["name"])]


def find_rarity(text):
    n = _norm(text)
    for key, r in D.RARITIES.items():
        if n in (_norm(key), _norm(r["name"])):
            return key
    return None


# ── ئاست و XP ──
def xp_for_level(level):
    n = level - 1
    return D.XP_BASE * n * (n + 1) * (2 * n + 1) // 6


def level_from_xp(xp):
    lvl = 1
    while lvl < D.MAX_PET_LEVEL and xp >= xp_for_level(lvl + 1):
        lvl += 1
    return lvl


def level_progress(xp, level):
    if level >= D.MAX_PET_LEVEL:
        return 1, 1
    base = xp_for_level(level)
    return xp - base, xp_for_level(level + 1) - base


def bar(cur, total, width=10):
    filled = width if total <= 0 else max(0, min(width, int(width * cur / total)))
    return "█" * filled + "░" * (width - filled)


# ═══════════════════════════════════════
# buff ەکان
# ═══════════════════════════════════════
def get_buffs(uid, now=None):
    """{kind: (strength, expires)} تەنها ئەوانەی نەمردوون"""
    now = now or time.time()
    rows = db.execute("SELECT kind, strength, expires FROM active_buffs WHERE user_id=? AND expires>?",
                      (uid, now)).fetchall()
    return {k: (s, e) for k, s, e in rows}


def _apply_buff(uid, kind, strength, duration, source, now):
    """یاسای stack: بەهێزترین strength دەمێنێتەوە، ماوەکە زیاد دەکرێت (تا MAX_BUFF_SECONDS)"""
    row = db.execute("SELECT strength, expires FROM active_buffs WHERE user_id=? AND kind=?", (uid, kind)).fetchone()
    if row and row[1] > now:
        strength = max(strength, row[0])
        expires = min(row[1] + duration, now + D.MAX_BUFF_SECONDS)
    else:
        expires = now + duration
    db.execute(
        "INSERT INTO active_buffs (user_id,kind,strength,expires,source) VALUES (?,?,?,?,?) "
        "ON CONFLICT(user_id,kind) DO UPDATE SET strength=excluded.strength, expires=excluded.expires, source=excluded.source",
        (uid, kind, strength, expires, source),
    )
    return strength, expires


def active_events(now=None):
    now = now or time.time()
    rows = db.execute("SELECT key, start_ts, end_ts FROM hunting_events WHERE start_ts<=? AND end_ts>?",
                      (now, now)).fetchall()
    return [(k, s, e) for k, s, e in rows if k in D.EVENTS]


# ═══════════════════════════════════════
# ڕۆڵ‌کردنی ئاژەڵ (probability)
# ═══════════════════════════════════════
def rarity_table(luck=0.0):
    """جەدوەلی ppm. luck تەنها ئەگەری non-common زیاد دەکات و common کەم دەکاتەوە، بۆیە کۆ هەمیشە ١٠٠٪یە"""
    base = {r: d["ppm"] for r, d in D.RARITIES.items() if d["pool"] == "main"}
    luck = max(0.0, min(luck, D.MAX_LUCK))
    if luck <= 0:
        return base
    adj = {r: int(w * (1 + luck)) for r, w in base.items() if r != "common"}
    adj["common"] = max(0, D.TOTAL_PPM - sum(adj.values()))
    return adj


def roll_rarity(table):
    total = sum(table.values())
    x = rng.randrange(total)
    acc = 0
    for r, w in table.items():
        acc += w
        if x < acc:
            return r
    return "common"


def roll_animal(table, lure=None, events=None):
    """lure = (category, strength). events = لیستی کلیلی eventە چالاکەکان"""
    for key in events or ():
        ev = D.EVENTS[key]
        ids = D.EVENT_ANIMALS.get(key)
        if ids and ev["animal_chance"] > 0 and rng.random() < ev["animal_chance"]:
            return D.ANIMALS[rng.choice(ids)]
    pool = D.MAIN_BY_RARITY[roll_rarity(table)]
    if lure:
        cat, strength = lure
        weights = [a["weight"] * ((1 + strength) if a["category"] == cat else 1) for a in pool]
        return rng.choices(pool, weights=weights, k=1)[0]
    return rng.choices(pool, weights=[a["weight"] for a in pool], k=1)[0]


def _lure_from(buffs):
    best = None
    for kind, (s, _) in buffs.items():
        if kind.startswith("lure_") and (best is None or s > best[1]):
            best = (kind[5:], s)
    return best


# ═══════════════════════════════════════
# ئاژەڵ زیادکردن، XP ی team
# ═══════════════════════════════════════
def _add_animals(uid, counts, now):
    """counts: {animal_id: n}. دەگەڕێنێتەوە لیستی ئەو ئاژەڵانەی یەکەمجارە دەیانبینێت"""
    new = []
    for aid, n in counts.items():
        prev = db.execute("SELECT total_caught FROM player_animals WHERE user_id=? AND animal_id=?", (uid, aid)).fetchone()
        if prev is None or prev[0] == 0:
            new.append(aid)
        db.execute(
            "INSERT INTO player_animals (user_id,animal_id,qty,total_caught,first_ts,last_ts) VALUES (?,?,?,?,?,?) "
            "ON CONFLICT(user_id,animal_id) DO UPDATE SET qty=qty+excluded.qty, "
            "total_caught=total_caught+excluded.total_caught, last_ts=excluded.last_ts, "
            "first_ts=CASE WHEN first_ts=0 THEN excluded.first_ts ELSE first_ts END",
            (uid, aid, n, n, now, now),
        )
    best = max(D.RARITY_RANK[D.ANIMALS[a]["rarity"]] for a in counts)
    db.execute("UPDATE hunt_stats SET highest_rank=MAX(highest_rank, ?) WHERE user_id=?", (best, uid))
    return new


def _team(uid):
    return [r[0] for r in db.execute("SELECT animal_id FROM player_zoo WHERE user_id=? ORDER BY slot", (uid,))]


def _award_team_xp(uid, xp):
    """XP دەدات بە هەموو team ی ئاژەڵەکان. دەگەڕێنێتەوە [(animal_id, ئاستی نوێ, پاداشت)]"""
    ups = []
    if xp <= 0:
        return ups
    for aid in _team(uid):
        row = db.execute("SELECT xp, level FROM player_animals WHERE user_id=? AND animal_id=? AND qty>0",
                         (uid, aid)).fetchone()
        if row is None:
            continue
        old_lvl = row[1]
        if old_lvl >= D.MAX_PET_LEVEL:
            continue
        new_xp = row[0] + xp
        new_lvl = level_from_xp(new_xp)
        db.execute("UPDATE player_animals SET xp=?, level=? WHERE user_id=? AND animal_id=?",
                   (new_xp, new_lvl, uid, aid))
        if new_lvl > old_lvl:
            reward = 0
            for lv in range(old_lvl + 1, new_lvl + 1):
                reward += lv * D.LEVEL_REWARD_PER_LEVEL
                if lv % D.LEVEL_BOX_EVERY == 0:
                    _grant_box(uid, "rare", 1)
            db.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (reward, uid))
            ups.append((aid, new_lvl, reward))
    return ups


def _xp_multiplier(buffs, events):
    m = 1.0 + (buffs["xp"][0] if "xp" in buffs else 0.0)
    for k in events:
        m += D.EVENTS[k]["xp"]
    return m


# ═══════════════════════════════════════
# lootbox
# ═══════════════════════════════════════
def _grant_box(uid, tier, n=1):
    db.execute("INSERT INTO lootboxes (user_id,tier,qty) VALUES (?,?,?) "
               "ON CONFLICT(user_id,tier) DO UPDATE SET qty=qty+excluded.qty", (uid, tier, n))


def _count_box(uid, tier, now):
    """lootbox ێک دەدات و بە checklist ی ڕۆژانە دەژمێرێت. دەگەڕێنێتەوە (boxes_today, checklist_bonus)"""
    day = today_key()
    st = db.execute("SELECT boxes_today, box_day, checklist_day FROM hunt_stats WHERE user_id=?", (uid,)).fetchone()
    today = (st[0] + 1) if st[1] == day else 1
    _grant_box(uid, tier, 1)
    bonus = 0
    if today >= D.DAILY_BOX_TARGET and st[2] != day:
        bonus = D.CHECKLIST_REWARD
        db.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (bonus, uid))
        db.execute("UPDATE hunt_stats SET checklist_day=? WHERE user_id=?", (day, uid))
    db.execute("UPDATE hunt_stats SET boxes_today=?, box_day=?, lootboxes=lootboxes+1 WHERE user_id=?",
               (today, day, uid))
    return today, bonus


def box_progress(uid):
    st = db.execute("SELECT boxes_today, box_day FROM hunt_stats WHERE user_id=?", (uid,)).fetchone()
    return st[0] if st and st[1] == today_key() else 0


def grant_daily_box(uid, last_daily):
    """دوای !daily: یەک lootbox. last_daily_box ڕێگری دەکات لە دووبارەبوونەوە"""
    ensure_user(uid)
    now = time.time()
    with Tx():
        cur = db.execute("UPDATE hunt_stats SET last_daily_box=? WHERE user_id=? AND last_daily_box<?",
                         (last_daily, uid, last_daily))
        if cur.rowcount != 1:
            return None
        return _count_box(uid, "common", now)


def _weighted(entries):
    return rng.choices(entries, weights=[e["weight"] for e in entries], k=1)[0]


def _pick_weighted_map(m):
    return rng.choices(list(m), weights=list(m.values()), k=1)[0]


def _give_gem(uid, tier, now):
    g = db.execute("SELECT name, emoji, durability FROM hunting_gems WHERE tier=?", (tier,)).fetchone()
    cur = db.execute("INSERT INTO player_gems (user_id,tier,durability,active,ts) VALUES (?,?,?,0,?)",
                     (uid, tier, g[2], now))
    db.execute("UPDATE hunt_stats SET gems_found=gems_found+1 WHERE user_id=?", (uid,))
    return cur.lastrowid, g


def _open_one(uid, tier, now):
    """یەک lootbox دەکاتەوە (دەبێت لەناو Tx بێت). دەگەڕێنێتەوە dict ی پاداشت"""
    cfg = D.BOXES[tier]
    r = _weighted(cfg["rewards"])
    t = r["type"]
    if t == "coins":
        amt = rng.randint(r["min"], r["max"])
        db.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (amt, uid))
        out = dict(type="coins", amount=amt, text=f"💵 **{amt:,}** coins")
    elif t == "essence":
        amt = rng.randint(r["min"], r["max"])
        db.execute("UPDATE player_essence SET essence=essence+? WHERE user_id=?", (amt, uid))
        db.execute("UPDATE hunt_stats SET essence_earned=essence_earned+? WHERE user_id=?", (amt, uid))
        out = dict(type="essence", amount=amt, text=f"💠 **{amt:,}** essence")
    elif t == "gem":
        gtier = _pick_weighted_map(r["tiers"])
        uid_g, g = _give_gem(uid, gtier, now)
        out = dict(type="gem", tier=gtier, gem_uid=uid_g, text=f"{g[1]} **{g[0]}** (ID `{uid_g}`)")
    elif t == "item":
        key = rng.choice(r["keys"])
        db.execute("INSERT INTO player_items (user_id,item,qty) VALUES (?,?,1) "
                   "ON CONFLICT(user_id,item) DO UPDATE SET qty=qty+1", (uid, key))
        it = D.ITEMS[key]
        out = dict(type="item", key=key, text=f"{it['emoji']} **{it['name']}**")
    else:  # animal
        rar = _pick_weighted_map(r["rarities"])
        a = rng.choice(D.MAIN_BY_RARITY[rar])
        _add_animals(uid, {a["id"]: 1}, now)
        out = dict(type="animal", animal=a["id"], text=f"{a['emoji']} **{a['name']}** ({D.RARITIES[rar]['name']})")
    db.execute("INSERT INTO lootbox_history (user_id,tier,reward,ts) VALUES (?,?,?,?)",
               (uid, tier, out["text"], now))
    return out


def open_boxes(uid, tier, count=1):
    """count جار lootbox دەکاتەوە. دەگەڕێنێتەوە لیستی پاداشتەکان یان None ئەگەر box ی پێویست نەبوو"""
    ensure_user(uid)
    now = time.time()
    with Tx():
        cur = db.execute("UPDATE lootboxes SET qty=qty-? WHERE user_id=? AND tier=? AND qty>=?",
                         (count, uid, tier, count))
        if cur.rowcount != 1:
            return None
        return [_open_one(uid, tier, now) for _ in range(count)]


def prune_history(days=14):
    """مێژووی hunt ی کۆن دەسڕێتەوە، بۆ ئەوەی داتابەیس گەورە نەبێت"""
    db.execute("DELETE FROM hunt_history WHERE ts<?", (time.time() - days * 86400,))
    db.commit()


def get_boxes(uid):
    return {t: q for t, q in db.execute("SELECT tier, qty FROM lootboxes WHERE user_id=? AND qty>0", (uid,))}


def box_history(uid, limit=10):
    return db.execute("SELECT tier, reward, ts FROM lootbox_history WHERE user_id=? ORDER BY id DESC LIMIT ?",
                      (uid, limit)).fetchall()


# ═══════════════════════════════════════
# HUNT ی دەستی
# ═══════════════════════════════════════
def hunt_cost(buffs):
    disc = min(0.9, buffs["discount"][0]) if "discount" in buffs else 0.0
    return max(1, round(D.HUNT_COST * (1 - disc)))


def perform_hunt(uid):
    """
    ٩ هەنگاوی hunt لە یەک مامەڵەی ئەتۆمیدا.
    دەگەڕێنێتەوە {"error": "cooldown"/"no_cash", ...} یان {"ok": True, ...}
    """
    ensure_user(uid)
    now = time.time()
    with Tx():
        st = db.execute("SELECT last_hunt, biggest_session, hunts_since_box FROM hunt_stats WHERE user_id=?",
                        (uid,)).fetchone()
        wait = D.HUNT_COOLDOWN - (now - st[0])
        if wait > 0:
            return {"error": "cooldown", "wait": wait}

        buffs = get_buffs(uid, now)
        events = [k for k, _, _ in active_events(now)]
        cost = hunt_cost(buffs)

        # gem ی چالاک
        gem = db.execute(
            "SELECT g.gem_uid, g.tier, g.durability, h.animals, h.name, h.emoji FROM player_gems g "
            "JOIN hunting_gems h ON h.tier=g.tier WHERE g.user_id=? AND g.active=1", (uid,)).fetchone()
        extra = (gem[3] if gem else 0) + (int(buffs["catch"][0]) if "catch" in buffs else 0)
        n = 1 + extra

        # نرخ: ئەتۆمی، هەرگیز سالب نابێت
        cur = db.execute("UPDATE users SET coins=coins-? WHERE user_id=? AND coins>=?", (cost, uid, cost))
        if cur.rowcount != 1:
            bal = db.execute("SELECT coins FROM users WHERE user_id=?", (uid,)).fetchone()[0]
            return {"error": "no_cash", "cost": cost, "balance": bal}

        luck = (buffs["luck"][0] if "luck" in buffs else 0.0) + sum(D.EVENTS[k]["luck"] for k in events)
        table = rarity_table(luck)
        lure = _lure_from(buffs)
        caught = [roll_animal(table, lure, events) for _ in range(n)]
        counts = {}
        for a in caught:
            counts[a["id"]] = counts.get(a["id"], 0) + 1
        new_ids = _add_animals(uid, counts, now)

        # gem durability
        gem_info = None
        if gem:
            left = gem[2] - 1
            if left <= 0:
                db.execute("DELETE FROM player_gems WHERE gem_uid=?", (gem[0],))
            else:
                db.execute("UPDATE player_gems SET durability=? WHERE gem_uid=?", (left, gem[0]))
            gem_info = dict(uid=gem[0], name=gem[4], emoji=gem[5], left=max(left, 0), expired=left <= 0)

        # XP ی team
        base_xp = sum(a["xp"] for a in caught)
        team_xp = int(base_xp * _xp_multiplier(buffs, events))
        level_ups = _award_team_xp(uid, team_xp)

        # lootbox
        since = st[2] + 1
        box = None
        if since >= D.LOOTBOX_EVERY:
            since = 0
            box = _count_box(uid, "common", now)
        db.execute(
            "UPDATE hunt_stats SET total_hunts=total_hunts+1, total_animals=total_animals+?, z_spent=z_spent+?, "
            "biggest_session=MAX(biggest_session,?), hunt_time=hunt_time+?, hunts_since_box=?, last_hunt=? "
            "WHERE user_id=?", (n, cost, n, D.HUNT_COOLDOWN, since, now, uid))
        db.execute("INSERT INTO hunt_history (user_id,ts,animals,cost,team_xp) VALUES (?,?,?,?,?)",
                   (uid, now, ",".join(a["id"] for a in caught), cost, team_xp))
        return dict(ok=True, animals=caught, counts=counts, new=new_ids, cost=cost, team_xp=team_xp,
                    level_ups=level_ups, gem=gem_info, box=box, since=since, events=events,
                    boxes_today=box_progress(uid), buffs=buffs)


# ═══════════════════════════════════════
# gem ، ئایتم
# ═══════════════════════════════════════
def get_gems(uid):
    return db.execute(
        "SELECT g.gem_uid, g.tier, g.durability, g.active, h.name, h.emoji, h.animals, h.durability "
        "FROM player_gems g JOIN hunting_gems h ON h.tier=g.tier WHERE g.user_id=? ORDER BY g.active DESC, g.gem_uid",
        (uid,)).fetchall()


def gem_info(uid, gem_uid):
    return db.execute(
        "SELECT g.gem_uid, g.tier, g.durability, g.active, h.name, h.emoji, h.animals, h.durability "
        "FROM player_gems g JOIN hunting_gems h ON h.tier=g.tier WHERE g.user_id=? AND g.gem_uid=?",
        (uid, gem_uid)).fetchone()


def toggle_gem(uid, gem_uid):
    """gem چالاک دەکات (تەنها یەک)، یان ئەگەر خۆی چالاک بوو، ناچالاکی دەکات"""
    ensure_user(uid)
    with Tx():
        g = gem_info(uid, gem_uid)
        if g is None:
            return None
        if g[3]:
            db.execute("UPDATE player_gems SET active=0 WHERE gem_uid=?", (gem_uid,))
            return ("off", g)
        db.execute("UPDATE player_gems SET active=0 WHERE user_id=?", (uid,))
        db.execute("UPDATE player_gems SET active=1 WHERE gem_uid=? AND user_id=?", (gem_uid, uid))
        return ("on", g)


def use_item(uid, key):
    ensure_user(uid)
    it = D.ITEMS[key]
    now = time.time()
    with Tx():
        cur = db.execute("UPDATE player_items SET qty=qty-1 WHERE user_id=? AND item=? AND qty>=1", (uid, key))
        if cur.rowcount != 1:
            return None
        s, e = _apply_buff(uid, it["kind"], it["strength"], it["duration"], key, now)
        return it, s, e


def get_items(uid):
    return {k: q for k, q in db.execute("SELECT item, qty FROM player_items WHERE user_id=? AND qty>0", (uid,))
            if k in D.ITEMS}


def find_item(text):
    n = _norm(text)
    for key, it in D.ITEMS.items():
        if n in (_norm(key), _norm(it["name"])):
            return key
    return None


def buff_label(kind):
    if kind.startswith("lure_"):
        return f"🪤 {kind[5:].title()} Lure"
    return {"luck": "🍀 Luck", "xp": "🧪 XP", "essence": "⚗️ Essence", "catch": "🎣 Catch",
            "discount": "🎟️ Discount"}.get(kind, kind)


def buff_strength_text(kind, s):
    if kind == "catch":
        return f"+{int(s)} animal"
    if kind.startswith("lure_"):
        return f"x{1 + s:g}"
    return f"{s * 100:+.0f}%"


# ═══════════════════════════════════════
# zoo ، team ، ناو ، قفڵ
# ═══════════════════════════════════════
def zoo_rows(uid, rarity=None, search=None):
    """[(animal_dict, qty, locked)] ڕیزکراو: دەگمەنترین یەکەم"""
    rows = db.execute("SELECT animal_id, qty, locked FROM player_animals WHERE user_id=? AND qty>0", (uid,)).fetchall()
    out = []
    n = _norm(search) if search else None
    for aid, qty, locked in rows:
        a = D.ANIMALS.get(aid)
        if a is None or (rarity and a["rarity"] != rarity) or (n and n not in _norm(a["name"])):
            continue
        out.append((a, qty, locked))
    out.sort(key=lambda r: (-D.RARITY_RANK[r[0]["rarity"]], r[0]["name"]))
    return out


def zoo_summary(uid):
    rows = zoo_rows(uid)
    total = sum(q for _, q, _ in rows)
    points = sum(a["zoo"] * q for a, q, _ in rows)
    by_r = {}
    for a, q, _ in rows:
        by_r[a["rarity"]] = by_r.get(a["rarity"], 0) + q
    discovered = db.execute("SELECT COUNT(*) FROM player_animals WHERE user_id=? AND total_caught>0", (uid,)).fetchone()[0]
    recent = db.execute("SELECT animal_id FROM player_animals WHERE user_id=? AND qty>0 ORDER BY last_ts DESC LIMIT 5",
                        (uid,)).fetchall()
    favs = [a for a, _, l in rows if l]
    return dict(total=total, points=points, by_rarity=by_r, discovered=discovered, species=len(D.ANIMALS),
                recent=[D.ANIMALS[r[0]] for r in recent if r[0] in D.ANIMALS], favorites=favs)


def get_team(uid):
    out = []
    for slot, aid in db.execute("SELECT slot, animal_id FROM player_zoo WHERE user_id=? ORDER BY slot", (uid,)):
        r = db.execute("SELECT xp, level, nickname, qty, total_caught FROM player_animals WHERE user_id=? AND animal_id=?",
                       (uid, aid)).fetchone()
        if r:
            out.append(dict(slot=slot, animal=D.ANIMALS[aid], xp=r[0], level=r[1], nickname=r[2], qty=r[3], caught=r[4]))
    return out


def team_add(uid, animal):
    ensure_user(uid)
    with Tx():
        r = db.execute("SELECT qty FROM player_animals WHERE user_id=? AND animal_id=?", (uid, animal["id"])).fetchone()
        if not r or r[0] < 1:
            return "not_owned"
        cur = [x[0] for x in db.execute("SELECT slot FROM player_zoo WHERE user_id=?", (uid,))]
        if db.execute("SELECT 1 FROM player_zoo WHERE user_id=? AND animal_id=?", (uid, animal["id"])).fetchone():
            return "already"
        free = [s for s in range(1, D.MAX_TEAM + 1) if s not in cur]
        if not free:
            return "full"
        db.execute("INSERT INTO player_zoo (user_id,slot,animal_id) VALUES (?,?,?)", (uid, free[0], animal["id"]))
        return "ok"


def team_remove(uid, animal):
    cur = db.execute("DELETE FROM player_zoo WHERE user_id=? AND animal_id=?", (uid, animal["id"]))
    db.commit()
    return cur.rowcount == 1


def set_lock(uid, animal, locked):
    cur = db.execute("UPDATE player_animals SET locked=? WHERE user_id=? AND animal_id=? AND total_caught>0",
                     (1 if locked else 0, uid, animal["id"]))
    db.commit()
    return cur.rowcount == 1


def set_nickname(uid, animal, name):
    cur = db.execute("UPDATE player_animals SET nickname=? WHERE user_id=? AND animal_id=? AND total_caught>0",
                     (name, uid, animal["id"]))
    db.commit()
    return cur.rowcount == 1


def animal_record(uid, aid):
    return db.execute("SELECT qty, total_caught, locked, xp, level, nickname, first_ts FROM player_animals "
                      "WHERE user_id=? AND animal_id=?", (uid, aid)).fetchone()


# ═══════════════════════════════════════
# فرۆشتن و sacrifice
# spec = dict(kind="all"|"rarity"|"animal", value=..., qty=None|int)
# ═══════════════════════════════════════
def build_plan(uid, spec, mode):
    """mode: 'sell' (دراو) یان 'sacrifice' (essence). هیچ شتێک ناگۆڕێت"""
    team = set(_team(uid))
    rows = db.execute("SELECT animal_id, qty, locked FROM player_animals WHERE user_id=? AND qty>0", (uid,)).fetchall()
    items, protected, total, count = [], 0, 0, 0
    for aid, qty, locked in rows:
        a = D.ANIMALS.get(aid)
        if a is None:
            continue
        kind = spec["kind"]
        if kind == "animal" and aid != spec["value"]:
            continue
        if kind == "rarity" and a["rarity"] != spec["value"]:
            continue
        if kind == "all" and a["rarity"] in D.PROTECTED_BULK:
            continue
        if locked:
            protected += qty
            continue
        avail = qty - (1 if aid in team else 0)  # یەک دانە لە ئاژەڵی team دەمێنێتەوە
        if avail <= 0:
            protected += qty
            continue
        take = avail if spec.get("qty") is None else min(avail, spec["qty"])
        if take <= 0:
            continue
        unit = a["sell"] if mode == "sell" else a["essence"]
        items.append((aid, take, unit))
        total += take * unit
        count += take
    return dict(items=items, total=total, count=count, protected=protected, mode=mode, spec=spec)


def plan_needs_confirm(plan):
    if plan["spec"]["kind"] in ("all", "rarity") or plan["count"] >= 20:
        return True
    return any(D.ANIMALS[aid]["rarity"] in D.CONFIRM_RARITIES for aid, _, _ in plan["items"])


def execute_plan(uid, spec, mode):
    """پلانەکە ئێستا دووبارە دروست دەکاتەوە (بۆ ئەوەی داتای کۆن بەکار نەهێنرێت) و ئەتۆمی جێبەجێی دەکات"""
    ensure_user(uid)
    now = time.time()
    with Tx():
        plan = build_plan(uid, spec, mode)
        if plan["count"] <= 0:
            return None
        team = set(_team(uid))
        for aid, take, _ in plan["items"]:
            reserve = 1 if aid in team else 0
            cur = db.execute(
                "UPDATE player_animals SET qty=qty-? WHERE user_id=? AND animal_id=? AND locked=0 AND qty-?>=?",
                (take, uid, aid, take, reserve))
            if cur.rowcount != 1:
                raise RuntimeError("collection changed")  # Tx دەگەڕێتەوە ڕۆڵبەک
        total = plan["total"]
        if mode == "sell":
            db.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (total, uid))
            db.execute("UPDATE hunt_stats SET z_earned_sell=z_earned_sell+? WHERE user_id=?", (total, uid))
        else:
            buffs = get_buffs(uid, now)
            total = int(total * (1 + (buffs["essence"][0] if "essence" in buffs else 0.0)))
            plan["total"] = total
            db.execute("UPDATE player_essence SET essence=essence+? WHERE user_id=?", (total, uid))
            db.execute("UPDATE hunt_stats SET essence_earned=essence_earned+? WHERE user_id=?", (total, uid))
        detail = ", ".join(f"{D.ANIMALS[a]['name']}x{n}" for a, n, _ in plan["items"][:12])
        db.execute("INSERT INTO collection_history (user_id,ts,action,detail,amount) VALUES (?,?,?,?,?)",
                   (uid, now, mode, detail[:500], total))
        return plan


def get_essence(uid):
    ensure_user(uid)
    return db.execute("SELECT essence FROM player_essence WHERE user_id=?", (uid,)).fetchone()[0]


def collection_history(uid, limit=10):
    return db.execute("SELECT ts, action, detail, amount FROM collection_history WHERE user_id=? ORDER BY id DESC LIMIT ?",
                      (uid, limit)).fetchall()


# ═══════════════════════════════════════
# HUNTBOT
# ═══════════════════════════════════════
def hb_levels(uid):
    lv = {s: 0 for s in D.HB_STATS}
    for s, l in db.execute("SELECT stat, level FROM huntbot_upgrades WHERE user_id=?", (uid,)):
        if s in lv:
            lv[s] = l
    return lv


def hb_stats(lv):
    return dict(
        animals_per_hour=D.HB_BASE_ANIMALS_PER_HOUR * (1 + 0.10 * lv["efficiency"]),
        essence_per_hour=D.HB_BASE_ESSENCE_PER_HOUR * (1 + 0.10 * lv["gain"]),
        xp_per_hour=D.HB_BASE_XP_PER_HOUR * (1 + 0.15 * lv["experience"]),
        max_hours=D.HB_BASE_MAX_HOURS + 0.5 * lv["duration"],
        cost_per_animal=max(1, round(D.HUNT_COST * (1 - D.HB_COST_DISCOUNT_PER_LEVEL * lv["cost"]))),
        bot_chance=D.HB_BASE_BOT_CHANCE + 0.001 * lv["radar"],
    )


def hb_upgrade_cost(stat, level):
    return D.HB_STATS[stat]["base"] * (level + 1) ** 2


def hb_total_level(uid):
    return sum(hb_levels(uid).values())


def hb_row(uid):
    ensure_user(uid)
    return db.execute("SELECT start_ts, end_ts, hours, animals, essence, xp, bot_chance, cost, collected "
                      "FROM huntbot WHERE user_id=?", (uid,)).fetchone()


def hb_start(uid, hours):
    ensure_user(uid)
    now = time.time()
    with Tx():
        row = db.execute("SELECT collected FROM huntbot WHERE user_id=?", (uid,)).fetchone()
        if row[0] == 0:
            return dict(error="busy")
        st = hb_stats(hb_levels(uid))
        hours = min(hours, st["max_hours"])
        if hours < D.HB_MIN_HOURS:
            return dict(error="too_short")
        animals = max(1, int(st["animals_per_hour"] * hours))
        cost = animals * st["cost_per_animal"]
        essence = int(st["essence_per_hour"] * hours)
        xp = int(st["xp_per_hour"] * hours)
        cur = db.execute("UPDATE users SET coins=coins-? WHERE user_id=? AND coins>=?", (cost, uid, cost))
        if cur.rowcount != 1:
            bal = db.execute("SELECT coins FROM users WHERE user_id=?", (uid,)).fetchone()[0]
            return dict(error="no_cash", cost=cost, balance=bal)
        db.execute("UPDATE huntbot SET start_ts=?, end_ts=?, hours=?, animals=?, essence=?, xp=?, bot_chance=?, "
                   "cost=?, collected=0 WHERE user_id=?",
                   (now, now + hours * 3600, hours, animals, essence, xp, st["bot_chance"], cost, uid))
        db.execute("UPDATE hunt_stats SET z_spent=z_spent+? WHERE user_id=?", (cost, uid))
        return dict(ok=True, hours=hours, animals=animals, cost=cost, essence=essence, xp=xp, end=now + hours * 3600)


def hb_claim(uid):
    """ئەگەر run تەواو بووبێت، یەکجار کۆی دەکاتەوە. flag و پاداشتەکان لە یەک مامەڵەدان، بۆیە دووبار نابێت"""
    ensure_user(uid)
    now = time.time()
    with Tx():
        cur = db.execute("UPDATE huntbot SET collected=1 WHERE user_id=? AND collected=0 AND end_ts<=?", (uid, now))
        if cur.rowcount != 1:
            return None
        n, essence, xp, bot_chance, hours = db.execute(
            "SELECT animals, essence, xp, bot_chance, hours FROM huntbot WHERE user_id=?", (uid,)).fetchone()
        table = rarity_table(0.0)
        counts = {}
        for _ in range(n):
            if D.BOT_ANIMALS and rng.random() < bot_chance:
                a = rng.choice(D.BOT_ANIMALS)
            else:
                a = roll_animal(table)
            counts[a["id"]] = counts.get(a["id"], 0) + 1
        new_ids = _add_animals(uid, counts, now)
        buffs = get_buffs(uid, now)
        essence = int(essence * (1 + (buffs["essence"][0] if "essence" in buffs else 0.0)))
        db.execute("UPDATE player_essence SET essence=essence+? WHERE user_id=?", (essence, uid))
        db.execute("UPDATE hunt_stats SET total_animals=total_animals+?, essence_earned=essence_earned+?, "
                   "hunt_time=hunt_time+? WHERE user_id=?", (n, essence, hours * 3600, uid))
        events = [k for k, _, _ in active_events(now)]
        ups = _award_team_xp(uid, int(xp * (1 + sum(D.EVENTS[k]["xp"] for k in events))))
        return dict(animals=n, counts=counts, new=new_ids, essence=essence, xp=xp, level_ups=ups, hours=hours)


def hb_pending_users():
    """هەموو ئەو بەکارهێنەرانەی huntbot یان تەواو بووە و هێشتا کۆ نەکراوەتەوە"""
    return [r[0] for r in db.execute("SELECT user_id FROM huntbot WHERE collected=0 AND end_ts<=?", (time.time(),))]


def hb_upgrade(uid, stat, expected_level):
    ensure_user(uid)
    with Tx():
        cur_lvl = hb_levels(uid)[stat]
        if cur_lvl != expected_level:
            return dict(error="changed")
        if cur_lvl >= D.HB_MAX_LEVEL:
            return dict(error="max")
        cost = hb_upgrade_cost(stat, cur_lvl)
        cur = db.execute("UPDATE player_essence SET essence=essence-? WHERE user_id=? AND essence>=?", (cost, uid, cost))
        if cur.rowcount != 1:
            return dict(error="no_essence", cost=cost)
        db.execute("INSERT INTO huntbot_upgrades (user_id,stat,level) VALUES (?,?,?) "
                   "ON CONFLICT(user_id,stat) DO UPDATE SET level=excluded.level", (uid, stat, cur_lvl + 1))
        return dict(ok=True, level=cur_lvl + 1, cost=cost)


# ═══════════════════════════════════════
# ئامار ، leaderboard
# ═══════════════════════════════════════
def hunt_stats(uid):
    ensure_user(uid)
    s = db.execute("SELECT total_hunts,total_animals,z_spent,z_earned_sell,essence_earned,biggest_session,lootboxes,"
                   "gems_found,hunt_time,highest_rank FROM hunt_stats WHERE user_id=?", (uid,)).fetchone()
    by = {r: 0 for r in ("common", "rare", "legendary")}
    for r, c in db.execute("SELECT a.rarity, SUM(p.total_caught) FROM player_animals p JOIN animals a ON a.id=p.animal_id "
                           "WHERE p.user_id=? AND a.rarity IN ('common','rare','legendary') GROUP BY a.rarity", (uid,)):
        by[r] = c or 0
    return dict(hunts=s[0], animals=s[1], spent=s[2], earned=s[3], essence=s[4], biggest=s[5], boxes=s[6],
                gems=s[7], hunt_time=s[8], highest=D.RARITY_ORDER[s[9]] if s[9] >= 0 else None,
                common=by["common"], rare=by["rare"], legendary=by["legendary"], buffs=get_buffs(uid))


LEADERBOARDS = {
    "zoo":       ("🏆 Highest Zoo Points",
                  "SELECT p.user_id, SUM(p.qty*a.zoo) v FROM player_animals p JOIN animals a ON a.id=p.animal_id "
                  "WHERE p.qty>0 GROUP BY p.user_id HAVING v>0 ORDER BY v DESC LIMIT 10"),
    "animals":   ("🐾 Largest Collection",
                  "SELECT user_id, SUM(qty) v FROM player_animals WHERE qty>0 GROUP BY user_id HAVING v>0 ORDER BY v DESC LIMIT 10"),
    "legendary": ("🟡 Most Legendary Animals",
                  "SELECT p.user_id, SUM(p.qty) v FROM player_animals p JOIN animals a ON a.id=p.animal_id "
                  "WHERE a.rarity='legendary' AND p.qty>0 GROUP BY p.user_id HAVING v>0 ORDER BY v DESC LIMIT 10"),
    "hidden":    ("⚫ Most Hidden Animals",
                  "SELECT p.user_id, SUM(p.qty) v FROM player_animals p JOIN animals a ON a.id=p.animal_id "
                  "WHERE a.rarity='hidden' AND p.qty>0 GROUP BY p.user_id HAVING v>0 ORDER BY v DESC LIMIT 10"),
    "hunts":     ("🎯 Most Hunts",
                  "SELECT user_id, total_hunts v FROM hunt_stats WHERE total_hunts>0 ORDER BY v DESC LIMIT 10"),
    "essence":   ("💠 Highest Essence",
                  "SELECT user_id, essence v FROM player_essence WHERE essence>0 ORDER BY v DESC LIMIT 10"),
    "huntbot":   ("🤖 Highest Huntbot Level",
                  "SELECT user_id, SUM(level) v FROM huntbot_upgrades GROUP BY user_id HAVING v>0 ORDER BY v DESC LIMIT 10"),
    "rare":      ("🔵 Most Rare Animals",
                  "SELECT p.user_id, SUM(p.qty) v FROM player_animals p JOIN animals a ON a.id=p.animal_id "
                  "WHERE a.rarity='rare' AND p.qty>0 GROUP BY p.user_id HAVING v>0 ORDER BY v DESC LIMIT 10"),
    "event":     ("🎃 Event Animals Caught",
                  "SELECT p.user_id, SUM(p.total_caught) v FROM player_animals p JOIN animals a ON a.id=p.animal_id "
                  "WHERE a.event IS NOT NULL GROUP BY p.user_id HAVING v>0 ORDER BY v DESC LIMIT 10"),
}


def leaderboard(key):
    title, sql = LEADERBOARDS[key]
    return title, db.execute(sql).fetchall()


# ═══════════════════════════════════════
# ئەدمین
# ═══════════════════════════════════════
def admin_event(key, hours):
    now = time.time()
    db.execute("INSERT INTO hunting_events (key,start_ts,end_ts) VALUES (?,?,?) "
               "ON CONFLICT(key) DO UPDATE SET start_ts=excluded.start_ts, end_ts=excluded.end_ts",
               (key, now, now + hours * 3600))
    db.commit()


def admin_event_stop(key):
    db.execute("UPDATE hunting_events SET end_ts=? WHERE key=?", (time.time(), key))
    db.commit()


def admin_give_box(uid, tier, n):
    ensure_user(uid)
    with Tx():
        _grant_box(uid, tier, n)


def admin_give_item(uid, key, n):
    ensure_user(uid)
    with Tx():
        db.execute("INSERT INTO player_items (user_id,item,qty) VALUES (?,?,?) "
                   "ON CONFLICT(user_id,item) DO UPDATE SET qty=qty+excluded.qty", (uid, key, n))


def admin_give_gem(uid, tier):
    ensure_user(uid)
    with Tx():
        return _give_gem(uid, tier, time.time())


def admin_give_animal(uid, aid, n):
    ensure_user(uid)
    with Tx():
        _add_animals(uid, {aid: n}, time.time())


def admin_set_gem(tier, animals, durability):
    db.execute("UPDATE hunting_gems SET animals=?, durability=? WHERE tier=?", (animals, durability, tier))
    db.commit()
