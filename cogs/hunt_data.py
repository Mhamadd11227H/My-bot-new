"""
ZERO HUNT — هەموو داتا و ڕێکخستنەکان لێرەن.
بۆ زیادکردنی ئاژەڵی نوێ: تەنها دێڕێکی نوێ لە ANIMAL_LIST زیاد بکە. هیچ کۆدێکی تر نابێت بگۆڕدرێت.
"""

# ═══════════════════════════════════════
# بەشی ١: ڕێکخستنی گشتی
# ═══════════════════════════════════════
HUNT_COST = 10            # نرخی هەر hunt (بە zero coin)
HUNT_COOLDOWN = 15        # چرکە
LOOTBOX_EVERY = 25        # هەر چەند hunt جارێک lootbox ێک دەدرێت
DAILY_BOX_TARGET = 3      # ئامانجی lootbox ی ڕۆژانە (checklist)
CHECKLIST_REWARD = 2500   # پاداشتی تەواوکردنی checklist
PAGE_SIZE = 10            # ژمارەی ئاژەڵ لە هەر پەڕەیەکی zoo
MAX_TEAM = 3
MAX_PET_LEVEL = 50
XP_BASE = 100             # xp بۆ ئاستی L+1 = XP_BASE * L^2
LEVEL_REWARD_PER_LEVEL = 50   # دراو بۆ هەر ئاستێک (level * 50)
LEVEL_BOX_EVERY = 10          # هەر ١٠ ئاست lootbox ی rare
MAX_BUFF_SECONDS = 24 * 3600
MAX_LUCK = 1.5            # زۆرترین luck (٪١٥٠). لەوە زیاتر کۆی ppm لە ١٠٠٪ تێدەپەڕێت
PITY_ENABLED = False      # pity ناچالاکە (ئەگەر ئەدمین بیەوێت)

# ═══════════════════════════════════════
# بەشی ٢: rarity ەکان
# ppm = بەشی لە ١,٠٠٠,٠٠٠ (٪١٠٠ = ١٠٠٠٠٠٠). کۆی pool ی main دەبێت وردەکاری ١٠٠٪ بێت
# pool: main (hunt)، event (تەنها لە event)، huntbot (radar)، none (تەنها ئەدمین)
# ═══════════════════════════════════════
RARITIES = {
    "common":         dict(name="Common",         ppm=600_000, xp=1,       sell=1,      essence=1,    zoo=1,       color=0x95A5A6, emoji="⚪", pool="main",    effect="",                              avail="Hunt"),
    "uncommon":       dict(name="Uncommon",       ppm=250_000, xp=10,      sell=3,      essence=3,    zoo=5,       color=0x2ECC71, emoji="🟢", pool="main",    effect="",                              avail="Hunt"),
    "rare":           dict(name="Rare",           ppm=100_000, xp=20,      sell=10,     essence=8,    zoo=20,      color=0x3498DB, emoji="🔵", pool="main",    effect="",                              avail="Hunt"),
    "epic":           dict(name="Epic",           ppm=35_000,  xp=400,     sell=50,     essence=20,   zoo=250,     color=0x9B59B6, emoji="🟣", pool="main",    effect="💜 Epic find!",                 avail="Hunt"),
    "mythical":       dict(name="Mythical",       ppm=10_000,  xp=1000,    sell=120,    essence=60,   zoo=500,     color=0xE74C3C, emoji="🔴", pool="main",    effect="🔥 Mythical find!",             avail="Hunt"),
    "patreon":        dict(name="Patreon",        ppm=0,       xp=400,     sell=100,    essence=50,   zoo=250,     color=0xF39C12, emoji="🧡", pool="none",    effect="🧡 Supporter exclusive",        avail="Admin"),
    "special":        dict(name="Special",        ppm=0,       xp=1000,    sell=300,    essence=100,  zoo=1000,    color=0x1ABC9C, emoji="⭐", pool="event",   effect="⭐ Event exclusive!",           avail="Events"),
    "legendary":      dict(name="Legendary",      ppm=4_000,   xp=2000,    sell=350,    essence=150,  zoo=2000,    color=0xFFC700, emoji="🟡", pool="main",    effect="🌟 LEGENDARY CATCH!",           avail="Hunt"),
    "gem":            dict(name="Gem",            ppm=900,     xp=5000,    sell=900,    essence=400,  zoo=5000,    color=0x00E5FF, emoji="💎", pool="main",    effect="💎 GEM-TIER CATCH!",            avail="Hunt"),
    "custom_patreon": dict(name="Custom Patreon", ppm=0,       xp=400,     sell=150,    essence=80,   zoo=500,     color=0xFF69B4, emoji="🩷", pool="none",    effect="🩷 Custom supporter pet",       avail="Admin"),
    "bot":            dict(name="Bot",            ppm=0,       xp=50,      sell=80,     essence=100,  zoo=50,      color=0x7289DA, emoji="🤖", pool="huntbot", effect="🤖 Found by your Huntbot",     avail="Huntbot radar"),
    "distorted":      dict(name="Distorted",      ppm=0,       xp=100_000, sell=2500,   essence=2000, zoo=50_000,  color=0xFF00FF, emoji="👾", pool="event",   effect="👾 R̸E̸A̸L̸I̸T̸Y̸ ̸G̸L̸I̸T̸C̸H̸",   avail="Lucky event"),
    "fabled":         dict(name="Fabled",         ppm=90,      xp=100_000, sell=8000,   essence=3000, zoo=100_000, color=0xFF6EC7, emoji="🌠", pool="main",    effect="🌠 F A B L E D !!",             avail="Hunt"),
    "hidden":         dict(name="Hidden",         ppm=10,      xp=300_000, sell=15000,  essence=8000, zoo=300_000, color=0x111111, emoji="⚫", pool="main",    effect="🕳️ A HIDDEN CREATURE REVEALED!", avail="Hunt"),
}
RARITY_ORDER = list(RARITIES)                       # ڕیزبەندی (کەم → زۆر دەگمەن)
RARITY_RANK = {k: i for i, k in enumerate(RARITY_ORDER)}
TOTAL_PPM = 1_000_000
assert sum(r["ppm"] for r in RARITIES.values() if r["pool"] == "main") == TOTAL_PPM, \
    "کۆی ppm ی rarity ەکانی main دەبێت ١٠٠٠٠٠٠ بێت (٪١٠٠)"

