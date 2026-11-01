import discord

# ناوی بوتەکە (لە فووتەری کارتەکان)
BOT_NAME = "Test bot"

# هێمای فەرمانەکان. تەنها لێرە بیگۆڕە، لە هەموو شوێنێک دەگۆڕێت
# نموونە: "z" یان "!z"
PREFIX = "z"

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
    
