"""
Zero Anime Cards — سیستەمی کارتەکانی ئەنیمی بۆ Zero Bot

 📦 سندوقەکان (Chest Shop)      💳 کڕینی ڕاستەوخۆ
 📚 کارتەکانم (بەهێزکردن، پیشاندان، بەخشین، فرۆشتن، سڕینەوە)
 🏪 مارکێتی یاریزانان           ⚔️ جەنگ (لە card_battle.py)

دراو: هەمان zero coin ی بۆتەکە (database.py). داتای کارتەکان: cards_data.py
"""

import random

import discord
from discord.ext import commands

from database import db, get_balance, spend_coins, add_coins, transfer_coins
from utils import make_embed, PREFIX, CURRENCY, CASH_EMOJI, ERROR, SUCCESS, WARN
from cards_data import ANIME_CHARACTERS, RARITY_CONFIG, CHEST_CONFIG, DEFAULT_IMAGE

# ═══════════════════════════════════════
# بەشی ١: ڕێکخستنەکان (لێرە دەستکاری بکە)
# ═══════════════════════════════════════
MAX_CARDS_LIMIT = 20                       # زۆرترین کارت بۆ هەر کەسێک
MAX_LEVEL = 3
UPGRADE_COSTS = {1: 250_000, 2: 750_000}   # تێچووی بەهێزکردن لە ئاستی N بۆ N+1
UPGRADE_MULTIPLIER = 1.60                  # هێز لە هەر بەهێزکردنێکدا ×١.٦
MARKET_MAX_PRICE = 1_000_000_000_000
MARKET_SHOW_LIMIT = 20                     # چەند کارت لە مارکێت پیشان بدرێت

PURPLE = 0x9B59B6
GOLD = 0xF1C40F
BLUE = 0x5865F2
ORANGE = 0xE67E22

RARITY_ORDER = list(RARITY_CONFIG.keys())

# ═══════════════════════════════════════
# بەشی ٢: داتابەیس
# ═══════════════════════════════════════
db.execute(
    "CREATE TABLE IF NOT EXISTS anime_cards ("
    "card_id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "user_id INTEGER NOT NULL, "
    "character_id TEXT NOT NULL, "
    "character_name TEXT NOT NULL, "
    "anime_title TEXT NOT NULL, "
    "rarity TEXT NOT NULL, "
    "level INTEGER NOT NULL DEFAULT 1, "
    "power INTEGER NOT NULL, "
    "image_url TEXT, "
    "created_at REAL NOT NULL DEFAULT 0)"
)
db.execute("CREATE INDEX IF NOT EXISTS idx_cards_user ON anime_cards(user_id)")
db.execute(
    "CREATE TABLE IF NOT EXISTS card_market ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "seller_id INTEGER NOT NULL, "
    "card_id INTEGER NOT NULL UNIQUE, "
    "character_name TEXT NOT NULL, "
    "price INTEGER NOT NULL, "
    "created_at REAL NOT NULL DEFAULT 0)"
)
db.commit()

CARD_COLS = "card_id, user_id, character_id, character_name, anime_title, rarity, level, power, image_url"


def _rows(cur):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def fetch_card(card_id):
    rows = _rows(db.execute(f"SELECT {CARD_COLS} FROM anime_cards WHERE card_id = ?", (card_id,)))
    return rows[0] if rows else None


def fetch_cards(user_id):
    return _rows(db.execute(
        f"SELECT {CARD_COLS} FROM anime_cards WHERE user_id = ? ORDER BY power DESC, card_id", (user_id,)
    ))


def count_cards(user_id):
    return db.execute("SELECT COUNT(*) FROM anime_cards WHERE user_id = ?", (user_id,)).fetchone()[0]


def listing_for_card(card_id):
    rows = _rows(db.execute("SELECT id, seller_id, card_id, price FROM card_market WHERE card_id = ?", (card_id,)))
    return rows[0] if rows else None


def listed_ids(user_id):
    return {r[0] for r in db.execute("SELECT card_id FROM card_market WHERE seller_id = ?", (user_id,)).fetchall()}


_MARKET_SELECT = (
    "SELECT m.id AS m_id, m.seller_id, m.price, c.card_id, c.user_id, c.character_id, c.character_name, "
    "c.anime_title, c.rarity, c.level, c.power, c.image_url "
    "FROM card_market m JOIN anime_cards c ON c.card_id = m.card_id AND c.user_id = m.seller_id "
)


def cleanup_market():
    # لیستی ئەو کارتانە دەسڕێتەوە کە خاوەنەکەیان گۆڕاوە یان نەماون
    db.execute(
        "DELETE FROM card_market WHERE NOT EXISTS ("
        "SELECT 1 FROM anime_cards c WHERE c.card_id = card_market.card_id AND c.user_id = card_market.seller_id)"
    )
    db.commit()


def market_rows(limit=MARKET_SHOW_LIMIT):
    cleanup_market()
    return _rows(db.execute(_MARKET_SELECT + "ORDER BY m.id DESC LIMIT ?", (limit,)))


def market_row(m_id):
    cleanup_market()
    rows = _rows(db.execute(_MARKET_SELECT + "WHERE m.id = ?", (m_id,)))
    return rows[0] if rows else None


# ═══════════════════════════════════════
# بەشی ٣: یاریدەدەرەکان (کارتی جوان، ڕەنگ، نرخ)
# ═══════════════════════════════════════
_DEFAULT_RARITY = {"emoji": "🎴", "color": BLUE, "stars": 1, "base_power": 100, "direct_buy_cost": 100_000}


def rarity_info(rarity):
    return RARITY_CONFIG.get(rarity, _DEFAULT_RARITY)