# ئەم rarity انە لە sell all / sacrifice all / sell <rarity> بە شێوەی بێ‌ئاگا ناگیرێن
PROTECTED_BULK = {"gem", "fabled", "hidden", "distorted", "special", "patreon", "custom_patreon", "bot"}
# ئەم rarity انە لە owodex دا بۆ ئەوەی نەدۆزرابنەوە ناوەکەیان نانیشان دەدرێت
SECRET_RARITIES = {"hidden", "distorted"}
# ئەم rarity انە هەمیشە دڵنیابوونەوە دەخوازن لە sell/sacrifice
CONFIRM_RARITIES = {"legendary", "gem", "fabled", "hidden", "distorted", "special", "patreon", "custom_patreon"}

# ═══════════════════════════════════════
# بەشی ٣: ئاژەڵەکان
# (ناو، ئیمۆجی، rarity، جۆر، وەسف، [event])
# ═══════════════════════════════════════
ANIMAL_LIST = [
    # ── Common ──
    ("Rabbit", "🐰", "common", "mammal", "A fluffy hopper that is always in a hurry."),
    ("Chick", "🐤", "common", "bird", "Tiny, yellow and very loud."),
    ("Chicken", "🐔", "common", "bird", "Lays eggs and judges you quietly."),
    ("Fish", "🐟", "common", "sea", "Swims in circles, happy anyway."),
    ("Snail", "🐌", "common", "insect", "Slow, steady and wearing its home."),
    ("Beetle", "🪲", "common", "insect", "A shiny little armored bug."),
    ("Shrimp", "🦐", "common", "sea", "Small, pink and surprisingly tasty."),
    ("Duck", "🦆", "common", "bird", "Quack. That is the whole personality."),
    ("Lizard", "🦎", "common", "reptile", "Loves sunbathing on warm rocks."),
    # ── Uncommon ──
    ("Dog", "🐶", "uncommon", "mammal", "Loyal to the end. Will fetch anything."),
    ("Cat", "🐱", "uncommon", "mammal", "Owns the house. Allows you to live there."),
    ("Sheep", "🐑", "uncommon", "mammal", "Counting these puts you to sleep."),
    ("Pig", "🐷", "uncommon", "mammal", "Smarter than it looks, and muddier too."),
    ("Cow", "🐮", "uncommon", "mammal", "Moo. Fresh milk delivery."),
    ("Crab", "🦀", "uncommon", "sea", "Walks sideways, pinches forward."),
    ("Bee", "🐝", "uncommon", "insect", "Busy all day, sweet results."),
    ("Dove", "🕊️", "uncommon", "bird", "A symbol of peace and quiet mornings."),
    ("Turtle", "🐢", "uncommon", "reptile", "Wins races by never giving up."),
    # ── Rare ──
    ("Fox", "🦊", "rare", "mammal", "Clever, quick and a little mischievous."),
    ("Deer", "🦌", "rare", "mammal", "Graceful walker of the misty forest."),
    ("Horse", "🐴", "rare", "mammal", "Fast, proud and free."),
    ("Monkey", "🐵", "rare", "mammal", "Swings through trees and through your bananas."),
    ("Butterfly", "🦋", "rare", "insect", "Wings painted by the morning sky."),
    ("Spider", "🕷️", "rare", "insect", "Eight legs, zero chill."),
    ("Squid", "🦑", "rare", "sea", "Squirts ink when startled."),
    ("Parrot", "🦜", "rare", "bird", "Repeats everything you say, loudly."),
    ("Snake", "🐍", "rare", "reptile", "Silent, smooth and slightly dramatic."),
    ("Camel", "🐪", "rare", "mammal", "Desert traveler with a built-in snack."),
    # ── Epic ──
    ("Wolf", "🐺", "epic", "mammal", "Leader of the pack, howls at the moon."),
    ("Owl", "🦉", "epic", "bird", "Sees everything in the dark."),
    ("Penguin", "🐧", "epic", "bird", "Dressed formally for every occasion."),
    ("Peacock", "🦚", "epic", "bird", "Lives for the spotlight."),
    ("Dolphin", "🐬", "epic", "sea", "Intelligent, playful and a great jumper."),
    ("Octopus", "🐙", "epic", "sea", "Eight arms, three hearts, endless tricks."),
    ("Crocodile", "🐊", "epic", "reptile", "An ancient predator with a big smile."),
    ("Gorilla", "🦍", "epic", "mammal", "Gentle giant, mighty chest."),
    # ── Mythical ──
    ("Lion", "🦁", "mythical", "mammal", "The king, and he knows it."),
    ("Tiger", "🐯", "mythical", "mammal", "Burning bright in the jungle night."),
    ("Bear", "🐻", "mythical", "mammal", "Strong, sleepy and fiercely protective."),
    ("Panda", "🐼", "mythical", "mammal", "Eats bamboo, wins hearts."),
    ("Shark", "🦈", "mythical", "sea", "Apex predator of the deep blue."),
    ("Eagle", "🦅", "mythical", "bird", "Rules the sky with a sharp gaze."),
    # ── Legendary ──
    ("Elephant", "🐘", "legendary", "mammal", "Never forgets, never stops."),
    ("Whale", "🐋", "legendary", "sea", "A song that crosses oceans."),
    ("Snowman", "⛄", "legendary", "fantasy", "Built from winter magic. Please keep it cold."),
    # ── Gem ──
    ("Dragon", "🐉", "gem", "fantasy", "Guards a mountain of shiny treasure."),
    ("Ghost", "👻", "gem", "fantasy", "Floats through walls and through hearts."),
    # ── Fabled ──
    ("Unicorn", "🦄", "fabled", "fantasy", "A horn of pure starlight. Almost never seen."),
    ("Phoenix", "🔥", "fabled", "fantasy", "Reborn from its own flames, every time."),
    # ── Hidden ──
    ("Shadow Cat", "🐈‍⬛", "hidden", "special", "Nobody has ever seen it arrive."),
    ("Zero Phantom", "🌌", "hidden", "special", "A creature from the space between the numbers."),
    # ── Bot (Huntbot radar) ──
    ("Robo Dog", "🤖", "bot", "robot", "Built by your Huntbot. Fetches data."),
    ("Robo Cat", "🦾", "bot", "robot", "Purrs in binary."),
    ("Zero Core", "🔋", "bot", "robot", "The glowing heart of the machine."),
    # ── Patreon / Custom (تەنها ئەدمین) ──
    ("Patron Cat", "🐈", "patreon", "special", "A thank-you from the Zero team."),
    ("Custom Companion", "💜", "custom_patreon", "special", "A personal pet for a special supporter."),
    # ── Event: Halloween ──
    ("Bat", "🦇", "special", "special", "Haunts the night of Halloween.", "halloween"),
    ("Pumpkin Cat", "🎃", "special", "special", "A cat with a very carved smile.", "halloween"),
    # ── Event: Christmas ──
    ("Reindeer", "🦌", "special", "special", "Pulls the sleigh through the snow.", "christmas"),
    ("Santa Penguin", "🎅", "special", "special", "Delivers fish to every house.", "christmas"),
    # ── Event: Easter ──
    ("Easter Chick", "🐣", "special", "special", "Just hatched from a colorful egg.", "easter"),
    ("Egg Bunny", "🐇", "special", "special", "Hides eggs in impossible places.", "easter"),
    # ── Event: Legendary Hunting ──
    ("Golden Lion", "🏆", "special", "special", "A champion of the legendary hunt.", "legendary_hunt"),
    # ── Event: Lucky (distorted) ──
    ("Glitch Wolf", "👾", "distorted", "special", "Part wolf, part error message.", "lucky"),
    ("Glitch Dragon", "🧬", "distorted", "special", "Its code is rewriting itself.", "lucky"),
]

