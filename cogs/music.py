import asyncio
import random
from collections import deque

import discord
import yt_dlp
from discord.ext import commands

from utils import make_embed, PREFIX, SUCCESS, ERROR, WARN, PURPLE

# ═══════════════════════════════════════
# بەشی ١: ڕێکخستنەکان (لێرە دەستکاری بکە)
# ═══════════════════════════════════════

MAX_QUEUE = 50          # زۆرترین ژمارەی گۆرانی لەناو ڕیزەکە
DEFAULT_VOLUME = 0.5    # دەنگی بنەڕەتی (٠.٥ = ٥٠٪)
IDLE_LEAVE = 60         # ئەگەر کەس لە ژوورەکە نەما، دوای چەند چرکە بوت دەردەچێت

YTDL_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,      # تەنها یەک گۆرانی، نەک هەموو پلەی لیست
    "quiet": True,
    "no_warnings": True,
    "source_address": "0.0.0.0",
}
# reconnect: ئەگەر ئینتەرنێت پچڕا، خۆکار دووبارە دەبەستێتەوە
FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


# ═══════════════════════════════════════
# بەشی ٢: یارمەتیدەرەکان
# ═══════════════════════════════════════

# گۆرانییەک یان گەڕان دەدۆزێتەوە (کارێکی هێدییە، بۆیە لە executor دا کار دەکات)
def extract(query):
    if not query.startswith(("http://", "https://")):
        query = f"ytsearch1:{query}"
    with yt_dlp.YoutubeDL(YTDL_OPTS) as ytdl:
        info = ytdl.extract_info(query, download=False)
    if info and "entries" in info:
        entries = [e for e in info["entries"] if e]
        info = entries[0] if entries else None
    return info