def find_char(char_id):
    return next((c for c in ANIME_CHARACTERS if c["id"] == char_id), None)


def char_image(char_id, level, fallback=None):
    char = find_char(char_id)
    if not char:
        return fallback or DEFAULT_IMAGE
    if level >= 3:
        return char.get("image_lvl3") or char.get("image_lvl2") or char.get("image_lvl1") or DEFAULT_IMAGE
    if level == 2:
        return char.get("image_lvl2") or char.get("image_lvl1") or DEFAULT_IMAGE
    return char.get("image_lvl1") or DEFAULT_IMAGE


def money(n):
    return f"{CASH_EMOJI} {n:,}"


def stars(n):
    n = max(1, min(5, n))
    return "★" * n + "☆" * (5 - n)


def level_bar(level):
    return "▰" * level + "▱" * (MAX_LEVEL - level)


def mk(title, description=None, color=PURPLE):
    return make_embed(title, description, color)


def card_embed(card, *, title=None, lead=None, listing=None, extra=None, show_upgrade=True):
    """کارتێکی جوان دروست دەکات. card دەتوانێت پێشبینینێکی ڕاستەوخۆش بێت (بێ card_id)"""
    r = rarity_info(card["rarity"])
    level = card.get("level", 1)
    e = mk(title or f"{r['emoji']}  {card['character_name']}", None, r["color"])
    head = f"📺 *{card['anime_title']}*\n{stars(r['stars'])}"
    e.description = f"{lead}\n\n{head}" if lead else head
    e.add_field(name="💎 جۆر", value=f"{r['emoji']} **{card['rarity']}**", inline=True)
    e.add_field(name="📈 ئاست", value=f"`{level_bar(level)}` Lvl {level}", inline=True)
    e.add_field(name="⚔️ هێز", value=f"**{card['power']:,}** PL", inline=True)
    if card.get("card_id"):
        e.add_field(name="🆔 کۆد", value=f"`#{card['card_id']}`", inline=True)
    if listing:
        e.add_field(name="🏪 لە مارکێتدایە", value=money(listing["price"]), inline=True)
    elif show_upgrade and card.get("card_id") and level < MAX_LEVEL:
        cost = UPGRADE_COSTS[level]
        nxt = int(card["power"] * UPGRADE_MULTIPLIER)
        e.add_field(name="⬆️ بەهێزکردنی داهاتوو", value=f"{money(cost)} ← **{nxt:,}** PL", inline=True)
    elif show_upgrade and card.get("card_id"):
        e.add_field(name="🌟 ئاست", value="گەیشتە لوتکە (Max)", inline=True)
    for name, value, inline in (extra or []):
        e.add_field(name=name, value=value, inline=inline)
    e.set_image(url=card.get("image_url") or DEFAULT_IMAGE)
    return e


ERR_TEXT = {
    "full": f"🃏 کارتەکانت پڕن (**{MAX_CARDS_LIMIT}/{MAX_CARDS_LIMIT}**)! سەرەتا کارتێک بسڕەوە، ببەخشە یان بیفرۆشە.",
    "no_money": "💸 دراوی پێویستت نییە!",
    "missing": "❌ ئەم کارتە نەدۆزرایەوە یان هی تۆ نییە!",
    "listed": "🏪 ئەم کارتە لە مارکێتدایە. سەرەتا لە مارکێت لای ببە.",
    "already": "🏪 ئەم کارتە پێشتر لە مارکێتدایە!",
    "max": "🌟 ئەم کارتە گەیشتووەتە لوتکەی ئاست (Lvl 3)!",
    "gone": "❌ ئەم کارتە لە مارکێت نەماوە (فرۆشراوە یان لابراوە)!",
    "own": "❌ ناتوانیت کارتی خۆت بکڕیت!",
    "bad_price": f"❌ نرخ دەبێت ژمارەیەک بێت لەنێوان **1** و **{MARKET_MAX_PRICE:,}**!",
    "self": "❌ ناتوانیت کارت بدەیت بە خۆت!",
    "bot": "❌ ناتوانیت کارت بدەیت بە بۆت!",
    "target_full": "❌ ئەو کەسە کارتەکانی پڕن!",
    "nochar": "❌ ئەم کاراکتەرە نەدۆزرایەوە!",
}


def err_embed(code):
    return mk("❌ هەڵە", ERR_TEXT.get(code, "❌ هەڵەیەک ڕوویدا."), ERROR)


# ═══════════════════════════════════════
# بەشی ٤: لۆجیکی یاری (بێ دوگمە — پشکنین و گۆڕانکاری داتابەیس)
# هیچ await ێک تێیدا نییە، بۆیە ئەتۆمین و ڕێگری لە تێکچوون دەکەن
# ═══════════════════════════════════════
def give_card(user_id, char):
    r = rarity_info(char["rarity"])
    cur = db.execute(
        "INSERT INTO anime_cards (user_id, character_id, character_name, anime_title, rarity, level, power, image_url, created_at) "
        "VALUES (?, ?, ?, ?, ?, 1, ?, ?, strftime('%s','now'))",
        (user_id, char["id"], char["name"], char["anime"], char["rarity"], r["base_power"], char_image(char["id"], 1)),
    )
    db.commit()
    return fetch_card(cur.lastrowid)