# ═══════════════════════════════════════
# بەشی ٤: gem ەکان (ئەدمین دەتوانێت بە z hgem بیانگۆڕێت)
# ═══════════════════════════════════════
GEMS = {
    "common":    dict(name="Common Gem",    emoji="💚", animals=1, durability=25),
    "uncommon":  dict(name="Uncommon Gem",  emoji="💙", animals=3, durability=25),
    "rare":      dict(name="Rare Gem",      emoji="💜", animals=4, durability=50),
    "epic":      dict(name="Epic Gem",      emoji="🧡", animals=5, durability=75),
    "mythical":  dict(name="Mythical Gem",  emoji="❤️", animals=6, durability=75),
    "legendary": dict(name="Legendary Gem", emoji="💛", animals=7, durability=100),
    "fabled":    dict(name="Fabled Gem",    emoji="🤍", animals=9, durability=100),
}

# ═══════════════════════════════════════
# بەشی ٥: ئایتم و buff
# kind: luck / xp / essence / catch / discount / lure_<category>
# strength: luck/xp/essence = +٪ (0.5 = +50%)، catch = ئاژەڵی زیاتر، discount = کەمکردنەوەی نرخ، lure = ×(1+strength) بۆ جۆرەکە
# ═══════════════════════════════════════
ITEMS = {
    "luck_potion":     dict(name="Luck Potion",     emoji="🍀", kind="luck",     strength=0.5, duration=3600, desc="+50% rare chance for 1h"),
    "mega_luck":       dict(name="Mega Luck Potion", emoji="🌈", kind="luck",    strength=1.5, duration=1800, desc="+150% rare chance for 30m"),
    "xp_potion":       dict(name="XP Potion",       emoji="🧪", kind="xp",       strength=1.0, duration=1800, desc="+100% pet XP for 30m"),
    "essence_potion":  dict(name="Essence Potion",  emoji="⚗️", kind="essence",  strength=0.5, duration=3600, desc="+50% essence for 1h"),
    "catch_charm":     dict(name="Catch Charm",     emoji="🎣", kind="catch",    strength=1,   duration=1800, desc="+1 animal per hunt for 30m"),
    "discount_ticket": dict(name="Discount Ticket", emoji="🎟️", kind="discount", strength=0.5, duration=1800, desc="-50% hunt cost for 30m"),
    "lure_mammal":     dict(name="Mammal Lure",     emoji="🥩", kind="lure_mammal",  strength=3, duration=3600, desc="Attracts mammals (x4) for 1h"),
    "lure_bird":       dict(name="Bird Lure",       emoji="🌾", kind="lure_bird",    strength=3, duration=3600, desc="Attracts birds (x4) for 1h"),
    "lure_sea":        dict(name="Sea Lure",        emoji="🪱", kind="lure_sea",     strength=3, duration=3600, desc="Attracts sea animals (x4) for 1h"),
    "lure_reptile":    dict(name="Reptile Lure",    emoji="🦗", kind="lure_reptile", strength=3, duration=3600, desc="Attracts reptiles (x4) for 1h"),
    "lure_insect":     dict(name="Insect Lure",     emoji="🍯", kind="lure_insect",  strength=3, duration=3600, desc="Attracts insects (x4) for 1h"),
    "lure_fantasy":    dict(name="Fantasy Lure",    emoji="✨", kind="lure_fantasy", strength=3, duration=3600, desc="Attracts fantasy creatures (x4) for 1h"),
}
LURE_CATEGORIES = ("mammal", "bird", "sea", "reptile", "insect", "fantasy")