def fmt_time(sec):
    if not sec:
        return "LIVE 🔴"
    sec = int(sec)
    hours, rest = divmod(sec, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"


class Track:
    def __init__(self, title, page_url, duration, thumb, requester):
        self.title = title
        self.page_url = page_url
        self.duration = duration
        self.thumb = thumb
        self.requester = requester


class GuildState:
    def __init__(self):
        self.queue = deque()
        self.current = None
        self.loop = False
        self.volume = DEFAULT_VOLUME
        self.channel = None  # ئەو کەناڵەی نامەکانی تێدا دەنێردرێت


def track_embed(title, track, color):
    embed = make_embed(title, f"**[{discord.utils.escape_markdown(track.title)}]({track.page_url})**", color=color)
    embed.add_field(name="⏱️ ماوە", value=f"`{fmt_time(track.duration)}`")
    embed.add_field(name="🙋 داواکار", value=discord.utils.escape_markdown(track.requester))
    if track.thumb:
        embed.set_thumbnail(url=track.thumb)
    return embed


# ═══════════════════════════════════════
# بەشی ٣: Cog ی میوزیک
# ═══════════════════════════════════════

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.states = {}  # guild_id -> GuildState

    async def cog_load(self):
        # Opus پێویستە بۆ دەنگ. لە Termux دەبێت `pkg install libopus` بکرێت
        if not discord.opus.is_loaded():
            for name in ("libopus.so", "libopus.so.0", "/data/data/com.termux/files/usr/lib/libopus.so"):
                try:
                    discord.opus.load_opus(name)
                    break
                except OSError:
                    continue

    async def cog_unload(self):
        for vc in list(self.bot.voice_clients):
            self.states.pop(vc.guild.id, None)
            await vc.disconnect(force=True)

    def state(self, guild_id):
        return self.states.setdefault(guild_id, GuildState())

    async def warn(self, ctx, title, text, color=WARN):
        await ctx.send(embed=make_embed(title, text, color=color, ctx=ctx), delete_after=8)

    # دڵنیابوونەوە: بوت لە ژوورێکی دەنگیدایە و ئەندامەکەش لەگەڵیدایە
    async def check_vc(self, ctx):
        vc = ctx.voice_client
        if vc is None:
            await self.warn(ctx, "⚠️ بوت لە ژووری دەنگیدا نییە", f"سەرەتا `{PREFIX}play <ناوی گۆرانی>` بنووسە.")
            return None
        if not ctx.author.voice or ctx.author.voice.channel != vc.channel:
            await self.warn(ctx, "⚠️ ژووری دەنگی", "دەبێت لەگەڵ بوت لە هەمان ژووری دەنگیدا بیت.")
            return None
        return vc

    async def cleanup(self, guild):
        self.states.pop(guild.id, None)
        vc = guild.voice_client
        if vc:
            await vc.disconnect(force=True)

    # ─── گۆرانی دواتر دەست پێ دەکات ───
    async def play_next(self, guild):
        vc = guild.voice_client
        if vc is None:
            return
        st = self.state(guild.id)

        if st.loop and st.current:
            track = st.current
        elif st.queue:
            track = st.queue.popleft()
        else:
            st.current = None
            return
        # current پێش هەر await ێک دادەنرێت، تا دوو !play ی هاوکات تێک نەچن
        st.current = track

        try:
            info = await self.bot.loop.run_in_executor(None, extract, track.page_url)
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(info["url"], **FFMPEG_OPTS), volume=st.volume
            )

            def after(error):
                if error:
                    print(f"هەڵەی لێدان: {error}")
                asyncio.run_coroutine_threadsafe(self.play_next(guild), self.bot.loop)

            vc.play(source, after=after)
        except Exception as e:
            print(f"هەڵەی میوزیک: {e}")
            st.current = None
            if st.channel:
                await st.channel.send(
                    embed=make_embed("❌ نەتوانرا بلێدرێت", f"**{track.title}** تێپەڕێنرا.", color=ERROR),
                    delete_after=8,
                )
            await self.play_next(guild)
            return

        if st.channel:
            try:
                await st.channel.send(embed=track_embed("🎶 ئێستا دەلێدرێت", track, PURPLE))
            except discord.HTTPException:
                pass

    # ─── فەرمانەکان ───

    # !play ناوی گۆرانی یان لینکی YouTube
    @commands.command(name="play", aliases=["p", "لێدان"])
    @commands.guild_only()
    async def play(self, ctx, *, query: str):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await self.warn(ctx, "⚠️ ژووری دەنگی", "سەرەتا بچۆ ناو ژوورێکی دەنگی.")
            return
        channel = ctx.author.voice.channel
        if ctx.voice_client and ctx.voice_client.channel != channel:
            await self.warn(ctx, "⚠️ بوت مەشغوولە", "بوت لە ژوورێکی ترە. دەبێت بچیتە ئەوێ.")
            return

        st = self.state(ctx.guild.id)
        if len(st.queue) >= MAX_QUEUE:
            await self.warn(ctx, "⚠️ ڕیزەکە پڕە", f"زۆرترین ژمارە `{MAX_QUEUE}` گۆرانییە.")
            return

        async with ctx.typing():
            try:
                info = await self.bot.loop.run_in_executor(None, extract, query)
            except Exception as e:
                print(f"هەڵەی yt-dlp: {e}")
                info = None
        if not info:
            await self.warn(ctx, "❌ نەدۆزرایەوە", "هیچ گۆرانییەک نەدۆزرایەوە.", ERROR)
            return

        vc = ctx.voice_client
        if vc is None:
            try:
                vc = await channel.connect(self_deaf=True)
            except (discord.ClientException, asyncio.TimeoutError, discord.Forbidden):
                await self.warn(ctx, "❌ هەڵە", "بوت نەیتوانی بچێتە ناو ژووری دەنگی (ڕێگەی Connect/Speak؟).", ERROR)
                return

        track = Track(
            title=info.get("title") or "؟",
            page_url=info.get("webpage_url") or info.get("original_url") or query,
            duration=info.get("duration"),
            thumb=info.get("thumbnail"),
            requester=ctx.author.display_name,
        )
        st.channel = ctx.channel
        st.queue.append(track)

        if st.current is None:
            await self.play_next(ctx.guild)
        else:
            embed = track_embed("➕ زیادکرا بۆ ڕیزەکە", track, SUCCESS)
            embed.add_field(name="📍 شوێن", value=f"`#{len(st.queue)}`")
            await ctx.send(embed=embed)

    # !pause
    @commands.command(name="pause")
    @commands.guild_only()
    async def pause(self, ctx):
        vc = await self.check_vc(ctx)
        if vc and vc.is_playing():
            vc.pause()
            await ctx.send(embed=make_embed("⏸️ ڕاگیرا", color=WARN, ctx=ctx))

    # !resume
    @commands.command(name="resume", aliases=["unpause"])
    @commands.guild_only()
    async def resume(self, ctx):
        vc = await self.check_vc(ctx)
        if vc and vc.is_paused():
            vc.resume()
            await ctx.send(embed=make_embed("▶️ بەردەوام بوو", color=SUCCESS, ctx=ctx))

    # !skip (ئاگادار: s بۆ slots ـە، بۆیە لێرە نییە)
    @commands.command(name="skip", aliases=["next", "تێپەڕە"])
    @commands.guild_only()
    async def skip(self, ctx):
        vc = await self.check_vc(ctx)
        if vc and (vc.is_playing() or vc.is_paused()):
            st = self.state(ctx.guild.id)
            st.current = None  # بۆ ئەوەی loop ی هەمان گۆرانی دووبارە نەکاتەوە
            vc.stop()          # after() خۆی گۆرانی دواتر دەست پێ دەکات
            await ctx.send(embed=make_embed("⏭️ تێپەڕێنرا", color=SUCCESS, ctx=ctx))

    # !stop: ڕیز دەسڕێتەوە و دەوەستێت (بوت لە ژوورەکە دەمێنێتەوە)
    @commands.command(name="stop")
    @commands.guild_only()
    async def stop(self, ctx):
        vc = await self.check_vc(ctx)
        if not vc:
            return
        st = self.state(ctx.guild.id)
        st.queue.clear()
        st.loop = False
        if vc.is_playing() or vc.is_paused():
            vc.stop()
        else:
            st.current = None
        await ctx.send(embed=make_embed("⏹️ وەستا و ڕیزەکە سڕایەوە", color=WARN, ctx=ctx))

    # !leave
    @commands.command(name="leave", aliases=["dc", "disconnect"])
    @commands.guild_only()
    async def leave(self, ctx):
        vc = await self.check_vc(ctx)
        if vc:
            await self.cleanup(ctx.guild)
            await ctx.send(embed=make_embed("👋 بوت دەرچوو", color=WARN, ctx=ctx))

    # !queue
    @commands.command(name="queue", aliases=["q", "ڕیز"])
    @commands.guild_only()
    async def queue(self, ctx):
        st = self.state(ctx.guild.id)
        if not st.current and not st.queue:
            await self.warn(ctx, "📭 ڕیزەکە بەتاڵە", f"`{PREFIX}play <گۆرانی>` بنووسە.")
            return
        lines = []
        if st.current:
            lines.append(f"🎶 **ئێستا:** {discord.utils.escape_markdown(st.current.title)} `{fmt_time(st.current.duration)}`")
        for i, t in enumerate(list(st.queue)[:10], start=1):
            lines.append(f"`{i}.` {discord.utils.escape_markdown(t.title)} `{fmt_time(t.duration)}`")
        if len(st.queue) > 10:
            lines.append(f"... و **{len(st.queue) - 10}** گۆرانی تر")
        embed = make_embed("📜 ڕیزی گۆرانییەکان", "\n".join(lines), color=PURPLE, ctx=ctx)
        embed.add_field(name="🔁 Loop", value="چالاکە" if st.loop else "ناچالاکە")
        embed.add_field(name="🔊 دەنگ", value=f"`{int(st.volume * 100)}%`")
        await ctx.send(embed=embed)

    # !nowplaying
    @commands.command(name="nowplaying", aliases=["np", "ئێستا"])
    @commands.guild_only()
    async def nowplaying(self, ctx):
        st = self.state(ctx.guild.id)
        if not st.current:
            await self.warn(ctx, "📭 هیچ نالێدرێت", f"`{PREFIX}play <گۆرانی>` بنووسە.")
            return
        await ctx.send(embed=track_embed("🎶 ئێستا دەلێدرێت", st.current, PURPLE))

    # !volume 70
    @commands.command(name="volume", aliases=["vol", "v"])
    @commands.guild_only()
    async def volume(self, ctx, level: int = None):
        vc = await self.check_vc(ctx)
        if not vc:
            return
        st = self.state(ctx.guild.id)
        if level is None:
            await ctx.send(embed=make_embed("🔊 دەنگ", f"`{int(st.volume * 100)}%`", color=PURPLE, ctx=ctx))
            return
        if not 1 <= level <= 100:
            await self.warn(ctx, "⚠️ ژمارە هەڵەیە", "ژمارەیەک لە نێوان `1` و `100` بنووسە.")
            return
        st.volume = level / 100
        if isinstance(vc.source, discord.PCMVolumeTransformer):
            vc.source.volume = st.volume
        await ctx.send(embed=make_embed("🔊 دەنگ گۆڕدرا", f"`{level}%`", color=SUCCESS, ctx=ctx))

    # !loop: گۆرانی ئێستا دووبارە دەکاتەوە
    @commands.command(name="loop", aliases=["repeat"])
    @commands.guild_only()
    async def loop(self, ctx):
        vc = await self.check_vc(ctx)
        if not vc:
            return
        st = self.state(ctx.guild.id)
        st.loop = not st.loop
        text = "🔁 Loop چالاک کرا" if st.loop else "➡️ Loop ناچالاک کرا"
        await ctx.send(embed=make_embed(text, color=SUCCESS if st.loop else WARN, ctx=ctx))

    # !shuffle
    @commands.command(name="shuffle", aliases=["mix"])
    @commands.guild_only()
    async def shuffle(self, ctx):
        vc = await self.check_vc(ctx)
        if not vc:
            return
        st = self.state(ctx.guild.id)
        if len(st.queue) < 2:
            await self.warn(ctx, "⚠️ ڕیزەکە کورتە", "پێویستە لانیکەم `2` گۆرانی لە ڕیزەکەدا بن.")
            return
        items = list(st.queue)
        random.shuffle(items)
        st.queue = deque(items)
        await ctx.send(embed=make_embed("🔀 ڕیزەکە تێکەڵ کرا", color=SUCCESS, ctx=ctx))

    # ─── ئەگەر کەس لە ژوورەکە نەما، بوت دەردەچێت ───
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild = member.guild
        # بوتەکە خۆی دەرکرا یان بەستنەوەی پچڕا
        if member.id == self.bot.user.id and after.channel is None:
            self.states.pop(guild.id, None)
            return
        vc = guild.voice_client
        if vc is None or vc.channel is None:
            return
        if before.channel == vc.channel and after.channel != vc.channel:
            if all(m.bot for m in vc.channel.members):
                await asyncio.sleep(IDLE_LEAVE)
                vc = guild.voice_client
                if vc and vc.channel and all(m.bot for m in vc.channel.members):
                    await self.cleanup(guild)


async def setup(bot):
    await bot.add_cog(Music(bot))
          
