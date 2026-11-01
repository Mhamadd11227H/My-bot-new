import os
import discord
from discord.ext import commands

# ═══════════════════════════════════════
# بەشی ١: ڕێکخستنی بنەڕەتی
# ═══════════════════════════════════════

# intents: ئەو شتانەن کە بوتەکە ڕێگەی پێدراوە ببینێت
intents = discord.Intents.default()
intents.message_content = True  # بۆ خوێندنەوەی نامەکان
intents.members = True          # بۆ بینینی ئەندامەکان

# command_prefix: ئەو هێمایەی فەرمانەکان پێ دەست پێ دەکەن
# بۆ نموونە !ping. دەتوانیت بیگۆڕیت بۆ "." یان "-"
bot = commands.Bot(command_prefix="!", intents=intents)

# ═══════════════════════════════════════
# بەشی ٢: ڕێکخستنەکان (لێرە دەستکاری بکە)
# ═══════════════════════════════════════

# ناوی ئەو ڕۆڵەی بە ئەندامی نوێ دەدرێت.
# ناوەکە دەبێت وەک خۆی لە سێرڤەرەکەت هەبێت
AUTO_ROLE_NAME = "Member"

# ═══════════════════════════════════════
# بەشی ٣: کاتێک بوتەکە ئۆنلاین دەبێت
# ═══════════════════════════════════════

@bot.event
async def on_ready():
    print(f"بوت ئۆنلاین بوو: {bot.user}")

# ═══════════════════════════════════════
# بەشی ٤: فەرمانە سادەکان
# ═══════════════════════════════════════

# !سڵاو: بوتەکە سڵاو دەکات و ناوی تۆ mention دەکات
@bot.command(name="سڵاو")
async def hello(ctx):
    await ctx.send(f"سڵاو {ctx.author.mention}! 👋")

# !ping: خێرایی بوتەکە پیشان دەدات
@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

# ═══════════════════════════════════════
# بەشی ٥: مۆدەراسیۆن (بەڕێوەبردنی سێرڤەر)
# ═══════════════════════════════════════

# !kick @کەس هۆکار: ئەندامێک دەرەوە دەکات (دەتوانێت دووبارە بێتەوە)
# has_permissions: تەنها ئەو کەسانە دەتوانن بەکاری بهێنن کە ڕێگەیان هەیە
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="هۆکار نەنووسراوە"):
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member.mention} دەرکرا. هۆکار: {reason}")

# !ban @کەس هۆکار: ئەندامێک بۆ هەمیشە بلۆک دەکات
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="هۆکار نەنووسراوە"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.mention} بلۆک کرا. هۆکار: {reason}")

# !unban ناو: بلۆکی کەسێک لادەبات. دەبێت ناوی بەکارهێنەرەکە بنووسیت
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, username):
    async for entry in ctx.guild.bans():
        if entry.user.name == username:
            await ctx.guild.unban(entry.user)
            await ctx.send(f"✅ بلۆکی {entry.user.name} لابرا")
            return
    await ctx.send("❌ ئەو کەسە لە لیستی بلۆککراوەکان نەدۆزرایەوە")

# !clear ژمارە: چەند نامەیەک دەسڕێتەوە (بنەڕەت: ٥)
# amount + 1: چونکە نامەی فەرمانەکەی خۆشت دەسڕێتەوە
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    # delete_after=3: نامەکە دوای ٣ چرکە خۆی دەسڕێتەوە
    await ctx.send(f"🧹 {amount} نامە سڕایەوە", delete_after=3)

# ═══════════════════════════════════════
# بەشی ٦: ڕۆڵی خۆکار + بەخێرهاتن
# ═══════════════════════════════════════

# کاتێک ئەندامێکی نوێ دێتە ژوورەوە ئەمە کار دەکات
@bot.event
async def on_member_join(member):
    # ١) ڕۆڵەکە بدۆزەرەوە بە ناو
    role = discord.utils.get(member.guild.roles, name=AUTO_ROLE_NAME)
    if role:
        await member.add_roles(role)

    # ٢) نامەی بەخێرهاتن بنێرە لە کەناڵی سەرەکی سێرڤەر
    channel = member.guild.system_channel
    if channel:
        await channel.send(f"بەخێربێیت {member.mention} بۆ سێرڤەرەکەمان! 🎉")

# ═══════════════════════════════════════
# بەشی ٧: زانیاری
# ═══════════════════════════════════════

# !user یان !user @کەس: زانیاری ئەندامێک پیشان دەدات
# member=None: ئەگەر کەسێک دیاری نەکرا، زانیاری خودی تۆ پیشان دەدات
@bot.command()
async def user(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=member.name, color=0x5865F2)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ناسنامە (ID)", value=member.id, inline=False)
    embed.add_field(
        name="جۆینی سێرڤەری کرد",
        value=member.joined_at.strftime("%Y-%m-%d"),
    )
    embed.add_field(
        name="ئەکاونتی دروست کرد",
        value=member.created_at.strftime("%Y-%m-%d"),
    )
    await ctx.send(embed=embed)

# !server: زانیاری سێرڤەرەکە پیشان دەدات
@bot.command()
async def server(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=guild.name, color=0x5865F2)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="ژمارەی ئەندامان", value=guild.member_count)
    embed.add_field(name="خاوەن", value=guild.owner.mention if guild.owner else "نەزانراو")
    embed.add_field(
        name="دروست کرا",
        value=guild.created_at.strftime("%Y-%m-%d"),
    )
    await ctx.send(embed=embed)

# ═══════════════════════════════════════
# بەشی ٨: مامەڵەکردن لەگەڵ هەڵەکان
# ═══════════════════════════════════════

# ئەگەر کەسێک فەرمانێک بەکاربهێنێت بێ ڕێگە، ئەمە پەیامێک دەنێرێت
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ تۆ ڕێگەت نییە ئەم فەرمانە بەکار بهێنیت")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ ئەو ئەندامە نەدۆزرایەوە")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ فەرمانەکە تەواو نەنووسراوە")
    elif isinstance(error, commands.CommandNotFound):
        pass  # فەرمانی نەناسراو: هیچ ناکات
    else:
        print(f"هەڵە: {error}")

# ═══════════════════════════════════════
# کۆتایی: بوتەکە دەست پێ دەکات
# ═══════════════════════════════════════

bot.run(os.environ["DISCORD_TOKEN"])