# ═══════════════════════════════════════
# بەشی ٦: lootbox ەکان
# type: coins / essence / gem / item / animal
# ═══════════════════════════════════════
_CONSUMABLES = ["luck_potion", "xp_potion", "essence_potion", "catch_charm", "discount_ticket",
                "lure_mammal", "lure_bird", "lure_sea", "lure_reptile", "lure_insect", "lure_fantasy"]
BOXES = {
    "common": dict(name="Lootbox", emoji="📦", color=0x95A5A6, rewards=[
        dict(type="coins", weight=35, min=200, max=800),
        dict(type="essence", weight=20, min=10, max=50),
        dict(type="item", weight=18, keys=_CONSUMABLES),
        dict(type="gem", weight=17, tiers={"common": 60, "uncommon": 30, "rare": 10}),
        dict(type="animal", weight=10, rarities={"rare": 100}),
    ]),
    "rare": dict(name="Rare Lootbox", emoji="🎁", color=0x3498DB, rewards=[
        dict(type="coins", weight=25, min=1000, max=4000),
        dict(type="essence", weight=20, min=50, max=200),
        dict(type="item", weight=15, keys=_CONSUMABLES + ["mega_luck"]),
        dict(type="gem", weight=25, tiers={"common": 20, "uncommon": 30, "rare": 30, "epic": 15, "mythical": 5}),
        dict(type="animal", weight=15, rarities={"epic": 100}),
    ]),
    "epic": dict(name="Epic Lootbox", emoji="👑", color=0x9B59B6, rewards=[
        dict(type="coins", weight=15, min=5000, max=20000),
        dict(type="essence", weight=15, min=300, max=1000),
        dict(type="item", weight=10, keys=["mega_luck", "xp_potion", "catch_charm", "essence_potion"]),
        dict(type="gem", weight=40, tiers={"rare": 20, "epic": 35, "mythical": 25, "legendary": 15, "fabled": 5}),
        dict(type="animal", weight=20, rarities={"mythical": 85, "legendary": 15}),
    ]),
}