def open_chest(user_id, key):
    chest = CHEST_CONFIG.get(key)
    if not chest:
        return None, "nochar"
    if count_cards(user_id) >= MAX_CARDS_LIMIT:
        return None, "full"
    if not spend_coins(user_id, chest["cost"]):
        return None, "no_money"
    try:
        rarities = list(chest["odds"].keys())
        weights = list(chest["odds"].values())
        chosen = random.choices(rarities, weights=weights, k=1)[0]
        pool = [c for c in ANIME_CHARACTERS if c["rarity"] == chosen] or ANIME_CHARACTERS
        return give_card(user_id, random.choice(pool)), None
    except Exception:
        add_coins(user_id, chest["cost"])  # گەڕاندنەوەی دراو ئەگەر هەڵەیەک ڕوویدا
        raise


def buy_direct(user_id, char_id):
    char = find_char(char_id)
    if not char:
        return None, "nochar"
    cost = rarity_info(char["rarity"])["direct_buy_cost"]
    if count_cards(user_id) >= MAX_CARDS_LIMIT:
        return None, "full"
    if not spend_coins(user_id, cost):
        return None, "no_money"
    try:
        return give_card(user_id, char), None
    except Exception:
        add_coins(user_id, cost)
        raise


def upgrade_card(user_id, card_id):
    card = fetch_card(card_id)
    if not card or card["user_id"] != user_id:
        return None, "missing", 0
    if listing_for_card(card_id):
        return None, "listed", 0
    level = card["level"]
    if level >= MAX_LEVEL:
        return None, "max", 0
    cost = UPGRADE_COSTS[level]
    if not spend_coins(user_id, cost):
        return None, "no_money", cost
    new_level = level + 1
    new_power = int(card["power"] * UPGRADE_MULTIPLIER)
    new_img = char_image(card["character_id"], new_level, card["image_url"])
    db.execute(
        "UPDATE anime_cards SET level = ?, power = ?, image_url = ? WHERE card_id = ?",
        (new_level, new_power, new_img, card_id),
    )
    db.commit()
    return fetch_card(card_id), None, cost


def gift_card(owner_id, target, card_id):
    if target.bot:
        return None, "bot"
    if target.id == owner_id:
        return None, "self"
    card = fetch_card(card_id)
    if not card or card["user_id"] != owner_id:
        return None, "missing"
    if listing_for_card(card_id):
        return None, "listed"
    if count_cards(target.id) >= MAX_CARDS_LIMIT:
        return None, "target_full"
    db.execute("UPDATE anime_cards SET user_id = ? WHERE card_id = ?", (target.id, card_id))
    db.commit()
    return card, None


def delete_card(user_id, card_id):
    card = fetch_card(card_id)
    if not card or card["user_id"] != user_id:
        return None, "missing"
    if listing_for_card(card_id):
        return None, "listed"
    db.execute("DELETE FROM anime_cards WHERE card_id = ?", (card_id,))
    db.commit()
    return card, None


def list_card(user_id, card_id, price):
    if not (1 <= price <= MARKET_MAX_PRICE):
        return None, "bad_price"
    card = fetch_card(card_id)
    if not card or card["user_id"] != user_id:
        return None, "missing"
    if listing_for_card(card_id):
        return None, "already"
    db.execute(
        "INSERT INTO card_market (seller_id, card_id, character_name, price, created_at) "
        "VALUES (?, ?, ?, ?, strftime('%s','now'))",
        (user_id, card_id, card["character_name"], price),
    )
    db.commit()
    return card, None


def unlist_card(user_id, card_id):
    cur = db.execute("DELETE FROM card_market WHERE card_id = ? AND seller_id = ?", (card_id, user_id))
    db.commit()
    return cur.rowcount == 1


def buy_listing(buyer_id, m_id):
    row = market_row(m_id)
    if not row:
        return None, "gone"
    if row["seller_id"] == buyer_id:
        return None, "own"
    if count_cards(buyer_id) >= MAX_CARDS_LIMIT:
        return None, "full"
    if not transfer_coins(buyer_id, row["seller_id"], row["price"]):
        return None, "no_money"
    db.execute("DELETE FROM card_market WHERE id = ?", (m_id,))
    db.execute("UPDATE anime_cards SET user_id = ? WHERE card_id = ?", (buyer_id, row["card_id"]))
    db.commit()
    return row, None


# ═══════════════════════════════════════
# بەشی ٥: بنەمای دوگمەکان
# ═══════════════════════════════════════
class OwnedView(discord.ui.View):
    """تەنها خاوەنی مێنیوەکە دەتوانێت کلیک بکات"""

    def __init__(self, user, timeout=180):
        super().__init__(timeout=timeout)
        self.user = user
        self.message = None  # تەنها بۆ مێنیوی سەرەکی (hub)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(f"❌ ئەم مێنیوە بۆ تۆ نییە! بنووسە: `{PREFIX} cards`", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


async def go(interaction, screen):
    """لەسەر هەمان پەیام بچۆ بۆ شاشەیەکی تر"""
    embed, view = screen
    await interaction.response.edit_message(embed=embed, view=view)


async def open_private(interaction, screen):
    embed, view = screen
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


def _is_private(interaction):
    msg = interaction.message
    return bool(msg and msg.flags.ephemeral)


async def announce(interaction, embed):
    """ڕاگەیاندنی گشتی. ئەگەر پەیامەکە خۆی گشتی بێت پێویست ناکات"""
    if not _is_private(interaction):
        return
    try:
        await interaction.channel.send(embed=embed)
    except (discord.HTTPException, AttributeError):
        pass


class BackButton(discord.ui.Button):
    def __init__(self, label, target, row=None):
        super().__init__(label=label, emoji="⬅️", style=discord.ButtonStyle.secondary, row=row)
        self.target = target  # فەرمانێک کە شاشەی گەڕانەوە دروست دەکات

    async def callback(self, interaction):
        await go(interaction, self.target(interaction.user))


