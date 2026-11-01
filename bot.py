import os
import discord
from discord.ext import commands

# ═══════════════════════════════════════
# بەشی ١: ڕێکخستنی بنەڕەتی
# ═══════════════════════════════════════

intents = discord.Intents.default()
intents.message_content = True  # بۆ خوێندنەوەی نامەکان
intents.members = True          # بۆ بینینی ئەندامەکان

# help_command=None: فەرمانی help ـی سادەی ئاسایی دەکوژێنین
# چونکە خۆمان یەکێکی جوانتر دروست دەکەین
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ═══════════════════════════════════════
# بەشی ٢: ڕێکخستنەکان (لێرە دەستکاری بکە)
# ═══════════════════════════════════════

AUTO_ROLE_NAME = "Member"   # ناوی ڕۆڵی ئەندامی نوێ
BOT_NAME = "Test bot"       # ناوی بوتەکە لە فووتەر

# ڕەنگەکان. دەتوانیت کۆدی هێکس بگۆڕیت بۆ هەر ڕەنگێک
MAIN = 0x5865F2      # شین (زانیاری)
SUCCESS = 0x2ECC71   # سەوز (سەرکەوتن)
ERROR = 0xE74C3C     # سوور (هەڵە)
WARN = 0xF1C40F      # زەرد (ئاگاداری)

# ═══════════════════════════════════════
# بەشی ٣: فەرمانی یارمەتیدەر بۆ دروستکردنی کارتی جوان
# ═══════════════════════════════════════

# ئەم فەرمانە هەموو کارتەکان دروست دەکات، بۆیە ئەگەر لێرە شتێک بگۆڕیت
# هەموو بوتەکە دەگۆڕێت (ڕەنگ، فووتەر، هتد)
def make_embed(title, description=None, color=MAIN, ctx=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=discord.utils.utcnow(),  # کاتی نامەکە لە خوارەوە
    )
    if ctx:
        # فووتەر: "داواکراوە لەلایەن ناوی کەس" لەگەڵ وێنەکەی
        embed.set_footer(
            text=f"داواکراوە لەلایەن {ctx.author.display_name} • {BOT_NAME}",
            icon_url=ctx.author.display_avatar.url,
        )
    else:
        embed.set_footer(text=BOT_NAME)
    return embed

# ═══════════════════════════════════════
# بەشی ٤: کاتێک بوتەکە ئۆنلاین دەبێت
# ═══════════════════════════════════════

@bot.event
async def on_ready():
    print(f"بوت ئۆنلاین بوو: {bot.user}")
    # ستاتوسی بوتەکە: "Watching !help" لە لیستی ئەندامان دەردەکەوێت
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="!help")
    )

# ═══════════════════════════════════════
# بەشی ٥: فەرمانە سادەکان
# ═══════════════════════════════════════

# !help: لیستی هەموو فەرمانەکان
@bot.command()
async def help(ctx):
    embed = make_embed("📖 لیستی فەرمانەکان", "ئەمانە ئەو فەرمانانەن کە دەتوانیت بەکاریان بهێنیت:", ctx=ctx)
    embed.add_field(
        name="🌟 گشتی",
        value="`!ping` • `!سڵاو` • `!user` • `!server`",
        inline=False,
    )
    embed.add_field(
        name="🛡️ مۆدەراسیۆن",
        value="`!kick` • `!ban` • `!unban` • `!clear`",
        inline=False,
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)

# !سڵاو: سڵاو کردن
@bot.command(name="سڵاو")
async def hello(ctx):
    embed = make_embed("👋 سڵاو!", f"سڵاو {ctx.author.mention}، بەخێربێیت!\nبۆ بینینی فەرمانەکان بنووسە `!help`", ctx=ctx)
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
# بەشی ٦: مۆدەراسیۆن
# ═══════════════════════════════════════

# !kick @کەس هۆکار
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

# !ban @کەس هۆکار
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

# !unban ناو
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, username):
    async for entry in ctx.guild.bans():
        if entry.user.name == username:
            await ctx.guild.unban(entry.user)
            embed = make_embed("✅ بلۆک لابرا", f"بلۆکی **{entry.user.name}** لابرا.", color=SUCCESS, ctx=ctx)
            await ctx.send(embed=embed)
            return
    embed = make_embed("❌ نەدۆزرایەوە", "ئەو کەسە لە لیستی بلۆککراوەکان نییە.", color=ERROR, ctx=ctx)
    await ctx.send(embed=embed)

# !clear ژمارە
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    # ژمارەکە دەبێت لە نێوان ١ و ١٠٠ بێت
    if amount < 1 or amount > 100:
        embed = make_embed("⚠️ ژمارە هەڵەیە", "ژمارەیەک لە نێوان `1` و `100` بنووسە.", color=WARN, ctx=ctx)
        await ctx.send(embed=embed, delete_after=5)
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    # len(deleted) - 1: چونکە نامەی فەرمانەکەی خۆشت دەسڕێتەوە
    embed = make_embed("🧹 پاککرایەوە", f"**{len(deleted) - 1}** نامە سڕایەوە.", color=SUCCESS, ctx=ctx)
    await ctx.send(embed=embed, delete_after=4)  # دوای ٤ چرکە خۆی دەسڕێتەوە

# ═══════════════════════════════════════
# بەشی ٧: ڕۆڵی خۆکار + بەخێرهاتن
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
        embed.add_field(name="ئەکاونتی دروست کرا", value=discord.utils.format_dt(member.created_at, "R"))
        await channel.send(embed=embed)

# ═══════════════════════════════════════
# بەشی ٨: زانیاری
# ═══════════════════════════════════════

# !user یان !user @کەس
# format_dt(...): بەرواری جوان کە بۆ هەر کەسێک بە کاتی خۆی دەردەکەوێت
@bot.command()
async def user(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = make_embed(f"👤 {member.display_name}", color=member.color if member.color.value else MAIN, ctx=ctx)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ناسنامە (ID)", value=f"`{member.id}`", inline=False)
    embed.add_field(name="جۆینی سێرڤەری کرد", value=discord.utils.format_dt(member.joined_at, "D"))
    embed.add_field(name="ئەکاونتی دروست کرد", value=discord.utils.format_dt(member.created_at, "D"))
    embed.add_field(name="بەرزترین ڕۆڵ", value=member.top_role.mention, inline=False)
    await ctx.send(embed=embed)

# !server
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
    embed.add_field(name="📅 دروست کرا", value=discord.utils.format_dt(g.created_at, "D"))
    await ctx.send(embed=embed)

# ═══════════════════════════════════════
# بەشی ٩: هەڵەکان (بە شێوەی جوان)
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
        text = "فەرمانەکە تەواو نەنووسراوە. بۆ یارمەتی: `!help`"
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
# کۆتایی
# ═══════════════════════════════════════

bot.run(os.environ["DISCORD_TOKEN"])
