"""
داتای کارتەکان — لێرە هەموو شتێک دەگۆڕیت (کاراکتەر، جۆر، سندوق، نرخ).
ئەم فایلە دەبێت لە فۆڵدەری سەرەکی بێت (لەتەنیشت bot.py و database.py).

⚠️ تێبینی گرنگ:
  • وێنەکان (GIF) لێرە هەموویان وێنەیەکی کاتین (DEFAULT_IMAGE).
    لینکی GIFی ڕاستەقینە بۆ هەر کاراکتەرێک لە image_lvl1 / image_lvl2 / image_lvl3 دابنێ.
    باشترین ڕێگا: GIF لە GitHub بار بکە و لینکی raw بەکاربهێنە، چونکە لینکی Discord CDN کاتییە.
  • نرخ و هێزی خوارەوە ژمارەی پێشنیارکراون، بە ئارەزووی خۆت بیانگۆڕە.
  • لە Discord هەر ئەنیمییەک دەبێت زیاتر نەبێت لە ٢٥ کاراکتەر، و ئەنیمییەکان زیاتر نەبن لە ٢٥.
"""

DEFAULT_IMAGE = "https://i.giphy.com/media/C3brYLms1bhv2/giphy.gif"

# ═══════════════════════════════════════
# جۆرەکان (Rarity)
# emoji: ئیمۆجی | color: ڕەنگی کارت | stars: ژمارەی ئەستێرە (١ تا ٥)
# base_power: هێزی سەرەتایی (Lvl 1) | direct_buy_cost: نرخی کڕینی ڕاستەوخۆ
# ═══════════════════════════════════════
RARITY_CONFIG = {
    "Common":    {"emoji": "⚪", "color": 0x95A5A6, "stars": 1, "base_power": 1_000,  "direct_buy_cost": 100_000},
    "Rare":      {"emoji": "🔵", "color": 0x3498DB, "stars": 2, "base_power": 2_500,  "direct_buy_cost": 300_000},
    "Epic":      {"emoji": "🟣", "color": 0x9B59B6, "stars": 3, "base_power": 5_000,  "direct_buy_cost": 800_000},
    "Legendary": {"emoji": "🟡", "color": 0xF1C40F, "stars": 4, "base_power": 9_000,  "direct_buy_cost": 2_500_000},
    "Mythic":    {"emoji": "🔴", "color": 0xE74C3C, "stars": 5, "base_power": 15_000, "direct_buy_cost": 6_000_000},
}

# ═══════════════════════════════════════
# سندوقەکان
# odds: ڕێژەی دەرچوونی هەر جۆرێک (کۆکراوەکەیان دەبێت ١٠٠ بێت)
# ═══════════════════════════════════════
CHEST_CONFIG = {
    "Bronze": {
        "name": "Bronze Chest", "emoji": "🥉", "cost": 50_000, "color": 0xCD7F32,
        "odds": {"Common": 70, "Rare": 25, "Epic": 5},
    },
    "Gold": {
        "name": "Gold Chest", "emoji": "🥇", "cost": 150_000, "color": 0xF1C40F,
        "odds": {"Common": 40, "Rare": 40, "Epic": 17, "Legendary": 3},
    },
    "Diamond": {
        "name": "Diamond Chest", "emoji": "💎", "cost": 500_000, "color": 0x1ABC9C,
        "odds": {"Rare": 40, "Epic": 45, "Legendary": 14, "Mythic": 1},
    },
    "Legendary": {
        "name": "Legendary Chest", "emoji": "👑", "cost": 1_200_000, "color": 0xE74C3C,
        "odds": {"Epic": 50, "Legendary": 44, "Mythic": 6},
    },
}


# ═══════════════════════════════════════
# کاراکتەرەکان
# _c(id, ناو, ئەنیمی, جۆر, وێنەی Lvl1, وێنەی Lvl2, وێنەی Lvl3)
# id دەبێت بێ هاوتا بێت. وێنە نەنووسرا = DEFAULT_IMAGE
# ═══════════════════════════════════════
def _c(cid, name, anime, rarity, img1=None, img2=None, img3=None):
    img1 = img1 or DEFAULT_IMAGE
    return {
        "id": cid, "name": name, "anime": anime, "rarity": rarity,
        "image_lvl1": img1,
        "image_lvl2": img2 or img1,
        "image_lvl3": img3 or img2 or img1,
    }


ANIME_CHARACTERS = [
    # ── Naruto ──
    _c("naruto_uzumaki",  "Naruto Uzumaki",  "Naruto", "Epic"),
    _c("sasuke_uchiha",   "Sasuke Uchiha",   "Naruto", "Epic"),
    _c("itachi_uchiha",   "Itachi Uchiha",   "Naruto", "Legendary"),
    _c("kakashi_hatake",  "Kakashi Hatake",  "Naruto", "Rare"),
    _c("sakura_haruno",   "Sakura Haruno",   "Naruto", "Common"),

    # ── One Piece ──
    _c("luffy",           "Monkey D. Luffy", "One Piece", "Legendary"),
    _c("zoro",            "Roronoa Zoro",    "One Piece", "Epic"),
    _c("ace",             "Portgas D. Ace",  "One Piece", "Epic"),
    _c("sanji",           "Sanji",           "One Piece", "Rare"),
    _c("nami",            "Nami",            "One Piece", "Common"),

    # ── Dragon Ball ──
    _c("goku",            "Goku",            "Dragon Ball", "Mythic"),
    _c("vegeta",          "Vegeta",          "Dragon Ball", "Legendary"),
    _c("gohan",           "Gohan",           "Dragon Ball", "Epic"),
    _c("piccolo",         "Piccolo",         "Dragon Ball", "Rare"),
    _c("krillin",         "Krillin",         "Dragon Ball", "Common"),

    # ── Attack on Titan ──
    _c("levi",            "Levi Ackerman",   "Attack on Titan", "Legendary"),
    _c("eren",            "Eren Yeager",     "Attack on Titan", "Epic"),
    _c("mikasa",          "Mikasa Ackerman", "Attack on Titan", "Rare"),
    _c("armin",           "Armin Arlert",    "Attack on Titan", "Common"),

    # ── Demon Slayer ──
    _c("rengoku",         "Kyojuro Rengoku", "Demon Slayer", "Legendary"),
    _c("nezuko",          "Nezuko Kamado",   "Demon Slayer", "Epic"),
    _c("tanjiro",         "Tanjiro Kamado",  "Demon Slayer", "Rare"),
    _c("zenitsu",         "Zenitsu Agatsuma", "Demon Slayer", "Common"),

    # ── Jujutsu Kaisen ──
    _c("gojo",            "Satoru Gojo",     "Jujutsu Kaisen", "Mythic"),
    _c("sukuna",          "Ryomen Sukuna",   "Jujutsu Kaisen", "Legendary"),
    _c("megumi",          "Megumi Fushiguro", "Jujutsu Kaisen", "Epic"),
    _c("yuji",            "Yuji Itadori",    "Jujutsu Kaisen", "Rare"),
    _c("nobara",          "Nobara Kugisaki", "Jujutsu Kaisen", "Common"),
]