# ═══════════════════════════════════════
# بەشی ٦: 🏠 مێنیوی سەرەکی
# ═══════════════════════════════════════
def hub_screen(user):
    cards = fetch_cards(user.id)
    best = cards[0] if cards else None
    e = mk("🎴  Zero Anime Cards", None, PURPLE)
    e.description = (
        f"بەخێربێیت {user.mention}! کارتی ئەنیمی کۆبکەرەوە، بەهێزیان بکە و لە جەنگدا بیانبەکارببە.\n\n"
        "📦 **سندوقەکان**  ─  کارتی هەڕەمەکی بکڕە\n"
        "💳 **کڕینی ڕاستەوخۆ**  ─  کارتی دیاریکراو بکڕە\n"
        "📚 **کارتەکانم**  ─  بەهێزکردن، پیشاندان، بەخشین\n"
        "🏪 **مارکێت**  ─  لەگەڵ یاریزانان بکڕە و بفرۆشە\n"
        f"⚔️ **جەنگ**  ─  `{PREFIX} cardbattle @کەس <گرەو>`"
    )
    e.add_field(name="💰 باڵانس", value=money(get_balance(user.id)), inline=True)
    e.add_field(name="🃏 کارتەکان", value=f"**{len(cards)}** / {MAX_CARDS_LIMIT}", inline=True)
    if best:
        r = rarity_info(best["rarity"])
        e.add_field(name="👑 بەهێزترین", value=f"{r['emoji']} {best['character_name']}\n`{best['power']:,} PL`", inline=True)
        e.set_thumbnail(url=best["image_url"] or DEFAULT_IMAGE)
    return e, MainMenuView(user)


class MainMenuView(OwnedView):
    def __init__(self, user):
        super().__init__(user, timeout=180)

    @discord.ui.button(label="سندوقەکان", emoji="📦", style=discord.ButtonStyle.primary, row=0)
    async def chests_btn(self, interaction, button):
        await open_private(interaction, chests_screen(interaction.user))

    @discord.ui.button(label="کڕینی ڕاستەوخۆ", emoji="💳", style=discord.ButtonStyle.success, row=0)
    async def direct_btn(self, interaction, button):
        await open_private(interaction, direct_anime_screen(interaction.user))

    @discord.ui.button(label="کارتەکانم", emoji="📚", style=discord.ButtonStyle.secondary, row=1)
    async def mycards_btn(self, interaction, button):
        await open_private(interaction, mycards_screen(interaction.user))

    @discord.ui.button(label="مارکێت", emoji="🏪", style=discord.ButtonStyle.primary, row=1)
    async def market_btn(self, interaction, button):
        await open_private(interaction, market_screen(interaction.user))


# ═══════════════════════════════════════
# بەشی ٧: 📦 سندوقەکان
# ═══════════════════════════════════════
def _odds_text(chest):
    return "\n".join(f"{rarity_info(r)['emoji']} {r}  `{p}%`" for r, p in chest["odds"].items())


def chests_screen(user):
    e = mk("📦  فرۆشگای سندوقەکان", "سندوقێک هەڵبژێرە. ڕێژەی دەرچوونی هەر جۆرێک لە خوارەوە دیارە.", GOLD)
    for key, c in CHEST_CONFIG.items():
        e.add_field(name=f"{c['emoji']} {c['name']}", value=f"{money(c['cost'])}\n{_odds_text(c)}", inline=True)
    e.add_field(name="💰 باڵانسی تۆ", value=money(get_balance(user.id)), inline=False)
    return e, ChestShopView(user)


class ChestButton(discord.ui.Button):
    def __init__(self, key):
        c = CHEST_CONFIG[key]
        super().__init__(label=f"{c['name']} · {c['cost']:,}", emoji=c["emoji"], style=discord.ButtonStyle.secondary)
        self.key = key

    async def callback(self, interaction):
        await go(interaction, chest_confirm_screen(interaction.user, self.key))


class ChestShopView(OwnedView):
    def __init__(self, user):
        super().__init__(user)
        for key in CHEST_CONFIG:
            self.add_item(ChestButton(key))


def chest_confirm_screen(user, key):
    c = CHEST_CONFIG[key]
    count = count_cards(user.id)
    e = mk(f"{c['emoji']}  دڵنیایت دەتەوێت {c['name']} بکڕیت؟", None, c["color"])
    e.description = f"💰 **تێچوو:** {money(c['cost'])}\n💳 **باڵانسی تۆ:** {money(get_balance(user.id))}\n🃏 **کارتەکانت:** {count}/{MAX_CARDS_LIMIT}"
    e.add_field(name="📊 ڕێژەی دەرچوونی کارت", value=_odds_text(c), inline=False)
    return e, ChestConfirmView(user, key)


class ChestConfirmView(OwnedView):
    def __init__(self, user, key):
        super().__init__(user, timeout=60)
        self.key = key
        self.add_item(BackButton("فرۆشگا", chests_screen))

    @discord.ui.button(label="بەڵێ، بیکڕە", emoji="✅", style=discord.ButtonStyle.success)
    async def confirm(self, interaction, button):
        card, err = open_chest(interaction.user.id, self.key)
        if err:
            return await go(interaction, (err_embed(err), ChestResultView(self.user, self.key, retry=False)))

        c = CHEST_CONFIG[self.key]
        e = card_embed(card, title=f"🎉  {card['character_name']}  🎉",
                       lead=f"لە **{c['name']}** ئەم کارتەت بۆ دەرچوو!")
        await go(interaction, (e, ChestResultView(self.user, self.key)))

        pub = card_embed(card, title=f"🎁  {interaction.user.display_name} سندوقێکی کردەوە!",
                         lead=f"{interaction.user.mention} لە **{c['name']}** ئەم کارتەی بەدەستهێنا!",
                         show_upgrade=False)
        await announce(interaction, pub)


