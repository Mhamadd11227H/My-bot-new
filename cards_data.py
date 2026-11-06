"""
Anime Cards Data with Chest Configurations, Rarity Direct Buy Costs,
Massive Character Universe, and Multi-Level GIF Evolution Support.
"""

CHEST_CONFIG = {
    "Bronze": {
        "cost": 50000,
        "color": 0xCD7F32,
        "emoji": "🥉",
        "name": "سندوقا بڕونز (Bronze Chest)",
        "odds": {"Common": 60, "Uncommon": 30, "Rare": 10}
    },
    "Gold": {
        "cost": 150000,
        "color": 0xFFD700,
        "emoji": "🥇",
        "name": "سندوقا زێڕین (Gold Chest)",
        "odds": {"Uncommon": 45, "Rare": 35, "Epic": 20}
    },
    "Diamond": {
        "cost": 400000,
        "color": 0xB9F2FF,
        "emoji": "💎",
        "name": "سندوقا ئەڵماس (Diamond Chest)",
        "odds": {"Rare": 40, "Epic": 35, "Mythic": 25}
    },
    "Legendary": {
        "cost": 1000000,
        "color": 0xFF4500,
        "emoji": "👑",
        "name": "سندوقا ئەفسانەیی (Legendary Chest)",
        "odds": {"Epic": 40, "Mythic": 30, "Legendary": 20, "Fabled": 10}
    }
}

RARITY_CONFIG = {
    "Common": {
        "color": 0x95A5A6,
        "base_power": 150,
        "drop_chance": 40,
        "direct_buy_cost": 30000,
        "emoji": "<:emoji_22:1535315607766044763>",
        "name": "Common"
    },
    "Uncommon": {
        "color": 0x2ECC71,
        "base_power": 450,
        "drop_chance": 28,
        "direct_buy_cost": 80000,
        "emoji": "<:emoji_20:1535315591282294784>",
        "name": "Uncommon"
    },
    "Rare": {
        "color": 0x3498DB,
        "base_power": 1200,
        "drop_chance": 18,
        "direct_buy_cost": 200000,
        "emoji": "<:emoji_19:1535315573976596610>",
        "name": "Rare"
    },
    "Epic": {
        "color": 0x9B59B6,
        "base_power": 2800,
        "drop_chance": 8,
        "direct_buy_cost": 500000,
        "emoji": "<:emoji_18:1535315554682937425>",
        "name": "Epic"
    },
    "Mythic": {
        "color": 0x992D22,
        "base_power": 5500,
        "drop_chance": 4,
        "direct_buy_cost": 1200000,
        "emoji": "<:emoji_16:1535315512400027768>",
        "name": "Mythic"
    },
    "Legendary": {
        "color": 0xF1C40F,
        "base_power": 12000,
        "drop_chance": 1.5,
        "direct_buy_cost": 3000000,
        "emoji": "<a:emoji_15:1535315469823910059>",
        "name": "Legendary"
    },
    "Fabled": {
        "color": 0xE74C3C,
        "base_power": 25000,
        "drop_chance": 0.5,
        "direct_buy_cost": 8000000,
        "emoji": "<a:emoji_35:1535330409221455952>",
        "name": "Fabled"
    }
}

