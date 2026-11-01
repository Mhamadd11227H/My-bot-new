import os
import discord
from discord.ext import commands

# ڕەنگەکان و فەرمانی دروستکردنی کارتەکان لە فایلی utils.py هاتوون
from utils import make_embed, PREFIX, MAIN, SUCCESS, ERROR, WARN

# ═══════════════════════════════════════
# بەشی ١: ڕێکخستنی بنەڕەتی
# ═══════════════════════════════════════

intents = discord.Intents.default()
intents.message_content = True  # بۆ خوێندنەوەی نامەکان
intents.members = True          # بۆ بینینی ئەندامەکان

# help_command=None: چونکە help ی خۆمان لە cogs/help.py دروست کردووە
# when_mentioned_or: mention کردنی بوتەکەش وەک هێما کار دەکات
# PREFIX.upper(): پیتی گەورەش کار دەکات (z و Z)
# strip_after_prefix: بۆشایی دوای هێما کێشە نییە (z ping)
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(PREFIX, PREFIX.upper()),
    intents=intents,
    help_command=None,
    strip_after_prefix=True,
)

# ناوی ئەو ڕۆڵەی بە ئەندامی نوێ دەدرێت (دەبێت وەک خۆی لە سێرڤەر هەبێت)
AUTO_ROLE_NAME = "Member"

# ═══════════════════════════════════════
# بەشی ٢: خوێندنەوەی فایلەکانی cogs
# ═══════════════════════════════════════

# ئەم بەشە کاتێک بوتەکە دەست پێ دەکات کار دەکات
# و فایلی help دەخوێنێتەوە. فایلی نوێت هەبوو، لێرە دێڕێکی نوێ زیاد بکە:
# await bot.load_extension("cogs.ناوی_فایل")
async def setup_hook():
    await bot.load_extension("cogs.help")
    await bot.load_extension("cogs.economy")  # دراو: cash, daily, coinflip
    await bot.load_extension("cogs.slots")    # یاری سلۆت

bot.setup_hook = setup_hook

# ═══════════════════════════════════════
# بەشی ٣: کاتێک بوتەکە ئۆنلاین دەبێت
# ═══════════════════════════════════════

@bot.event
async def on_ready():
    print(f"بوت ئۆنلاین بوو: {bot.user}")
    # ستاتوسی بوتەکە: "Watching !help"
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=f"{PREFIX}help")
    )

# ═══════════════════════════════════════
# بەشی ٤: فەرمانە سادەکان
# ═══════════════════════════════════════

# !سڵاو: سڵاو کردن
@bot.command(name="سڵاو")
async def hello(ctx):
    embed = make_embed(
        "👋 سڵاو!",
        f"سڵاو {ctx.author.mention}، بەخێربێیت!\nبۆ بینینی فەرمانەکان بنووسە `{PREFIX}help`",
        ctx=ctx,
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# !ping: خێرایی بوتەکە. ڕەنگەکە بەپێی خێرایی دەگۆڕێت
@bot.command()
async def ping(ctx):
    ms = round(bot.latency * 1000)
    # خێرا = سەوز، ناوەند = زەرد، هێدی = سوور
    if ms < 150:
        color, status = SUCCESS, "زۆر خێرا ⚡"
    elif ms < 300:
        color, status = WARN, "ئاسایی 👍"
    else:
        color, status = ERROR, "هێدی 🐢"
    embed = make_embed("🏓 Pong!", color=color, ctx=ctx)
    embed.add_field(name="خێرایی", value=f"`{ms}ms`")
    embed.add_field(name="دۆخ", value=status)
    await ctx.send(embed=embed)

# ═══════════════════════════════════════
# بەشی ٥: مۆدەراسیۆن
# ═══════════════════════════════════════

# !kick @کەس هۆکار: ئەندامێک دەردەکات
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="هۆکار نەنووسراوە"):
    await member.kick(reason=reason)
    embed = make_embed("👢 ئەندامێک دەرکرا", color=WARN, ctx=ctx)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ئەندام", value=member.mention)
    embed.add_field(name="بەڕێوەبەر", value=ctx.author.mention)
    embed.add_field(name="هۆکار", value=reason, inline=False)
    await ctx.send(embed=embed)

# !ban @کەس هۆکار: ئەندامێک بلۆک دەکات
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="هۆکار نەنووسراوە"):
    await member.ban(reason=reason)
    embed = make_embed("🔨 ئەندامێک بلۆک کرا", color=ERROR, ctx=ctx)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ئەندام", value=member.mention)
    embed.add_field(name="بەڕێوەبەر", value=ctx.author.mention)
    embed.add_field(name="هۆکار", value=reason, inline=False)
    await ctx.send(embed=embed)

# !unban ناو: بلۆکی کەسێک لادەبات
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, username):
    async for entry in ctx.guild.bans():
        if entry.user.name == username:
            await ctx.guild.unban(entry.user)
            embed = make_embed(
                "✅ بلۆک لابرا", f"بلۆکی **{entry.user.name}** لابرا.", color=SUCCESS, ctx=ctx
            )
            await ctx.send(embed=embed)
            return
    embed = make_embed(
        "❌ نەدۆزرایەوە", "ئەو کەسە لە لیستی بلۆککراوەکان نییە.", color=ERROR, ctx=ctx
    )
    await ctx.send(embed=embed)