# ═══════════════════════════════════════
# بەشی ٧: event ەکان (ئەدمین بە z hevent دەیانکاتەوە)
# animal_chance: ئەگەری ئەوەی هەر ئاژەڵێکی hunt بە ئاژەڵی event بگۆڕدرێت
# ═══════════════════════════════════════
EVENTS = {
    "halloween":      dict(name="Halloween Event",       emoji="🎃", animal_chance=0.04, luck=0.0, xp=0.0, desc="Spooky exclusive animals!"),
    "christmas":      dict(name="Christmas Event",       emoji="🎄", animal_chance=0.04, luck=0.0, xp=0.0, desc="Festive exclusive animals!"),
    "easter":         dict(name="Easter Event",          emoji="🐣", animal_chance=0.04, luck=0.0, xp=0.0, desc="Colorful exclusive animals!"),
    "legendary_hunt": dict(name="Legendary Hunting Event", emoji="👑", animal_chance=0.01, luck=1.0, xp=0.0, desc="Rare animals appear much more often!"),
    "double_xp":      dict(name="Double XP Event",       emoji="✨", animal_chance=0.0,  luck=0.0, xp=1.0, desc="Pets earn double XP!"),
    "lucky":          dict(name="Lucky Hunting Event",   emoji="🍀", animal_chance=0.002, luck=0.5, xp=0.0, desc="More luck, and glitched animals!"),
}