class ChestResultView(OwnedView):
    def __init__(self, user, key, retry=True):
        super().__init__(user, timeout=120)
        self.key = key
        if retry:
            again = discord.ui.Button(label="سندوقێکی تر", emoji="🔁", style=discord.ButtonStyle.success)

            async def again_cb(interaction):
                await go(interaction, chest_confirm_screen(interaction.user, self.key))

            again.callback = again_cb
            self.add_item(again)
        self.add_item(BackButton("فرۆشگا", chests_screen))


# ═══════════════════════════════════════
# بەشی ٨: 💳 کڕینی ڕاستەوخۆ (ئەنیمی ← کاراکتەر ← کڕین)
# ═══════════════════════════════════════
def direct_anime_screen(user):
    animes = sorted({c["anime"] for c in ANIME_CHARACTERS})
    lines = [f"{r['emoji']} **{name}**  ─  {money(r['direct_buy_cost'])}" for name, r in RARITY_CONFIG.items()]
    e = mk("💳  کڕینی ڕاستەوخۆ", "**نرخی هەر جۆرێک:**\n" + "\n".join(lines) + "\n\nسەرەتا ئەنیمییەک هەڵبژێرە:", BLUE)
    return e, DirectAnimeView(user, animes)


class DirectAnimeView(OwnedView):
    def __init__(self, user, animes):
        super().__init__(user)
        options = [
            discord.SelectOption(label=a[:100], value=a[:100], emoji="📺",
                                 description=f"{sum(1 for c in ANIME_CHARACTERS if c['anime'] == a)} کاراکتەر")
            for a in animes[:25]
        ]
        if options:
            sel = discord.ui.Select(placeholder="📺 ئەنیمییەک هەڵبژێرە...", options=options)

            async def cb(interaction):
                await go(interaction, direct_chars_screen(interaction.user, sel.values[0]))

            sel.callback = cb
            self.add_item(sel)


def direct_chars_screen(user, anime):
    chars = [c for c in ANIME_CHARACTERS if c["anime"] == anime]
    chars.sort(key=lambda c: RARITY_ORDER.index(c["rarity"]) if c["rarity"] in RARITY_ORDER else 0, reverse=True)
    lines = [f"{rarity_info(c['rarity'])['emoji']} **{c['name']}**  ─  {money(rarity_info(c['rarity'])['direct_buy_cost'])}" for c in chars]
    e = mk(f"📺  {anime}", "\n".join(lines) + "\n\nکارتێک هەڵبژێرە بۆ بینین و کڕین:", BLUE)
    return e, DirectCharsView(user, chars)


class DirectCharsView(OwnedView):
    def __init__(self, user, chars):
        super().__init__(user)
        options = [
            discord.SelectOption(label=c["name"][:100], value=c["id"], emoji=rarity_info(c["rarity"])["emoji"],
                                 description=f"{c['rarity']} • {rarity_info(c['rarity'])['direct_buy_cost']:,}")
            for c in chars[:25]
        ]
        if options:
            sel = discord.ui.Select(placeholder="🎴 کاراکتەرێک هەڵبژێرە...", options=options)

            async def cb(interaction):
                await go(interaction, direct_char_screen(interaction.user, sel.values[0]))

            sel.callback = cb
            self.add_item(sel)
        self.add_item(BackButton("ئەنیمییەکان", direct_anime_screen))


def direct_char_screen(user, char_id):
    char = find_char(char_id)
    if not char:
        return err_embed("nochar"), OwnedView(user)
    r = rarity_info(char["rarity"])
    preview = {
        "character_name": char["name"], "anime_title": char["anime"], "rarity": char["rarity"],
        "level": 1, "power": r["base_power"], "image_url": char_image(char["id"], 1),
    }
    e = card_embed(preview, title=f"🔍  {char['name']}",
                   extra=[("💰 نرخ", money(r["direct_buy_cost"]), True),
                          ("💳 باڵانسی تۆ", money(get_balance(user.id)), True)])
    return e, DirectBuyView(user, char)


class DirectBuyView(OwnedView):
    def __init__(self, user, char):
        super().__init__(user)
        self.char = char
        self.add_item(BackButton("کاراکتەرەکان", lambda u: direct_chars_screen(u, char["anime"])))

    @discord.ui.button(label="کڕینی ئەم کارتە", emoji="🛒", style=discord.ButtonStyle.success)
    async def buy(self, interaction, button):
        card, err = buy_direct(interaction.user.id, self.char["id"])
        back = DirectBuyView(self.user, self.char)
        if err:
            return await go(interaction, (err_embed(err), back))
        cost = rarity_info(card["rarity"])["direct_buy_cost"]
        e = card_embed(card, title=f"🎉  {card['character_name']} کڕدرا!",
                       lead=f"💰 تێچوو: {money(cost)}")
        await go(interaction, (e, back))
        pub = card_embed(card, title=f"🛒  {interaction.user.display_name} کارتێکی کڕی!",
                         lead=f"{interaction.user.mention} کارتی **{card['character_name']}** کڕی!", show_upgrade=False)
        await announce(interaction, pub)