# !clear ژمارە: نامەکان دەسڕێتەوە
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    # ژمارەکە دەبێت لە نێوان ١ و ١٠٠ بێت
    if amount < 1 or amount > 100:
        embed = make_embed(
            "⚠️ ژمارە هەڵەیە", "ژمارەیەک لە نێوان `1` و `100` بنووسە.", color=WARN, ctx=ctx
        )
        await ctx.send(embed=embed, delete_after=5)
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    # len(deleted) - 1: چونکە نامەی فەرمانەکەی خۆشت دەسڕێتەوە
    embed = make_embed(
        "🧹 پاککرایەوە", f"**{len(deleted) - 1}** نامە سڕایەوە.", color=SUCCESS, ctx=ctx
    )
    await ctx.send(embed=embed, delete_after=4)  # دوای ٤ چرکە خۆی دەسڕێتەوە

# ═══════════════════════════════════════
# بەشی ٦: ڕۆڵی خۆکار + بەخێرهاتن
# ═══════════════════════════════════════

@bot.event
async def on_member_join(member):
    # ١) ڕۆڵەکە بدە
    role = discord.utils.get(member.guild.roles, name=AUTO_ROLE_NAME)
    if role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            print("بوتەکە ناتوانێت ڕۆڵ بدات: ڕۆڵی بوت دەبێت بەرزتر بێت")

    # ٢) نامەی بەخێرهاتنی جوان
    channel = member.guild.system_channel
    if channel:
        embed = make_embed(
            "🎉 بەخێربێیت!",
            f"{member.mention} هاتە ناو **{member.guild.name}**\nهیوادارین کاتێکی خۆش بەسەر ببەیت 💙",
            color=SUCCESS,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ژمارەی ئەندام", value=f"#{member.guild.member_count}")
        embed.add_field(
            name="ئەکاونتی دروست کرا",
            value=discord.utils.format_dt(member.created_at, "R"),
        )
        await channel.send(embed=embed)

# ═══════════════════════════════════════
# بەشی ٧: زانیاری
# ═══════════════════════════════════════

# !user یان !user @کەس: زانیاری ئەندامێک
@bot.command()
async def user(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = make_embed(
        f"👤 {member.display_name}",
        color=member.color if member.color.value else MAIN,
        ctx=ctx,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ناسنامە (ID)", value=f"`{member.id}`", inline=False)
    embed.add_field(
        name="جۆینی سێرڤەری کرد",
        value=discord.utils.format_dt(member.joined_at, "D"),
    )
    embed.add_field(
        name="ئەکاونتی دروست کرد",
        value=discord.utils.format_dt(member.created_at, "D"),
    )
    embed.add_field(name="بەرزترین ڕۆڵ", value=member.top_role.mention, inline=False)
    await ctx.send(embed=embed)

# !server: زانیاری سێرڤەر
@bot.command()
async def server(ctx):
    g = ctx.guild
    embed = make_embed(f"🏠 {g.name}", color=MAIN, ctx=ctx)
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="👥 ئەندامان", value=g.member_count)
    embed.add_field(name="💬 کەناڵەکان", value=len(g.channels))
    embed.add_field(name="🎭 ڕۆڵەکان", value=len(g.roles))
    embed.add_field(name="👑 خاوەن", value=g.owner.mention if g.owner else "نەزانراو")
    embed.add_field(
        name="📅 دروست کرا", value=discord.utils.format_dt(g.created_at, "D")
    )
    await ctx.send(embed=embed)

# ═══════════════════════════════════════
# بەشی ٨: هەڵەکان (بە شێوەی جوان)
# ═══════════════════════════════════════

@bot.event
async def on_command_error(ctx, error):
    # هەندێک هەڵە لەناو هەڵەی تر شاراوەنەتەوە، ئەمە دەریدەهێنێت
    error = getattr(error, "original", error)

    if isinstance(error, commands.MissingPermissions):
        text = "تۆ ڕێگەی بەکارهێنانی ئەم فەرمانەت نییە."
    elif isinstance(error, commands.MemberNotFound):
        text = "ئەو ئەندامە نەدۆزرایەوە."
    elif isinstance(error, commands.MissingRequiredArgument):
        text = f"فەرمانەکە تەواو نەنووسراوە. بۆ یارمەتی: `{PREFIX}help`"
    elif isinstance(error, commands.BadArgument):
        text = "نرخێکی هەڵەت نووسیوە (بۆ نموونە ژمارە پێویستە)."
    elif isinstance(error, discord.Forbidden):
        text = "بوتەکە ڕێگەی ئەم کارەی نییە. ڕۆڵی بوتەکە دەبێت لە سەرووی ڕۆڵی ئەو کەسەوە بێت."
    elif isinstance(error, commands.CommandNotFound):
        return  # فەرمانی نەناسراو: هیچ ناکات
    else:
        print(f"هەڵە: {error}")
        text = "هەڵەیەکی چاوەڕواننەکراو ڕوویدا."

    embed = make_embed("❌ هەڵە", text, color=ERROR, ctx=ctx)
    await ctx.send(embed=embed, delete_after=8)

# ═══════════════════════════════════════
# کۆتایی: بوتەکە دەست پێ دەکات
# ═══════════════════════════════════════

bot.run(os.environ["DISCORD_TOKEN"])
    