# ═══════════════════════════════════════
# بەشی ٨: Huntbot
# base = نرخی ئاستی ١ (بە essence). نرخی ئاستی L+1 = base * (L+1)^2
# ═══════════════════════════════════════
HB_MAX_LEVEL = 50
HB_STATS = {
    "efficiency": dict(name="Efficiency", emoji="🐾", base=100, desc="More animals per hour"),
    "gain":       dict(name="Gain",       emoji="💠", base=100, desc="More essence per hour"),
    "duration":   dict(name="Duration",   emoji="⏳", base=150, desc="Longer maximum run time"),
    "experience": dict(name="Experience", emoji="✨", base=100, desc="More pet XP per hour"),
    "cost":       dict(name="Cost",       emoji="💸", base=200, desc="Cheaper hunting (-1% per level)"),
    "radar":      dict(name="Radar",      emoji="📡", base=300, desc="Higher chance to find Bot animals"),
}
HB_BASE_ANIMALS_PER_HOUR = 12      # ×(1 + 0.10 × level)
HB_BASE_ESSENCE_PER_HOUR = 20      # ×(1 + 0.10 × level)
HB_BASE_XP_PER_HOUR = 100          # ×(1 + 0.15 × level)
HB_BASE_MAX_HOURS = 2.0            # + 0.5 × level
HB_COST_DISCOUNT_PER_LEVEL = 0.01  # لە نرخی HUNT_COST بۆ هەر ئاژەڵێک
HB_BASE_BOT_CHANCE = 0.002         # + 0.001 × level
HB_MIN_HOURS = 0.25

# ═══════════════════════════════════════
# بەشی ٩: ئامرازی ئاژەڵ (خۆکار دروست دەبن، دەستکاری مەکە)
# ═══════════════════════════════════════
def _slug(s):
    return s.lower().replace(" ", "_")

ANIMALS = {}
for _row in ANIMAL_LIST:
    _name, _emoji, _rar, _cat, _desc = _row[:5]
    _event = _row[5] if len(_row) > 5 else None
    _r = RARITIES[_rar]
    ANIMALS[_slug(_name)] = dict(
        id=_slug(_name), name=_name, emoji=_emoji, rarity=_rar, category=_cat, description=_desc,
        event=_event, pool=_r["pool"], image=None, weight=1.0,
        sell=_r["sell"], essence=_r["essence"], xp=_r["xp"], zoo=_r["zoo"],
    )

MAIN_BY_RARITY = {r: [a for a in ANIMALS.values() if a["rarity"] == r and a["pool"] == "main"]
                  for r, d in RARITIES.items() if d["pool"] == "main"}
BOT_ANIMALS = [a for a in ANIMALS.values() if a["pool"] == "huntbot"]
EVENT_ANIMALS = {}
for _a in ANIMALS.values():
    if _a["event"]:
        EVENT_ANIMALS.setdefault(_a["event"], []).append(_a["id"])
for _r, _l in MAIN_BY_RARITY.items():
    assert _l, f"rarity {_r} دەبێت لانی کەم ئاژەڵێکی هەبێت"

def animal_chance_percent(a):
    """ئەگەری ڕاستەوخۆی ئاژەڵێک لە hunt ی ئاسایی (٪)"""
    r = RARITIES[a["rarity"]]
    if r["pool"] != "main":
        return 0.0
    pool = MAIN_BY_RARITY[a["rarity"]]
    total_w = sum(x["weight"] for x in pool)
    return r["ppm"] / TOTAL_PPM * 100 * a["weight"] / total_w