# ═══════════════════════════════════════
# بەشی ٩: 📚 کارتەکانم
# ═══════════════════════════════════════
def mycards_screen(user):
    cards = fetch_cards(user.id)
    if not cards:
        e = mk("📚  کارتەکانم", f"هێشتا هیچ کارتێکت نییە!\nلە 📦 **سندوقەکان** یان 💳 **کڕینی ڕاستەوخۆ** دەست پێ بکە (`{PREFIX} cards`).", BLUE)
        return e, OwnedView(user)
    listed = listed_ids(user.id)
    lines = []
    for c in cards:
        r = rarity_info(c["rarity"])
        tag = " 🏪" if c["card_id"] in listed else ""
        lines.append(f"`#{c['card_id']}` {r['emoji']} **{c['character_name']}**  ·  Lvl {c['level']}  ·  ⚔️ `{c['power']:,}`{tag}")
    total_power = sum(c["power"] for c in cards)
    e = mk(f"📚  کارتەکانی {user.display_name}  ({len(cards)}/{MAX_CARDS_LIMIT})", "\n".join(lines), BLUE)
    e.add_field(name="⚔️ کۆی هێز", value=f"**{total_power:,}** PL", inline=True)
    e.add_field(name="💡 ئامۆژگاری", value="کارتێک هەڵبژێرە بۆ بەهێزکردن، بەخشین، فرۆشتن...", inline=True)
    e.set_thumbnail(url=cards[0]["image_url"] or DEFAULT_IMAGE)
    return e, MyCardsView(user, cards)


class MyCardsView(OwnedView):
    def __init__(self, user, cards):
        super().__init__(user)
        options = [
            discord.SelectOption(label=f"{c['character_name']} (Lvl {c['level']})"[:100], value=str(c["card_id"]),
                                 emoji=rarity_info(c["rarity"])["emoji"],
                                 description=f"PL: {c['power']:,} | {c['rarity']}")
            for c in cards[:25]
        ]
        sel = discord.ui.Select(placeholder="🎴 کارتێک هەڵبژێرە...", options=options)

        async def cb(interaction):
            await go(interaction, card_screen(interaction.user, int(sel.values[0])))

        sel.callback = cb
        self.add_item(sel)


def card_screen(user, card_id):
    card = fetch_card(card_id)
    if not card or card["user_id"] != user.id:
        return err_embed("missing"), _back_to_cards_view(user)
    listing = listing_for_card(card_id)
    return card_embed(card, listing=listing), CardActionView(user, card, listing)


def _back_to_cards_view(user):
    v = OwnedView(user)
    v.add_item(BackButton("کارتەکانم", mycards_screen))
    return v


class SellModal(discord.ui.Modal, title="🏪 نرخی فرۆشتن"):
    price = discord.ui.TextInput(label="نرخ (zero coin)", placeholder="نموونە: 500000", min_length=1, max_length=15)

    def __init__(self, user, card_id):
        super().__init__()
        self.user = user
        self.card_id = card_id

    async def on_submit(self, interaction):
        raw = self.price.value.replace(",", "").strip()
        if not raw.isdigit():
            return await interaction.response.send_message(embed=err_embed("bad_price"), ephemeral=True)
        card, err = list_card(interaction.user.id, self.card_id, int(raw))
        if err:
            return await interaction.response.send_message(embed=err_embed(err), ephemeral=True)
        await go(interaction, card_screen(interaction.user, self.card_id))


class CardActionView(OwnedView):
    def __init__(self, user, card, listing):
        super().__init__(user)
        self.card = card
        self.listing = listing
        level = card["level"]
        if listing:
            for b in (self.upgrade_btn, self.gift_btn, self.delete_btn):
                b.disabled = True
            self.sell_btn.label = "لابردن لە مارکێت"
            self.sell_btn.emoji = "❌"
            self.sell_btn.style = discord.ButtonStyle.secondary
        if level >= MAX_LEVEL:
            self.upgrade_btn.disabled = True
            self.upgrade_btn.label = "لوتکەی هێز (Max)"
        else:
            self.upgrade_btn.label = f"بەهێزکردن → Lvl {level + 1} ({UPGRADE_COSTS[level]:,})"
        self.add_item(BackButton("کارتەکانم", mycards_screen, row=2))

    @discord.ui.button(label="بەهێزکردن", emoji="⬆️", style=discord.ButtonStyle.success, row=0)
    async def upgrade_btn(self, interaction, button):
        card, err, cost = upgrade_card(interaction.user.id, self.card["card_id"])
        if err == "no_money":
            return await interaction.response.send_message(f"❌ پێویستت بە {money(cost)} هەیە بۆ ئەم بەهێزکردنە!", ephemeral=True)
        if err:
            return await interaction.response.send_message(embed=err_embed(err), ephemeral=True)
        e = card_embed(card, title=f"⚡  {card['character_name']} بەهێزکرا!  ⚡", lead=f"💰 تێچوو: {money(cost)}")
        await go(interaction, (e, CardActionView(self.user, card, None)))
        pub = card_embed(card, title=f"⚡  {interaction.user.display_name} کارتێکی بەهێز کرد!",
                         lead=f"🔥 {interaction.user.mention} کارتی **{card['character_name']}** گەیاندە **Lvl {card['level']}**!",
                         show_upgrade=False)
        await announce(interaction, pub)

    @discord.ui.button(label="پیشاندان لە چات", emoji="👁️", style=discord.ButtonStyle.secondary, row=0)
    async def show_btn(self, interaction, button):
        card = fetch_card(self.card["card_id"])
        if not card or card["user_id"] != interaction.user.id:
            return await interaction.response.send_message(embed=err_embed("missing"), ephemeral=True)
        pub = card_embed(card, title=f"✨  کارتی {interaction.user.display_name}", show_upgrade=False)
        try:
            await interaction.channel.send(embed=pub)
        except (discord.HTTPException, AttributeError):
            return await interaction.response.send_message("❌ بۆتەکە ناتوانێت لەم چاتە بنووسێت!", ephemeral=True)
        await interaction.response.send_message("✅ کارتەکەت لە چات پیشان درا!", ephemeral=True)

    @discord.ui.button(label="فرۆشتن لە مارکێت", emoji="🏪", style=discord.ButtonStyle.primary, row=1)
    async def sell_btn(self, interaction, button):
        if self.listing:
            unlist_card(interaction.user.id, self.card["card_id"])
            return await go(interaction, card_screen(interaction.user, self.card["card_id"]))
        await interaction.response.send_modal(SellModal(interaction.user, self.card["card_id"]))

    @discord.ui.button(label="بەخشین", emoji="🎁", style=discord.ButtonStyle.primary, row=1)
    async def gift_btn(self, interaction, button):
        e = mk("🎁  بەخشینی کارت", f"کارتی **{self.card['character_name']}** (`#{self.card['card_id']}`) بدە بە هاوڕێیەک:", GOLD)
        await go(interaction, (e, GiftView(self.user, self.card["card_id"])))

    @discord.ui.button(label="سڕینەوە", emoji="🗑️", style=discord.ButtonStyle.danger, row=1)
    async def delete_btn(self, interaction, button):
        e = mk("🗑️  دڵنیایت؟", f"کارتی **{self.card['character_name']}** (`#{self.card['card_id']}`) بە تەواوی دەسڕدرێتەوە و ناگەڕێتەوە!", ERROR)
        await go(interaction, (e, DeleteConfirmView(self.user, self.card["card_id"])))