ANIME_CHARACTERS = [
    # 🌟 FABLED (لوتکەی هێزی بێسنوور)
    {
        "id": "jinwoo_monarch", "name": "Sung Jin-Woo (Shadow Monarch)", "anime": "Solo Leveling", "rarity": "Fabled",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535717995882483773/tumblr_8dc800c6f5ff48cbee3dd562268ef535_ed70648d_640.gif?ex=6a78c856&is=6a7776d6&hm=35e4089b08db5c44919275bf9d9ba9eaa496c6dfdc242eab6fed1cae442a68e8&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535718014408990921/sqjtjhaazsqe1.gif?ex=6a78c85a&is=6a7776da&hm=0c8b85b99de0b15f3de3f791a939bc085c14d81d1bca2445c073814f157a079d&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535716698295111680/223415.gif?ex=6a78c721&is=6a7775a1&hm=3670184e2542d7c9d3fc1a3ed77b542d86aa657a5884a2ea71bf55fcf8548b61&"
    },
    {
        "id": "gojo_purple", "name": "Gojo Satoru (Hollow Purple)", "anime": "Jujutsu Kaisen", "rarity": "Fabled",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535723221922357310/fJFQdW.gif?ex=6a78cd34&is=6a777bb4&hm=fd6f905e99533884ef5b12c4badcd3df797f5d01c2c9848ea28ee75c92781e22&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535723647992602765/211786.gif?ex=6a78cd9a&is=6a777c1a&hm=4e686750dfa4bc2539aa65bceddca4fef0d9a71cf09ef730cc97d6cb25ab962d&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535723965379510322/satoru-gojo-gif-7.gif?ex=6a78cde5&is=6a777c65&hm=cbccf511018399de25995c88ff987c42e75293f371eb973a1c2a9e740f0a399a&"
    },
    {
        "id": "sukuna_20f", "name": "Ryomen Sukuna (King of Curses)", "anime": "Jujutsu Kaisen", "rarity": "Fabled",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535727141654765658/tumblr_91e8d1645e7d7ddb4f0b6f40c9cd5552_e28fdb6a_540.gif.webp?ex=6a78d0db&is=6a777f5b&hm=16ba0f456da3fea70156b65b0b5dae0b7aa712c996de690f46b02b9321f8e6cd&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535727490633433169/25a9bfc6f707d9119d723e7f4b179c1c.gif?ex=6a78d12e&is=6a777fae&hm=179186fe7883a57d0b4b3f51175f466e4a623791c70e108fcde83e403420177e&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535727151360376894/57a9e8dea4dd3dd8be8357f5075f1a91.gif?ex=6a78d0dd&is=6a777f5d&hm=249801a6f5b41b5d77c5a327111c2fc1ff3fd1ecdef9974998375f9f49a66d1d&"
    },
    {
        "id": "luffy_g5", "name": "Monkey D. Luffy (Gear 5 Nika)", "anime": "One Piece", "rarity": "Fabled",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535696658640404530/luffy-gif-4.gif?ex=6a78b477&is=6a7762f7&hm=a27c12ce0769f666d9996ae810aea5c5bf7415bc799bb95a7ad7b89168866e48&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535696678794039381/xovtud0riaxe1.gif?ex=6a78b47c&is=6a7762fc&hm=e2a3516cf66e86e2d086cab9b27e0a86b285c8f43d240f3f80b0503ca77f0c3e&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535697010785517648/a5427317a501a52d7c60bb4a26b3b69e.gif?ex=6a78b4cb&is=6a77634b&hm=44371910b477582e4bbe99752160fa069ae37a277f1ed3b08010794035cff01a&"
    },
    {
        "id": "muzan_demon", "name": "Muzan Kibutsuji (Demon King)", "anime": "Demon Slayer", "rarity": "Fabled",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535728711435948192/406be933ab39e678f50f9e1a3fa687fb.gif?ex=6a78d251&is=6a7780d1&hm=6fda02c24834504333ca5985dc1c9a57c3e9bffe607f9a75adc7e7b150d4eabc&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535728732747206787/f23f834aa6b4b034baf06bf922295462.gif?ex=6a78d256&is=6a7780d6&hm=a71656ef141646e971537a946fcd89e82d870a445c6c7cf261119faf7cfd2724&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535728795728740443/predicting-muzan-is-moveset-v0-rfzr1ykho3ff1.gif?ex=6a78d265&is=6a7780e5&hm=12615bb479c8f2eb467d044d701faba42f3824bebee701cc8b7964880ed9f2d5&"
    },
    {
        "id": "ashborn_monarch", "name": "Ashborn (Original Shadow Monarch)", "anime": "Solo Leveling", "rarity": "Fabled",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535730088631599224/solo-leveling-ore-dake-level-up-na-ken.gif?ex=6a78d399&is=6a778219&hm=b90799332bcbdd886fe3e41030befde651c901a9f8c3a19a66658688968c94bc&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535730088631599224/solo-leveling-ore-dake-level-up-na-ken.gif?ex=6a78d399&is=6a778219&hm=b90799332bcbdd886fe3e41030befde651c901a9f8c3a19a66658688968c94bc&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535730088631599224/solo-leveling-ore-dake-level-up-na-ken.gif?ex=6a78d399&is=6a778219&hm=b90799332bcbdd886fe3e41030befde651c901a9f8c3a19a66658688968c94bc&"
    },

    # 👑 LEGENDARY (کاپتنەکان، ئۆردەر، و حاشیرای ئەفسانەیی)
    {
        "id": "sakamoto_prime", "name": "Taro Sakamoto (Prime Assassin)", "anime": "Sakamoto Days", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535732768296800316/hnyo7qyt6kje1.gif?ex=6a78d618&is=6a778498&hm=c39dd9e82e7f8a36afaaca35ad3f9088984e333c9b256754795fa9a6c82b7d1a&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535733486604783706/658a89575f42a846996024d87a9d985a.jpg?ex=6a78d6c3&is=6a778543&hm=8fe8ce019e190be993f3cb1e71c605105b1bac42062542ed23045bc498015dc1&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535732749917233172/223323.gif?ex=6a78d614&is=6a778494&hm=a5a303279d9b3b36c2cb15f4830eb4931fd8598c98353831719de13e898a07f7&"
    },
    {
        "id": "nagumo_order", "name": "Nagumo (ORDER Member)", "anime": "Sakamoto Days", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535734992641196052/nagumo-nagumo-sakamoto-days.gif?ex=6a78d82a&is=6a7786aa&hm=8a655a1c23d3ac9bdf1c927ac02ac1a52c3f54a1d11da7b0fa8a26c33a2123fd&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535734925838524466/nagumo-yoichi.gif?ex=6a78d81a&is=6a77869a&hm=4a95d75cdf61b1d01a8cd27c333418337886db3f05798b507207fd5da098597d&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535734952291737692/nagumo-nagumo-yoichi.gif?ex=6a78d821&is=6a7786a1&hm=b9c464f29ff2d6ef582dde9a234fd1be36201840acc413d7656814c1e0624e96&"
    },
    {
        "id": "uzuki_slur", "name": "X / Kei Uzuki (Slur)", "anime": "Sakamoto Days", "rarity": "Legendary",
        "image_lvl1": "https://i.giphy.com/media/arbHBoiUW3iyA/giphy.gif",
        "image_lvl2": "https://i.giphy.com/media/arbHBoiUW3iyA/giphy.gif",
        "image_lvl3": "https://i.giphy.com/media/arbHBoiUW3iyA/giphy.gif"
    },
    {
        "id": "shishiba_order", "name": "Shishiba (ORDER Hammer)", "anime": "Sakamoto Days", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535736271551467530/sakamoto-days.gif?ex=6a78d95b&is=6a7787db&hm=b41c09619c15923c72f948507340acaba67bbe45a45454ab82475746b1de1a42&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535736308926779432/tumblr_c8bc8278e7919f9302222e98288ea61a_3a8df952_640.gif?ex=6a78d964&is=6a7787e4&hm=57f34039f09c44c20ed6ec91c2273ed692c0b4ce9c2b6b91a28bbe5e8b19c5c5&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535736338962194533/tumblr_0b0b04b43c54c4919ea2f572153c7572_cdbe4f5c_640.gif?ex=6a78d96b&is=6a7787eb&hm=17350daaec0c83cfd75c5b18e5b8507d12e5daa5318d08ca9e27ea4dba29d17d&"
    },
    {
        "id": "beru_king", "name": "Beru (Shadow Ant King)", "anime": "Solo Leveling", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535737171774939258/beru-solo-leveling-beru_1.gif?ex=6a78da32&is=6a7788b2&hm=d2a3ed2e12df8c1e51201170d557076da4d670f6729fbc2f024ab433e7ada4d8&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535737144159641692/beru-solo-leveling-beru.gif?ex=6a78da2b&is=6a7788ab&hm=70d1cbb77caccebeaa75e0452a35ab8f455ca11bed48095aee8767aef4f47e16&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535737207317332028/solo-leveling-ant-king.gif?ex=6a78da3a&is=6a7788ba&hm=5a35017d361ccfe826b70f4db8eae433644d494a774d2f9659d2d8185831b6e8&"
    },
    {
        "id": "igris_red", "name": "Igris (Red Knight Commander)", "anime": "Solo Leveling", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535738365708861510/igris-solo-leveling.gif?ex=6a78db4f&is=6a7789cf&hm=7c9c3729998890652217266625a99a4fe7124155154a98f0a4c9724baf9a5b33&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535738388186136767/solo-leveling-ore-dake-level-up-na-ken_1.gif?ex=6a78db54&is=6a7789d4&hm=5104cd676ea4cb3b82a7a1339f0624343c091c8eea343896443f7518379414e4&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535738344003080222/solo-leveling-igris.gif?ex=6a78db49&is=6a7789c9&hm=cd47839609e385e9340c83f94559693875571c2c270111557c6e1e0b5b54f26f&"
    },
    {
        "id": "bellion_shadow", "name": "Bellion (Grand Marshal Shadow)", "anime": "Solo Leveling", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535739418202214480/bellion-solo-leveling-1.jpg?ex=6a78dc49&is=6a778ac9&hm=bfdaf8c6b99bb3d7a6c538555401e1fd6683099e3ecc42d3e3030f23c33e21ce&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535739418202214480/bellion-solo-leveling-1.jpg?ex=6a78dc49&is=6a778ac9&hm=bfdaf8c6b99bb3d7a6c538555401e1fd6683099e3ecc42d3e3030f23c33e21ce&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535739418202214480/bellion-solo-leveling-1.jpg?ex=6a78dc49&is=6a778ac9&hm=bfdaf8c6b99bb3d7a6c538555401e1fd6683099e3ecc42d3e3030f23c33e21ce&"
    },
    {
        "id": "kaido_dragon", "name": "Kaido (King of Beasts)", "anime": "One Piece", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535740488487927828/one-piece-luffy-vs-kaido.gif?ex=6a78dd49&is=6a778bc9&hm=db6a069bfc445e5953ce341fe2f8ce1f1b15158bac6845e500326b5a7d926ff9&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535740543559143525/3a93cb1a9914b244cfb0fda35c9511ce.gif?ex=6a78dd56&is=6a778bd6&hm=a8836306097f37265e594e31f35735e72d405f1b3739b5579c0658244fde93fb&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535741033005064232/3965025.gif?ex=6a78ddca&is=6a778c4a&hm=0adacf187ee07828327fb5c60acc6f63fb0168d7c94a063bb4ed058809725637&"
    },
    {
        "id": "shanks_haki", "name": "Red-Haired Shanks (Divine Departure)", "anime": "One Piece", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535746997233918092/9782.gif?ex=6a78e358&is=6a7791d8&hm=8b08f83e26a5e0b7b55d59fb004713f8fa17b1ca5ca400769a6ba47c4e247339&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535746991311814788/aef23c9afcf6dd47a4f2f5e08e10da5f.gif?ex=6a78e357&is=6a7791d7&hm=28fbb8f8ed7c24053a6c93e0fcd7a746334c0f7cac32913f2e1abcf837fbcec8&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535747015491846144/0447b5ba8cd97910ba57afdf15fde7a5.gif?ex=6a78e35d&is=6a7791dd&hm=609ef95a012fdf7492ac5969fe6634f56068bf7014c24fcafcdb19689dfab718&"
    },
    {
        "id": "whitebeard_quake", "name": "Edward Newgate (Whitebeard Prime)", "anime": "One Piece", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535749696075862066/download_1.gif?ex=6a78e5dc&is=6a77945c&hm=7988d9768d1721661a1af11c387fda71ec49eb2c33e7716ac8435018bbd33429&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535749230621360218/65c28470ebe051d643756ae31cd5f5a6.gif?ex=6a78e56d&is=6a7793ed&hm=cbbb7f5d2d62cfc8b5cf355308f22bd03f5425c5e61b2d2bbf54debba06f8a11&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535749310602420324/edward-whitebeard-newgate-from-one-piece-v0-gc3m6nd3cpkf1.gif?ex=6a78e580&is=6a779400&hm=67750e49f9c3f1181cdc186529ce24d00761d19a871aef29e6e1b3078c3a6a9e&"
    },
    {
        "id": "gold_roger", "name": "Gol D. Roger (Pirate King)", "anime": "One Piece", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535750822216867950/sq-Xe.gif?ex=6a78e6e8&is=6a779568&hm=8a6dd2f33b8bbe244dd3d9f1815f00b7762656389c8a9b35a9dc35a8682771ce&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535750854425055293/48d2d446903509f10103848b5fe648b9.gif?ex=6a78e6f0&is=6a779570&hm=6453b807f6a05cdd14786f7479afb53369f9fd5ddec5b028701353275b95d898&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535750871294410893/FVeatyI.gif?ex=6a78e6f4&is=6a779574&hm=85977898298130779b6e774dfe6dd34bb7975bad1f64fae6ef34873d2f8048a9&"
    },
    {
        "id": "yoriichi_sun", "name": "Yoriichi Tsugikuni (Sun God)", "anime": "Demon Slayer", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535753611143815199/tumblr_0601bdb3a5c574e8f49272d4a1557096_e6fda0f9_640.gif?ex=6a78e981&is=6a779801&hm=7bb277f176861f193a1881a0e750076de714fc1c794afc0a41fbf147e654a213&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535753460279021720/14edc5ed90f3f1a7990dfc8949e7dade.gif?ex=6a78e95d&is=6a7797dd&hm=6530bf739ef12830ba206bb3ebc2b964705a4e7073d2afcb6d1bc7209ddef75d&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535753519829614612/5568f31749a10d8483ab8ba9af745bf3.gif?ex=6a78e96c&is=6a7797ec&hm=04f13ec6767806fb49e812ad660d9cd14efa8f5c121961f45d6f79de84707315&"
    },
    {
        "id": "kokushibo_moon", "name": "Kokushibo (Upper Moon 1)", "anime": "Demon Slayer", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535754913534054460/kokushibo.gif?ex=6a78eab8&is=6a779938&hm=57cd9936107cc70c2a39578ba6f371ef800def04052683eaf7c5b91f07539681&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535754896668758036/2c541bd3e9d03cae8dd4c534c59b08f2.gif?ex=6a78eab4&is=6a779934&hm=f04b187845c500651f3eb474c4701073534d4f917033fc5e5b30a3dc974f2ac1&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535754657631174686/81c43fdf49b65b66afbc85b78a2a8873.gif?ex=6a78ea7b&is=6a7798fb&hm=16de1280ba4cc16c71b9392c3e2ca07390336934fcb8a9ff70a362e20bea0f7e&"
    },
    {
        "id": "meruem_king", "name": "Meruem (Post-Rose Ant King)", "anime": "Hunter x Hunter", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535756196001218580/601dde03ab3d87665e79015d72204d73.gif?ex=6a78ebea&is=6a779a6a&hm=f095344c3d856a0e97ce92cc57ae6ff0de080a1627a179652c99cba701e38ddd&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535756291966767175/bIWVci.gif?ex=6a78ec00&is=6a779a80&hm=3f4479016d8148b60db827cb9545ecc47a8e652731ae48da0e081153635572db&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535756310384091216/5384010-5393474661-tumbl.gif?ex=6a78ec05&is=6a779a85&hm=c7ce879945c94944bf8ecfe00ce50809669c7ff229dc03c1ed2c9df9b7a5e27e&"
    },
    {
        "id": "netero_buddha", "name": "Isaac Netero (100-Type Guanyin)", "anime": "Hunter x Hunter", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535757167334916146/5edd53cbbdf986c655f970a055fec991.gif?ex=6a78ecd1&is=6a779b51&hm=98eb80b2ab4fbb7ec14f2d1e8047b2167e44b977c39ea26cad3cb57fafc1d61b&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535757213224800369/0WYtMmA.gif?ex=6a78ecdc&is=6a779b5c&hm=a3f17aad1ff8f26105248714646e118d81fe095ba7c9b3edb2353685047e0e25&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535757192785825842/netero-death-netero-gif.webp?ex=6a78ecd7&is=6a779b57&hm=cce2e2a5ef704ea0488d40ae9c9c343b21e3095e4f8e3144c63d47094b16f11d&"
    },
    {
        "id": "ging_freecss", "name": "Ging Freecss (Zodiac Hunter)", "anime": "Hunter x Hunter", "rarity": "Legendary",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535759104520359996/animesher.com_ging-manga-gif-1947040.gif?ex=6a78ee9f&is=6a779d1f&hm=2f74af38731614f19e5df98eeee197d1c5a2161c2f7edc2ed70bef105d32aaf9&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535759161797906472/o3g894R.gif?ex=6a78eead&is=6a779d2d&hm=05b52d8e51b1ebf75e34d89e9687435284fcdd3b84b28358ac1afcae36899a7b&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535759349362851910/91bd5d16a247728665aac2bfcb38c9d3.gif?ex=6a78eed9&is=6a779d59&hm=ef79542a65ef6e5fb838b6cbe8be9e4d08555187b58b84114dc2a4a1a1c0c846&"
    },

    # 🩸 MYTHIC (پاشاکانی شەڕ و ژەنڕاڵەکان)
    {
        "id": "zoro_koh", "name": "Roronoa Zoro (King of Hell)", "anime": "One Piece", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535774687349706863/zoro-gif-10.gif?ex=6a79a5e2&is=6a785462&hm=1bbfb36ec64acb7bc9bb228a7fdd9cd715982b7a19aa17304af288ffde9ccaaa&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535774707306078218/2e55f7894bf872a68daca8829ff27379.gif?ex=6a79a5e7&is=6a785467&hm=98c7646d2736e0ea7be76ccb80b6c8f26230a0e06ccf5b7ae4aedbc51ec1ca82&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535774679569272943/a-drawing-of-a-man-with-a-sword-in-his-mouth-with-stitches-on-his-chest-jcjc5y7wv6g4z9xd.gif?ex=6a79a5e0&is=6a785460&hm=29544690ec5a647d2dcf1925a73fe5640928a12aa42faaa753d4c6bb2a7fdf07&"
    },
    {
        "id": "blackbeard_gura", "name": "Marshall D. Teach (Blackbeard)", "anime": "One Piece", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535775333226250272/9332bf76c5a8c8389ef447b5df1a3f05.gif?ex=6a79a67c&is=6a7854fc&hm=57de4592afe05df428eca554bf825bef8d142d1b0fb2a3c30946520667d05ed0&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535775303123869756/0874d121307b3cc5c123cbea31146127.gif?ex=6a79a675&is=6a7854f5&hm=46cb973552a1535ed79379479e732f4b6a77a766dafac331ea39ed7c5d324cb4&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535775351500841020/6thh7hmi2ygf1.gif?ex=6a79a681&is=6a785501&hm=6df0ec3e4be6005dc5a04e8e86f3b1436948537ec8bf5af34c5bc2d214b3f426&"
    },
    {
        "id": "big_mom_soul", "name": "Charlotte Linlin (Big Mom)", "anime": "One Piece", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535776108048416818/prime-bigmom-vs-kaido-v0-zwff3qwoer7c1.gif?ex=6a79a735&is=6a7855b5&hm=60d2db0d40a84f7c1d8e452fb146edd88952f2cd17bec6d3ce3fc9ccb846771a&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535776124942946444/fff11f198151cb4b0afc2e79bf7a495e.gif?ex=6a79a739&is=6a7855b9&hm=8aeb72dc09eb12fd392c5ece4d29577933aac10566b8edbcd0eb6be5b3774871&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535776147130818632/tumblr_43bc182a5f0280b7f940f398ddad4cb2_dad8b629_540.gif?ex=6a79a73e&is=6a7855be&hm=59e130d3a5040ffd7e696e5b104a30f3bc9179862d0ae84044ff017422a6c920&"
    },
    {
        "id": "akainu_magma", "name": "Fleet Admiral Sakazuki (Akainu)", "anime": "One Piece", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535776883730415626/one-piece-akainu.gif?ex=6a79a7ee&is=6a78566e&hm=62d81fdf9dae9e487c1c023230c9aecf780cd6c8e3adcc963e8034d8d3ed60be&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535776941007966279/one-piece-akainu_1.gif?ex=6a79a7fc&is=6a78567c&hm=a8da869982a7225fed21eeaad2e690c4f9ce579f19f8162ee2a9af3c35626eab&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535776935047602266/akainu-covered-in-magma-xuo0jpjphiuw43f6.gif?ex=6a79a7fa&is=6a78567a&hm=f6c9c6c01353a19f297752b5b1d73adf11426338318bb8925131ec18219e955a&"
    },
    {
        "id": "akaza_upper3", "name": "Akaza (Destructive Death)", "anime": "Demon Slayer", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535777627888160858/5e4337a94a1f5e77448dbe65c57cd6fa.gif?ex=6a79a89f&is=6a78571f&hm=361c68892e99513ac5041d8c8936805718a68177e7071630fd06e9ea42c58ec3&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535777734566092830/3ce2487506f08547933ee3a24e8199c8.gif?ex=6a79a8b9&is=6a785739&hm=9817d41475a9c20affd354a92482e53fc62dc5c0ec2f6f7bdd8aa9e670eebf16&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535777696519290960/VyDlY0.gif?ex=6a79a8b0&is=6a785730&hm=3ea903170a66aba424a67b0c9463b7cfa30b00f9c372065c9ad65b07a11ea182&"
    },
    {
        "id": "doma_upper2", "name": "Doma (Upper Moon 2)", "anime": "Demon Slayer", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535778444481134702/4d8d732b49ad3da6671fcaff3351b89c.gif?ex=6a7900a2&is=6a77af22&hm=e4ed746ea473d2f64a6c140be977284c0a14911667a18db371e1c83c4623d0ed&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535778474160296036/giphy_1.gif?ex=6a7900a9&is=6a77af29&hm=6d819c3eb6f749d1b3b66295808a8c255a018e222dd178245e15faf91cfb2256&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535778610399682620/408966de0712cf50ec737388dc6ba4cd.gif?ex=6a79a98a&is=6a78580a&hm=bc04203aa33647e779b9050bd87040276e43edb7e2dff8a251196e320fe53e19&"
    },
    {
        "id": "gyomei_stone", "name": "Gyomei Himejima (Stone Hashira)", "anime": "Demon Slayer", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535779030719008869/223103.gif?ex=6a79012e&is=6a77afae&hm=640c3fe7a70a9b2f61a3f71416ac5c102513452ffadc772e03d78706b8303d52&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535779098033659925/tumblr_87b703aa63ff88d730e34528d3a19ec9_adcf1ac9_1280.gif?ex=6a79013e&is=6a77afbe&hm=a10a52519f0d788a90aed77addb0b82b3b0558780ebf9ee462c50c894db6f0c3&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535779125485248533/9314556-gif_20240307_235546_305.gif?ex=6a790144&is=6a77afc4&hm=caf47954277861e8f2ff4bcf1ddd36b1f8b08f2b6fb85470a6b205ebfa353d20&"
    },
    {
        "id": "toji_heavenly", "name": "Toji Fushiguro (Sorcerer Killer)", "anime": "Jujutsu Kaisen", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535779936810303538/219891.gif?ex=6a790206&is=6a77b086&hm=7e064f3ee3f78f646f4b0a4b8bf16113d29253d30cc8868669b78a079d3e5cfb&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535779959203696710/toji-gif-6.gif?ex=6a79020b&is=6a77b08b&hm=6b3e7b557eeba72069df51934046134fa7736daab320b1ec0318729632328817&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535779989759336519/7de6c35c012945758539d381df67a081.gif?ex=6a790212&is=6a77b092&hm=f47f5b0d20bb4a16a24b4bbd051f9191bb522c4658776a847df2f13704862f79&"
    },
    {
        "id": "geto_curse", "name": "Suguru Geto (Uzumaki Domain)", "anime": "Jujutsu Kaisen", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535955014437052416/tumblr_dce355bd20ee23d42929675022771087_2f02bce9_540.gif?ex=6a79a514&is=6a785394&hm=89dfe7eeae0d020650d824531010264c80b8f400275cc1c5b5cb18d9cd160a7d&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535954974541090917/211829.gif?ex=6a79a50a&is=6a78538a&hm=0b9a3799234b8cd81f31c76af7128ee1fdf13b3506dd828553c6b6c0f8894c7d&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535955033068142613/tumblr_6d3f3e698b97d1bfb195944a616ea121_0aab3cbe_640.gif?ex=6a79a518&is=6a785398&hm=40a1e1873eb47346f7a906979281c6169b9b06707c9c8963a0926c36cbb33b85&"
    },
    {
        "id": "kenjaku_brain", "name": "Kenjaku (Womb Profusion)", "anime": "Jujutsu Kaisen", "rarity": "Mythic",
        "image_lvl1": "https://i.giphy.com/media/DMvXFFMFmoM80/giphy.gif",
        "image_lvl2": "https://i.giphy.com/media/DMvXFFMFmoM80/giphy.gif",
        "image_lvl3": "https://i.giphy.com/media/DMvXFFMFmoM80/giphy.gif"
    },
    {
        "id": "gon_adult", "name": "Gon Freecss (Adult Rage)", "anime": "Hunter x Hunter", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535956218617667624/13214.gif?ex=6a79a633&is=6a7854b3&hm=28c72d51cecc7f828e7d65da6c2cca910f0afa27a37caef83870e3f597491af2&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535956232303804426/143335.gif?ex=6a79a636&is=6a7854b6&hm=51995ddba89c17c6698fa71089cc06991b1df01c1db17506996768e7bab51f1c&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535956247017168926/727a23a3d85e0a4664bc536dd56d3aa2.gif?ex=6a79a639&is=6a7854b9&hm=eb123587166a3007ff25439aee4705c9665514c564ec686785950547ec2bd2ad&"
    },
    {
        "id": "hisoka_bungee", "name": "Hisoka Morow (Bungee Gum)", "anime": "Hunter x Hunter", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535956924976201769/1ed6e0bc978ddf4f7aaddd67b521c159.gif?ex=6a79a6db&is=6a78555b&hm=a831c58c30f17416f858be54e6ec1ca38aa7639fb262540885e4e14eb6e3ff2d&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535956908102389800/9dde138706e8de34ef75d03bc9e8975c.gif?ex=6a79a6d7&is=6a785557&hm=e919e3ab1dfe36cd20ddb7ec23f4147fcccab7d24d2fbe9ac26270a4f8a76d03&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535956935751503984/fd696321cd7d2902474660b9f2e27609.gif?ex=6a79a6de&is=6a78555e&hm=9e289ddb7323394979b05b1b2290e3af39251d02c207f0c05f068894be35b8f3&"
    },
    {
        "id": "pitou_terpsichora", "name": "Neferpitou (Terpsichora)", "anime": "Hunter x Hunter", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535957411901341756/b7e3636052bc1a444a043258ae394a59.gif?ex=6a79a74f&is=6a7855cf&hm=8ee5c7ed010d81ce4ea5b1dfc59da93101713271f6403dd2c2c9b574e871f9cb&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535957424337461298/d6753a0c048e935de407f12526c6a393.gif?ex=6a79a752&is=6a7855d2&hm=0b6c18e22a9744031ec9a06732072fe1fd627f34c772ded325a2276021b0923e&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535957428158468106/neferpitou-hunter-x-hunter.gif?ex=6a79a753&is=6a7855d3&hm=27bed3a61a9c27a0486a28c9321bfd507d20f3b60ba11922588a4dc6d8322a51&"
    },
    {
        "id": "cha_hae_in", "name": "Cha Hae-In (Sword Dancer S-Rank)", "anime": "Solo Leveling", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535957980313559170/cha-hae-in-featured-image.jpg?ex=6a79a7d7&is=6a785657&hm=5de45438c32ba67dfdc43c6ad217badcbf7a2f51b3b82a6e57e78f30ab04373e&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535957996767809606/tumblr_cdfb64682fe5e1e856c031046d0225a4_e7c24a77_640.gif?ex=6a79a7db&is=6a78565b&hm=b787bc3c2223d7ba69438c836532e0352b50f076e7cc25fdb0733e9ac70bacd8&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535958022650859560/tumblr_48d0ae4f949f834c8512ce20bcb9b842_4edb2ba0_640.gif?ex=6a79a7e1&is=6a785661&hm=16c89f11c25e9f62590644c9ab71b71676e0c6dacc277cf72526c71b095843b7&"
    },
    {
        "id": "thomas_andre", "name": "Thomas Andre (Goliath National-Level)", "anime": "Solo Leveling", "rarity": "Mythic",
        "image_lvl1": "https://i.giphy.com/media/DMvXFFMFmoM80/giphy.gif",
        "image_lvl2": "https://i.giphy.com/media/DMvXFFMFmoM80/giphy.gif",
        "image_lvl3": "https://i.giphy.com/media/DMvXFFMFmoM80/giphy.gif"
    },
    {
        "id": "osaragi_order", "name": "Osaragi (ORDER Saw Blade)", "anime": "Sakamoto Days", "rarity": "Mythic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535958708541067344/5461bb7876caa7660437ad53b3455236.gif?ex=6a79a884&is=6a785704&hm=9ac0b30c31e27be9d90ab7648befc95c1545ebbb242777b93f13a510d114990a&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535958667315122176/tumblr_ebffa9383effaf2f5c510a6b58f6defd_8a97e299_640.gif?ex=6a79a87b&is=6a7856fb&hm=c3f0db7857bf26bcb93ea2419427069d6071d2e73ce703884fb9b787dc9ebc78&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535958715872583741/download_2.gif?ex=6a79a886&is=6a785706&hm=5de157a331bcc7e2bd046139546a68154dc1a9c34357c6f92e74958ac6909bd0&"
    },
    {
        "id": "hyo_order", "name": "Hyo (ORDER Iron Fist)", "anime": "Sakamoto Days", "rarity": "Mythic",
        "image_lvl1": "https://i.giphy.com/media/DMvXFFMFmoM80/giphy.gif",
        "image_lvl2": "https://i.giphy.com/media/DMvXFFMFmoM80/giphy.gif",
        "image_lvl3": "https://i.giphy.com/media/DMvXFFMFmoM80/giphy.gif"
    },

    # 🟣 EPIC (پاڵەوانان و حاشیراکان)
    {
        "id": "sanji_ifrit", "name": "Vinsmoke Sanji (Ifrit Jambe)", "anime": "One Piece", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535964817385459752/fdc3f0e8b695f339299758ea62cb815c.gif?ex=6a79ae35&is=6a785cb5&hm=74152239fcc8bca0e91b3ff7291e183d71f1f0220fd45c6765aafad6b76ed2cf&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535964805792268388/219066.gif?ex=6a79ae32&is=6a785cb2&hm=c5e29f0599bb3c83f9ed219dc847de98cb14b7dcbb77c7a8f82c15d862920b4c&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535964849199124580/e7c05ea75a71182f966f3d9a5aa1574d.gif?ex=6a79ae3c&is=6a785cbc&hm=a428564947e6d259ece5a6a7730688393ebe280681c8e730a348f7b892099512&"
    },
    {
        "id": "law_kroom", "name": "Trafalgar D. Law (K-ROOM)", "anime": "One Piece", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535965672176222249/8583d4062eac8960245572e1a7ba7a5b.gif?ex=6a79af01&is=6a785d81&hm=8c6b55b95ffdb35bb07eef481f640858ff04d350310f76ae1cd5c368066caefd&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535965683903373362/6e7522c1fafe73c2a68e25906a3d0956.gif?ex=6a79af03&is=6a785d83&hm=5aed887ea88652ade72c02201a1b5731e5c8d26ee9af70d2aa3c9b4b109e354e&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535965716266623096/tumblr_502d6186bcdd0cd5d5d24923ba0330a8_cf363bf0_540.gif?ex=6a79af0b&is=6a785d8b&hm=70cf5781e82efe343a86ecbeca7bdf5757f1df076a2896fbef951aa1194def10&"
    },
    {
        "id": "eustass_kid", "name": "Eustass Kid (Damned Punk)", "anime": "One Piece", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535966294623518801/eustass-kid-one-piece-kid-gif.gif?ex=6a79af95&is=6a785e15&hm=7ad9d7ef5f4e90d666f4d27e80e4670550166eb2dd16c4816114a1e54a6fefc9&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535966302378917959/eustass-kid-one-piece.gif?ex=6a79af97&is=6a785e17&hm=5eb517633dfb77ab862284f36f871a0eb91efc89d7248cbb7e13120e4232384c&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535966374827130932/a-kidd-gif-collection-appreciation-post-v0-aash9kkrrige1.gif?ex=6a79afa8&is=6a785e28&hm=2a85230eee821d0afec44e43fc3feb403b27df2abc0e00dec086d5d3fca17e1b&"
    },
    {
        "id": "katakuri_mochi", "name": "Charlotte Katakuri (Mochi Awakening)", "anime": "One Piece", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535967646015557662/b2aa0c6b2c99a34708003ead09672481.gif?ex=6a79b0d7&is=6a785f57&hm=1f7de71df937d3ba66c6c9490a05c0a8525053730cc9b580c960b9e3e81f41be&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535967655016792164/tumblr_95445acc04c9c72a1c823eef87e69673_47bbf295_500.gif?ex=6a79b0d9&is=6a785f59&hm=4382512f8dc01ef0655e6386323273b1579bb880821ca24c0c78155fac2b9d23&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535967664357380257/rXWaTEB.gif?ex=6a79b0dc&is=6a785f5c&hm=b043050f7a7385368031ed26d20f5d82289388577db6f6fea316d6407cb43996&"
    },
    {
        "id": "rengoku_flame", "name": "Kyojuro Rengoku (Flame Hashira)", "anime": "Demon Slayer", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535968447861620766/f3fcdb523cdc9ac235c264f4f59d3d9f.gif?ex=6a79b196&is=6a786016&hm=5075e02ec02666b4986fc65718b60b157ec3786e2b6e954a86a66105b17cebda&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535968467201826836/220166.gif?ex=6a79b19b&is=6a78601b&hm=2b5d01ffb9e50aab68930cf2ab4e4438a6e0b41b13bced0b76fc4074bec44d65&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535968428572020777/ee8c21cbc213428ae44f6c968f8264e4.gif?ex=6a79b192&is=6a786012&hm=4b01eb2ff8f8b939e277451953acff5adcca5b58f2d03a22cf3e0f320ab2d75f&"
    },
    {
        "id": "tengen_sound", "name": "Tengen Uzui (Sound Hashira)", "anime": "Demon Slayer", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535969193818587206/68747470733a2f2f73332e616d617a6f6e6177732e636f6d2f776174747061642d6d656469612d736572766963652f53746f7279496d6167652f6763556e425538526c31486578773d3d2d3337392e313664353033666439646539363031363435343131333633373538322e676966.gif?ex=6a79b248&is=6a7860c8&hm=33547eb96b6e54feaab32d55664ca040e65beb0ad8ca223c46e0d60c32e39ec2&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535969176500572241/295c98125c4c60e01d6ea96c136437ab.gif?ex=6a79b244&is=6a7860c4&hm=89f3110f21c849024bd8d76e88a3a8fb8fea6e0fabdf470352aa73250dfba7de&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535969220700016770/TrC72k.gif?ex=6a79b24f&is=6a7860cf&hm=0e3a47e227cf39b6350c30b1d7d5edc905152d195f07925960ee0677b311ae12&"
    },
    {
        "id": "sanemi_wind", "name": "Sanemi Shinazugawa (Wind Hashira)", "anime": "Demon Slayer", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535969593812721684/sanemi-shinazugawa-sanemi.gif?ex=6a79b2a8&is=6a786128&hm=db99d672c294a29d788c4b6a4f192e7d16483872cf2f2f18ce54746592bcd8c2&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535969626213716059/8bea30a304de5fd87f18ceda3c27dc4d.gif?ex=6a79b2af&is=6a78612f&hm=21ef937aac744b7c7e82b75edb402fbae063f05ba893876d4074ea5aa8a34583&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535969690982031431/giphy-downsized-medium.gif?ex=6a79b2bf&is=6a78613f&hm=bec430d92be262689d2377b8ff1e6103ba0d0d4ec6e53b875ad84a3856e2e233&"
    },
    {
        "id": "giyu_water", "name": "Giyu Tomioka (Water Hashira)", "anime": "Demon Slayer", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535970132122144789/491b509aa57faed09346c70037387c3f.gif?ex=6a79b328&is=6a7861a8&hm=d8ae0a7dc5e9d17067f5ec4380b3a948fbfd9e102c7dca218e6da31c1e913226&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535970164384731226/download_3.gif?ex=6a79b330&is=6a7861b0&hm=773656ee2f5fe325ec091db212279ca426c551d0462d7a3ad78536d98395901b&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535970194890031134/219475.gif?ex=6a79b337&is=6a7861b7&hm=67502cf47f8c2615a41fb165c2eff65405b2b8e31e44c091b0a9dddce60da48f&"
    },
    {
        "id": "muichiro_mist", "name": "Yuta Okkotsu (Rika Queen)", "anime": "Jujutsu Kaisen", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535970915903479809/yuta-yuta-okkotsu_1.gif?ex=6a79b3e3&is=6a786263&hm=fbf1811c5edbf52ddea0e891dd618852c2cb71c1e915a696ffbf043b3296b201&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535970816070520943/yuta-yuta-okkotsu.gif?ex=6a79b3cb&is=6a78624b&hm=5c595e66ca64d8402569be71a469b3b42134a4a033197287e1d808baff1a2626&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535970898677338112/320c62f22ae09c62461e3dd297580676.gif?ex=6a79b3df&is=6a78625f&hm=87543e760efd5506f1f57f2946ee5a4beac1e7800a32fd75e5be53bf6cacb372&"
    },
    {
        "id": "hakari_gamble", "name": "Kinji Hakari (Idle Death Gamble)", "anime": "Jujutsu Kaisen", "rarity": "Epic",
        "image_lvl1": "https://i.giphy.com/media/dyjrp4XA453SU/giphy.gif",
        "image_lvl2": "https://i.giphy.com/media/dyjrp4XA453SU/giphy.gif",
        "image_lvl3": "https://i.giphy.com/media/dyjrp4XA453SU/giphy.gif"
    },
    {
        "id": "maki_liberated", "name": "Maki Zenin (Heavenly Restriction)", "anime": "Jujutsu Kaisen", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535971466753871883/b37e80e29b6c4efca0cf4937f855bc63.gif?ex=6a79b466&is=6a7862e6&hm=84de638bdb29a65be8ce87f221fa61c4402dd09adc7b39973f5be88645fd6dd3&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535971598077534371/9e38fd5a6867ac28621ffe9700c910f9.gif?ex=6a79b485&is=6a786305&hm=6d162b1290fc9a8d83dfdefd06c1466cdcc3eabc643cb613572fba255da53fe1&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535971568608354335/47d0c70ae064577a49f545214a06b716.gif?ex=6a79b47e&is=6a7862fe&hm=5d197f1d3a9eab38c1ded848f10d05ca6aa68f7506445e06a5381d39f8f463ed&"
    },
    {
        "id": "killua_godspeed", "name": "Killua Zoldyck (Godspeed)", "anime": "Hunter x Hunter", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535972263608713306/3a34e49605b9ee8034cce5276406f9c8.gif?ex=6a79b524&is=6a7863a4&hm=90829b75b421fac6cb1ac6c7d5f136cd22603b56e055e6ae288c434c86669af8&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535972227860930621/142416.gif?ex=6a79b51c&is=6a78639c&hm=8d9a2bceb875ebc4a4cae2460bc6672060996ef56fed85a4236f045e3c9b6841&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535972240812933231/fd9f38c7f92a9c37ea91d6d8c757aea0.gif?ex=6a79b51f&is=6a78639f&hm=a9c461b0ac67c71d9b66cc69287a4f6a84b80f0ebcc23f3ea2521ff8bf7a079b&"
    },
    {
        "id": "chrollo_lucilfer", "name": "Chrollo Lucilfer (Phantom Leader)", "anime": "Hunter x Hunter", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535972631176552492/giphy_2.gif?ex=6a79b57c&is=6a7863fc&hm=edaa8f5b9f6e35db1358ff570e4e3858dcbdada7165065e0db2898373f04984b&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535972803474489344/source.gif?ex=6a79b5a5&is=6a786425&hm=5b9741aac70c65ca3692f395033285c789d2cc1e9295f98ae5c009fb1dd2d8c3&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535972918952075324/sMYoej.gif?ex=6a79b5c0&is=6a786440&hm=f956a5f2a461e15a06c518c1a6b0d04afd37075d20706db5cd7e4d5cdfd51c04&"
    },
    {
        "id": "feitan_rising", "name": "Feitan Portor (Rising Sun)", "anime": "Hunter x Hunter", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535973426815180870/60908cd7dbad99577b7a69f71fc3b78d.gif?ex=6a79b639&is=6a7864b9&hm=eb7e1ade9fc9be145831d84e235970f4d1984f699e749430883cdbd192773186&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535973453369442405/526df5cd1a4b6b6b9976633c42089e56.gif?ex=6a79b640&is=6a7864c0&hm=5126b10385931d53dad2e823510c4ab7a8d726355d0b358db9b3bbcb888ab2e0&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535973437963509830/142869.gif?ex=6a79b63c&is=6a7864bc&hm=76660600984ce89fb96be9c711788b2e9be088df61ecb26a359f711b378f76c0&"
    },
    {
        "id": "shin_telepath", "name": "Shin (Clairvoyant / Mind Reader)", "anime": "Sakamoto Days", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535973932237197413/shin-asakura-in-sakamoto-days.jpg?ex=6a79b6b2&is=6a786532&hm=b74460931de71f6f67a2d8eb254da34ca2f19ff3f9ebdc75be7a06275b2ef8fc&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535973939174440991/images_2.jpeg?ex=6a79b6b4&is=6a786534&hm=28c7a8d82c2e71850a03b89471a8b9424dff77ecb486ac1e0d71a8899ccc0f84&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535973945097060382/sakamoto-days-episode-1-shin-holding-gun.jpg?ex=6a79b6b5&is=6a786535&hm=c2fa3a996b449265dbfa5236cf5e638be9e6bb7223850924e1b319ec56c5102c&"
    },
    {
        "id": "lu_xiaotang", "name": "Lu Xiaotang (Drunken Master)", "anime": "Sakamoto Days", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535974918523461692/tumblr_2f0af11215a10d27251ddfc8bce3d23e_e87d0301_540.gif?ex=6a79b79d&is=6a78661d&hm=109629d03c1c25ea87cdd8655aa1264ab21211daa98ff0a82d5974ea047b3735&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535974880351223898/lu-sakadays.gif?ex=6a79b794&is=6a786614&hm=6282660f18586b9a42b518d4b1c5380effa22ea0e617c7bc6f5a07da7b8dee9b&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535974880351223898/lu-sakadays.gif?ex=6a79b794&is=6a786614&hm=6282660f18586b9a42b518d4b1c5380effa22ea0e617c7bc6f5a07da7b8dee9b&"
    },
    {
        "id": "gaku_slur_group", "name": "Gaku (Gamer / Slur Officer)", "anime": "Sakamoto Days", "rarity": "Epic",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535974929550544896/optimize-image.webp?ex=6a79b7a0&is=6a786620&hm=28aec9a31803a2c029addd400720ccae3b7ce29253404156e2d1a4108287d2aa&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535974925158981722/sakamoto-days-gaku.gif?ex=6a79b79f&is=6a78661f&hm=981d0f66c744a922c34f73ba459f5632fa48d925f708b74245f41272a1bfa353&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535974925158981722/sakamoto-days-gaku.gif?ex=6a79b79f&is=6a78661f&hm=981d0f66c744a922c34f73ba459f5632fa48d925f708b74245f41272a1bfa353&"
    },

    # 🔵 RARE (شەڕکەرە لێهاتوو و ناودارەکان)
    {
        "id": "tanjiro_sun", "name": "Tanjiro Kamado (Hinokami Dragon)", "anime": "Demon Slayer", "rarity": "Rare",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535983539147903126/d5202fc4df11af73d10c4e6cf78b6425.gif?ex=6a79bfa4&is=6a786e24&hm=2894a3f9ad7b280a534000253b8246ae647dc8d86cc7c5a52f02472bd9b02c6a&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535983469325193216/219867.gif?ex=6a79bf94&is=6a786e14&hm=a6615fc2a94d5d1d87daaff2e94a4bbae925c16e15cc9360516a15cb217679eb&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535983373581946981/icegif-189.gif?ex=6a79bf7d&is=6a786dfd&hm=5d4bcb31326306bff1688d1abece18ed5e48e17a1ff70809d8dadd13f37d3292&"
    },
    {
        "id": "zenitsu_thunder", "name": "Zenitsu Agatsuma (Thunder God)", "anime": "Demon Slayer", "rarity": "Rare",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535983881550045296/218883.gif?ex=6a79bff6&is=6a786e76&hm=7561b1c4f81b13d5e25bdfad7dca934c917b51cd3694bc5379d1fef7afd5f354&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535983895793770566/bc56d8db5de21683d987539bfef65f60.gif?ex=6a79bff9&is=6a786e79&hm=04a0213056f9721b0b4422fa122c3bb0eefe970c98826390c4b00725266b9276&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535983899698536448/zenitsu-agatsuma-kimetsu-no-yaiba.gif?ex=6a79bffa&is=6a786e7a&hm=bdcdbbd38044fadf9522a4421e4223dbcd93fddf80dce5bb96993d09d421f02a&"
    },
    {
        "id": "nezuko_demon", "name": "Nezuko Kamado (Advanced Form)", "anime": "Demon Slayer", "rarity": "Rare",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535984259331002428/214249.gif?ex=6a79c050&is=6a786ed0&hm=75daa49e6b7847a78974f40130a79171fcf0ed43098fdd75c18843504f6dc450&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535984279819919420/219866.gif?ex=6a79c055&is=6a786ed5&hm=f8072e25500cb477cfc02561034d30588819d21b34b7dda56b59fed74eb4718f&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535984294303109231/nezuko-gif-3.gif?ex=6a79c058&is=6a786ed8&hm=23cfc7f07a2fe1b08f95f5ea8c6c428facf4dffe7deb6c7025f9ff33f8ee5873&"
    },
    {
        "id": "megumi_mahoraga", "name": "Megumi Fushiguro (Mahoraga Ritual)", "anime": "Jujutsu Kaisen", "rarity": "Rare",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535984836576018482/13-defeated-megumi-concentrates-on-staying-alive.gif?ex=6a79c0da&is=6a786f5a&hm=6a4dfd39504f3ae743875e191f08503da5781ced2901b9dccdbc797c656cf9ed&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535984757593219092/211824.gif?ex=6a79c0c7&is=6a786f47&hm=1739e1e47c1be2b94dd5f6313571ff045bb1574d0c09cddd1ec2c1fd2e2254ae&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535984820465967135/8c458e45b37b221435f085e6b458c16e.gif?ex=6a79c0d6&is=6a786f56&hm=d776c5494bcf73e949020de7807a7de7335f6b16f31a9801b52f07bcf2724f1d&"
    },
    {
        "id": "nobara_resonance", "name": "Nobara Kugisaki (Hairpin Resonance)", "anime": "Jujutsu Kaisen", "rarity": "Rare",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535985218488639548/211800.gif?ex=6a79c135&is=6a786fb5&hm=c331706d8b011d56346f80a4f079b7f0773dc9e6d08ea7d310e8b3d869e1bcbd&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535985305923092561/211815.gif?ex=6a79c14a&is=6a786fca&hm=9f10c2f5f291c32f5313021764c6a0f8672b56b7297b82654151a4025f2398f7&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535985164100960409/giphy_1.gif?ex=6a79c128&is=6a786fa8&hm=794781fa2f769296b792f5c0f93154398bb21c9035c1221777adb8be74ef8943&"
    },
    {
        "id": "todo_boogie", "name": "Aoi Todo (Boogie Woogie)", "anime": "Jujutsu Kaisen", "rarity": "Rare",
        "image_lvl1": "https://i.giphy.com/media/dyjrp4XA453SU/giphy.gif",
        "image_lvl2": "https://i.giphy.com/media/dyjrp4XA453SU/giphy.gif",
        "image_lvl3": "https://i.giphy.com/media/dyjrp4XA453SU/giphy.gif"
    },
    {
        "id": "kurapika_chain", "name": "Kurapika (Emperor Time Chains)", "anime": "Hunter x Hunter", "rarity": "Rare",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535986356835323934/tumblr_aecacdeb28a23747c42aef1645c97178_43e6586d_500.gif?ex=6a79c244&is=6a7870c4&hm=cd3c93be5f6aaa7e6f366ba58e113764efefc547961b842d976f53a043d4dd68&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535986222973984848/143369.gif?ex=6a79c224&is=6a7870a4&hm=b0802a2353314b1dd31d2df2f0b05ba0f6d139979a52d3629bb39b0362a59aef&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535986234726420480/7841170-kurapika.gif?ex=6a79c227&is=6a7870a7&hm=18813803b5122ebc5821f403538d549c5c79fc24d73936deb249498aa9be78ad&"
    },
    {
        "id": "illumi_zoldyck", "name": "Illumi Zoldyck (Needleperson)", "anime": "Hunter x Hunter", "rarity": "Rare",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535986791734182000/143321.gif?ex=6a79c2ac&is=6a78712c&hm=18ad1c3d1334e47394a4fe2c8c18d10cec9b4b5445defb0f5a7474b679d51546&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535986810646433872/142829.gif?ex=6a79c2b0&is=6a787130&hm=8b63670816c5954dcc6ea2da34ea21ca60d7c11e7b92bf09c3b62d405ee4be4d&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535986828774084679/tumblr_d843baf121dd1b30970af684d7e0b976_3c0a9302_500.gif?ex=6a79c2b5&is=6a787135&hm=fb31829dd306c88c30ad37ed76a0aadca9e7a2d14754292cdfca660de1a4db01&"
    },
    {
        "id": "choi_jong_in", "name": "Choi Jong-In (Ultimate Flame)", "anime": "Solo Leveling", "rarity": "Rare",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535987111055073351/solo-leveling-choi-jong-in.gif?ex=6a79c2f8&is=6a787178&hm=b5b126aaac74e5019be3a8a350edb6c27cff277d3febd19043f4af8fa410da1b&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535987119456002148/solo-leveling-choi-jong-in_1.gif?ex=6a79c2fa&is=6a78717a&hm=dfeaa60c9f29fda63825c42e3ebbdb9a7c529e8c44216dfba5267eac59b64056&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535987127643283546/solo-leveling-choi-jong-in_2.gif?ex=6a79c2fc&is=6a78717c&hm=0f43f08fa4ced30d6297dd777ab6f9fc5d617c53507ebf854bb25dbd988c29af&"
    },
    {
        "id": "baek_yoonho", "name": "Baek Yoonho (White Tiger)", "anime": "Solo Leveling", "rarity": "Rare",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535987571023286392/solo-leveling-episode-21-yoonho-baek.png?ex=6a79c366&is=6a7871e6&hm=20f94d58fcc931d8259ead91494a1e0b28bcbe598a378925b0fc8a2f9dc32b6f&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535987577075540048/solo-leveling-sung-jin-woo.gif?ex=6a79c367&is=6a7871e7&hm=d7b99166c5e6091476178f642c0e8d925e84cc7ec1f851e2d18f396a73ab410f&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535987585455755355/solo-leveling-baek-yoonho.gif?ex=6a79c369&is=6a7871e9&hm=008cccfcc650a8be13ff7ba56a5cb0d983a0eb9c38c935a49cc642e944419ae0&"
    },
    {
        "id": "heisuke_sniper", "name": "Heisuke Mashimo (God Sniper)", "anime": "Sakamoto Days", "rarity": "Rare",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535988010099675156/crying-heisuke-mashimo.gif?ex=6a79c3ce&is=6a78724e&hm=3bfb8ab44c2572c02399c5260ba19c278458c2fcd848261554677342266feca6&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535988003934179328/heisuke-sakamoto-days.gif?ex=6a79c3cd&is=6a78724d&hm=f0566f2f52ab84fd075751596aac08214f65e700aa1d288e719c059885901078&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535987999014387782/you-sure-thats-where-you-wanna-be-heisuke-mashimo.gif?ex=6a79c3cc&is=6a78724c&hm=9823230c6e6e15027c9cc3335954cd077ac41d8a5187cb9144d59391076dae51&"
    },

    # 🟢 UNCOMMON (شەڕکەرانی ناوەند)
    {
        "id": "inosuke_beast", "name": "Inosuke Hashibira (Beast Fangs)", "anime": "Demon Slayer", "rarity": "Uncommon",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535991476155195452/219667.gif?ex=6a79c709&is=6a787589&hm=a6afa2d76fbf1e76071dbdc6bdfe5273e491515e8fca2f0e9782c766b008716e&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535991498628407377/cd5ed23a776e6e5a30dc5a651839fda3.gif?ex=6a79c70e&is=6a78758e&hm=50dffc9e5208497e16027a84355e91324f1b04f06137885a450dd8959fe2e208&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535991525710889020/3914f53796f0f44dbc8c1bf7e1b3e05f.gif?ex=6a79c715&is=6a787595&hm=845fac1d48cac7630ccaeeab2699ccbb20d7ad6d49ea23bd101a1510a9aad63d&"
    },
    {
        "id": "kanao_tsuyuri", "name": "Kanao Tsuyuri (Flower Breathing)", "anime": "Demon Slayer", "rarity": "Uncommon",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535991927902568488/222411.gif?ex=6a79c774&is=6a7875f4&hm=549b2a229bc9e6751552605fcc3b8029f23ca1965dbe869ccf0ed3ea12ebd7d6&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535991979626995712/215482.gif?ex=6a79c781&is=6a787601&hm=2961eca9d8aa2966bec9a0b2638699bcc46a8e3539185b06cd218a31460a9b1b&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535991954146594896/222408.gif?ex=6a79c77b&is=6a7875fb&hm=c31d39f07fee44314155b3f6b13437358c5fe9f4a81f3d19ea11ac57e19d09a0&"
    },
    {
        "id": "maki_zenin_base", "name": "Maki Zenin (Cursed Tools)", "anime": "Jujutsu Kaisen", "rarity": "Uncommon",
        "image_lvl1": "",
        "image_lvl2": "",
        "image_lvl3": ""
    },
    {
        "id": "inumaki_speech", "name": "Toge Inumaki (Cursed Speech)", "anime": "Jujutsu Kaisen", "rarity": "Uncommon",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535992560969973931/ae416b810bec2d4f7e5db937d2f501ac.gif?ex=6a79c80b&is=6a78768b&hm=9b510beef56f2568bf6b6090fb3e82402c5743c5dd8da5f43f7ac6e6e7219daa&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535992596051001435/10012d13b32f83ea68b1c837f84991f7.gif?ex=6a79c814&is=6a787694&hm=4b8563931133846143882047203505d9c0c4db3a7e2b48b6dfd00b4169ddbec7&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535992654561804298/tumblr_25ccc34e9a0fbd6d70ae873082534057_6a6a888d_540.gif?ex=6a79c822&is=6a7876a2&hm=5118fcc3e4886f9671902999e326a1905c5abf47dd471de4b04c41880c44a173&"
    },
    {
        "id": "usopp_god", "name": "God Usopp", "anime": "One Piece", "rarity": "Uncommon",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535993214501261352/god-usopp-one-piece-v0-s3ev7nxtrxvg1.gif?ex=6a79c8a7&is=6a787727&hm=0520376ee77570ccbb470aa9ab4626cee02fbc8a9104538b33f9f4f1a0ed6625&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535993261678923846/219464.gif?ex=6a79c8b2&is=6a787732&hm=5e41586e569c054c855f2530a7e6dcf6a625cf2c67e38c396b3c85b829b3f115&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535993284466450462/god-usopp-one-piece-v0-gpdp66xwrxvg1.gif?ex=6a79c8b8&is=6a787738&hm=9d13007f8d4b3409f30e74392d720c37a77a48fc1fd0ca833d50c30a2f51aee3&"
    },
    {
        "id": "frankyborg", "name": "Franky (General Franky)", "anime": "One Piece", "rarity": "Uncommon",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535994476403888129/top-androides-one-piece-franky-clip.gif?ex=6a79c9d4&is=6a787854&hm=61722a8c33d8cb9ed51ec9aa02b9af120f7223ab27a640487a69270874b1a7fb&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535994492845428746/download_1.gif?ex=6a79c9d8&is=6a787858&hm=216fb9257545faa8b3c354dc560f7e34b577134adcf85657da4057e923162784&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535994484393906176/2ehPSBY.gif?ex=6a79c9d6&is=6a787856&hm=8b9c7b839ff652ce146ce4853475ffb6dd0e10403bc64a3bf9da0846ab966d23&"
    },
    {
        "id": "leorio_paladinik", "name": "Leorio Paradinight (Doctor Hunter)", "anime": "Hunter x Hunter", "rarity": "Uncommon",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535995337179926528/f6b32030e281251977672c31d0c50acd.gif?ex=6a79caa1&is=6a787921&hm=6c5dded96a269bf3bef275b26de0f97e5609dcafafd8815eabd25ded6858e35a&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535995343060209846/hxh.gif?ex=6a79caa3&is=6a787923&hm=d264dcbad61cfd40aba48de3e49e59271168226e7c23f7d9fb79797e5c6e2d76&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535995354179305502/55898b241e9a13074aa31794948380be.gif?ex=6a79caa5&is=6a787925&hm=c06b4f1362606e711b4d0c3903dc553b4656986b6000cabe4935cb00c60b358a&"
    },
    {
        "id": "yoo_jinho", "name": "Yoo Jinho (Rich Guild Vice-Cap)", "anime": "Solo Leveling", "rarity": "Uncommon",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535996256248270868/images_1.jpeg?ex=6a79cb7c&is=6a7879fc&hm=e7d1d4056c54106f241537409f92b1e252bb5a75c8601ec7218afb8288f77c31&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535996256248270868/images_1.jpeg?ex=6a79cb7c&is=6a7879fc&hm=e7d1d4056c54106f241537409f92b1e252bb5a75c8601ec7218afb8288f77c31&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535996256248270868/images_1.jpeg?ex=6a79cb7c&is=6a7879fc&hm=e7d1d4056c54106f241537409f92b1e252bb5a75c8601ec7218afb8288f77c31&"
    },

    # ⚪ COMMON (سەرەتایی و ئاساییەکان)
    {
        "id": "buggy_clown", "name": "Buggy the Clown", "anime": "One Piece", "rarity": "Common",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535997011856457748/714b8df94f246661e28f8284d31748ea.gif?ex=6a79cc31&is=6a787ab1&hm=f93465e0f756885ce3945be5c1953827e713dc9de57178c9c1728f7e41e5f75e&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535997189929705512/buggy-the-clown-flipping-sword-muh4amfdcf1i2773.gif?ex=6a79cc5b&is=6a787adb&hm=0511859447d94c92e6ab32af03159b0efbfe074c871505d3dc4297e92985bcde&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535997195612856421/buggy-clown.gif?ex=6a79cc5c&is=6a787adc&hm=c1e88905d8722be34cbf32a1487d4952b079de452909bf6a92f2142cbe2ecd53&"
    },
    {
        "id": "tonpa_rookie", "name": "Tonpa (Rookie Crusher)", "anime": "Hunter x Hunter", "rarity": "Common",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535997486857199636/Tonpa_2011.PNG.webp?ex=6a79cca2&is=6a787b22&hm=4a64741729c8eec34e77bd66d00769755ba1c048661debc8a00922fd22c976bc&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535997497498013796/iwuwo6o3aaaa.jpg?ex=6a79cca4&is=6a787b24&hm=9c2b8418a5d2580db0275081b34d80c873b21c7ccfe81f1cccec9c1bb4a1219b&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535997492980748369/kzFeFrJ.jpg?ex=6a79cca3&is=6a787b23&hm=db9e462f30033c3c7b50615447050b1ef1056db8e3ba911c1f6574b49104a7f8&"
    },
    {
        "id": "panda_jkk", "name": "Panda Gorilla", "anime": "Jujutsu Kaisen", "rarity": "Common",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535997904617996422/jujutsu-kaisen-jjk_1.gif?ex=6a79cd05&is=6a787b85&hm=bb1a2c80b11586fb38ade1fd58af2ba993776ff17caa3353edff2bc699309e41&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535997889325572156/jujutsu-kaisen-jjk.gif?ex=6a79cd02&is=6a787b82&hm=fed48cf3b9128e560986b8fcc85611d803f561830eb50b513278ccddffe4b161&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535997898095853578/anime.gif?ex=6a79cd04&is=6a787b84&hm=262d517e247dd1c596866024c8e04b3a8a5086f892b1ff7aa100445b40343386&"
    },
    {
        "id": "murata_swordsman", "name": "Murata (Veteran Swordsman)", "anime": "Demon Slayer", "rarity": "Common",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1535998557855944854/images_2.jpeg?ex=6a79cda1&is=6a787c21&hm=901904db86c55d686c7af67154324ab4ad1f1a346ca4eb77c3cad469947cd4bc&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1535998571630043157/6d30172c251f2810602f295f274092ac.png?ex=6a79cda4&is=6a787c24&hm=507bf8b4bb26999bce5f08daff2ef2cfa1450b738844bc4b6fb2c6de91bba9e5&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1535998571630043157/6d30172c251f2810602f295f274092ac.png?ex=6a79cda4&is=6a787c24&hm=507bf8b4bb26999bce5f08daff2ef2cfa1450b738844bc4b6fb2c6de91bba9e5&"
    },
    {
        "id": "aoi_sakamoto_store", "name": "Aoi Sakamoto (Store Manager)", "anime": "Sakamoto Days", "rarity": "Common",
        "image_lvl1": "https://cdn.discordapp.com/attachments/1080163033948631091/1536003788408754286/sakamoto-sakamoto-days.gif?ex=6a79d280&is=6a788100&hm=a993181f0760290de968845c7678b4fe0aaffcf8afd16a26ea57f58d2eeb21ee&",
        "image_lvl2": "https://cdn.discordapp.com/attachments/1080163033948631091/1536003781261791373/images_3.jpeg?ex=6a79d27f&is=6a7880ff&hm=dd9b7e26b7aad97b82e43b1251a747084f9a07566bb0ee93ebd2b5489d8cf542&",
        "image_lvl3": "https://cdn.discordapp.com/attachments/1080163033948631091/1536003794398355618/whats-that-about-aoi-sakamoto.gif?ex=6a79d282&is=6a788102&hm=4c2c62b39be9878fe2360b34d41429c1ea0450490e61a0b594119c699ce215b2&"
    }
]