class GiftView(OwnedView):
    def __init__(self, user, card_id):
        super().__init__(user, timeout=90)
        self.card_id = card_id
        self.add_item(BackButton("گەڕانەوە", lambda u: card_screen(u, card_id), row=1))

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="👤 هاوڕێیەک هەڵبژێرە...", row=0)
    async def pick(self, interaction, select):
        target = select.values[0]
        card, err = gift_card(interaction.user.id, target, self.card_id)
        if err:
            return await interaction.response.send_message(embed=err_embed(err), ephemeral=True)
        e = mk("🎁  پیرۆزە! کارتەکە بەخشرا", f"کارتی **{card['character_name']}** (`#{card['card_id']}`) درا بە {target.mention}!", SUCCESS)
        await go(interaction, (e, _back_to_cards_view(self.user)))
        pub = mk("🎁  دیاری!", f"{interaction.user.mention} کارتی **{card['character_name']}** بەخشی بە {target.mention} 💝", GOLD)
        await announce(interaction, pub)


class DeleteConfirmView(OwnedView):
    def __init__(self, user, card_id):
        super().__init__(user, timeout=30)
        self.card_id = card_id

    @discord.ui.button(label="بەڵێ، بیسڕەوە", emoji="🗑️", style=discord.ButtonStyle.danger)
    async def yes(self, interaction, button):
        card, err = delete_card(interaction.user.id, self.card_id)
        if err:
            return await go(interaction, (err_embed(err), _back_to_cards_view(self.user)))
        e = mk("🗑️  سڕایەوە", f"کارتی **{card['character_name']}** (`#{card['card_id']}`) سڕایەوە و شوێنێکی بەتاڵ بوو.", SUCCESS)
        await go(interaction, (e, _back_to_cards_view(self.user)))

    @discord.ui.button(label="نەخێر", emoji="↩️", style=discord.ButtonStyle.secondary)
    async def no(self, interaction, button):
        await go(interaction, card_screen(interaction.user, self.card_id))


# ═══════════════════════════════════════
# بەشی ١٠: 🏪 مارکێتی یاریزانان
# ═══════════════════════════════════════
def market_screen(user):
    rows = market_rows()
    e = mk("🏪  مارکێتی کارتەکان", None, ORANGE)
    if rows:
        lines = []
        for r in rows:
            ri = rarity_info(r["rarity"])
            mine = " ← *هی تۆیە*" if r["seller_id"] == user.id else ""
            lines.append(f"`#{r['m_id']}` {ri['emoji']} **{r['character_name']}** · Lvl {r['level']} · ⚔️ `{r['power']:,}` · {money(r['price'])}{mine}")
        e.description = "\n".join(lines) + "\n\nکارتێک هەڵبژێرە بۆ بینین و کڕین:"
    else:
        e.description = "ℹ️ هیچ کارتێک لە مارکێتدا نییە!"
    e.add_field(
        name="📌 فەرمانەکان",
        value=f"`{PREFIX} cardsell <card_id> <نرخ>`  ─  فرۆشتن\n`{PREFIX} buycard <market_id>`  ─  کڕین\n`{PREFIX} cardunsell <card_id>`  ─  لابردن",
        inline=False,
    )
    return e, MarketView(user, rows)


class MarketView(OwnedView):
    def __init__(self, user, rows):
        super().__init__(user)
        if rows:
            options = [
                discord.SelectOption(label=f"{r['character_name']} (Lvl {r['level']})"[:100], value=str(r["m_id"]),
                                     emoji=rarity_info(r["rarity"])["emoji"],
                                     description=f"{r['price']:,} • PL {r['power']:,}")
                for r in rows[:25]
            ]
            sel = discord.ui.Select(placeholder="🛒 کارتێک هەڵبژێرە...", options=options)

            async def cb(interaction):
                await go(interaction, listing_screen(interaction.user, int(sel.values[0])))

            sel.callback = cb
            self.add_item(sel)

    @discord.ui.button(label="نوێکردنەوە", emoji="🔄", style=discord.ButtonStyle.secondary)
    async def refresh(self, interaction, button):
        await go(interaction, market_screen(interaction.user))


def listing_screen(user, m_id):
    row = market_row(m_id)
    if not row:
        v = OwnedView(user)
        v.add_item(BackButton("مارکێت", market_screen))
        return err_embed("gone"), v
    e = card_embed(row, title=f"🏪  {row['character_name']}", show_upgrade=False,
                   extra=[("💰 نرخ", money(row["price"]), True), ("👤 فرۆشیار", f"<@{row['seller_id']}>", True),
                          ("🆔 مارکێت", f"`#{row['m_id']}`", True)])
    return e, ListingView(user, row)


class ListingView(OwnedView):
    def __init__(self, user, row):
        super().__init__(user)
        self.row = row
        if row["seller_id"] == user.id:
            btn = discord.ui.Button(label="لابردن لە مارکێت", emoji="❌", style=discord.ButtonStyle.danger)

            async def cancel_cb(interaction):
                unlist_card(interaction.user.id, self.row["card_id"])
                await go(interaction, market_screen(interaction.user))

            btn.callback = cancel_cb
        else:
            btn = discord.ui.Button(label=f"کڕین ({row['price']:,})", emoji="🛒", style=discord.ButtonStyle.success)

            async def buy_cb(interaction):
                await _do_buy(interaction, self.row["m_id"])

            btn.callback = buy_cb
        self.add_item(btn)
        self.add_item(BackButton("مارکێت", market_screen))


async def _do_buy(interaction, m_id):
    row, err = buy_listing(interaction.user.id, m_id)
    back = OwnedView(interaction.user)
    back.add_item(BackButton("مارکێت", market_screen))
    if err:
        return await go(interaction, (err_embed(err), back))
    card = fetch_card(row["card_id"])
    e = card_embed(card, title=f"🎉  {card['character_name']} کڕدرا!", lead=f"💰 تێچوو: {money(row['price'])}")
    await go(interaction, (e, back))
    pub = mk("🏪  مامەڵەی مارکێت", f"{interaction.user.mention} کارتی **{card['character_name']}** کڕی لە <@{row['seller_id']}> بە {money(row['price'])}!", ORANGE)
    await announce(interaction, pub)


# ═══════════════════════════════════════
# بەشی ١١: فەرمانەکان
# ═══════════════════════════════════════
class Cards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cards", aliases=["card", "gacha", "کارت"])
    async def cards_menu(self, ctx):
        """مێنیوی سەرەکی کارتەکان"""
        embed, view = hub_screen(ctx.author)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(name="pull", aliases=["ڕاکێشان"])
    async def pull_cmd(self, ctx):
        """فرۆشگای سندوقەکان"""
        embed, view = chests_screen(ctx.author)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="mycards", aliases=["mc", "کارتەکانم"])
    async def mycards_cmd(self, ctx):
        """کارتەکانی خۆت"""
        embed, view = mycards_screen(ctx.author)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="showcard", aliases=["scard", "پیشاندانی_کارت"])
    async def showcard_cmd(self, ctx, card_id: int = None):
        """پیشاندانی کارتێکی خۆت لە چات"""
        if card_id is None:
            return await ctx.send(f"❌ بەکارهێنان: `{PREFIX} showcard <card_id>`")
        card = fetch_card(card_id)
        if not card or card["user_id"] != ctx.author.id:
            return await ctx.send(embed=err_embed("missing"))
        await ctx.send(embed=card_embed(card, title=f"✨  کارتی {ctx.author.display_name}",
                                        listing=listing_for_card(card_id), show_upgrade=False))

    @commands.command(name="cardmarket", aliases=["cmarket", "cm"])
    async def cardmarket_cmd(self, ctx):
        """مارکێتی کارتەکان"""
        embed, view = market_screen(ctx.author)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="cardsell", aliases=["csell"])
    async def cardsell_cmd(self, ctx, card_id: int = None, price: int = None):
        """فرۆشتنی کارت لە مارکێت"""
        if card_id is None or price is None:
            return await ctx.send(f"❌ بەکارهێنان: `{PREFIX} cardsell <card_id> <نرخ>`")
        card, err = list_card(ctx.author.id, card_id, price)
        if err:
            return await ctx.send(embed=err_embed(err))
        await ctx.send(embed=mk("🏪  خرایە مارکێتەوە",
                                f"کارتی **{card['character_name']}** (`#{card_id}`) بە {money(price)} خرایە مارکێتەوە!", SUCCESS))

    @commands.command(name="cardunsell", aliases=["cunsell"])
    async def cardunsell_cmd(self, ctx, card_id: int = None):
        """لابردنی کارت لە مارکێت"""
        if card_id is None:
            return await ctx.send(f"❌ بەکارهێنان: `{PREFIX} cardunsell <card_id>`")
        if unlist_card(ctx.author.id, card_id):
            await ctx.send(embed=mk("✅  لابرا", f"کارتی `#{card_id}` لە مارکێت لابرا.", SUCCESS))
        else:
            await ctx.send(embed=mk("❌ هەڵە", "ئەم کارتە لە مارکێتی تۆدا نییە!", ERROR))

    @commands.command(name="buycard", aliases=["cbuy"])
    async def buycard_cmd(self, ctx, market_id: int = None):
        """کڕینی کارت لە مارکێت"""
        if market_id is None:
            return await ctx.send(f"❌ بەکارهێنان: `{PREFIX} buycard <market_id>`")
        row, err = buy_listing(ctx.author.id, market_id)
        if err:
            return await ctx.send(embed=err_embed(err))
        card = fetch_card(row["card_id"])
        await ctx.send(embed=card_embed(card, title=f"🎉  {card['character_name']} کڕدرا!",
                                        lead=f"{ctx.author.mention} بە {money(row['price'])} کڕی لە <@{row['seller_id']}>"))


async def setup(bot):
    await bot.add_cog(Cards(bot))
