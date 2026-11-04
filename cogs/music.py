import asyncio
import math
import os
import random
import shlex
import time
from dataclasses import dataclass
from typing import Optional

import discord
from discord.ext import commands
import yt_dlp

from utils import make_embed, PREFIX, BOT_NAME, PURPLE, GOLD, SUCCESS, ERROR, WARN

# ═══════════════════════════════════════
# Zero Music ─ بەشی میوزیک
# - کارتەکان بە make_embed ی utils.py دروست دەبن (هەمان دیزاینی بوتەکە)
# - هێما لە utils.py وەردەگیرێت: z play / zero play / z! play
# - لە bot.py دا زیادی بکە:  await bot.load_extension("cogs.music")
# پێویستی: pip install yt-dlp PyNaCl   +   pkg install ffmpeg libopus (Termux)
# ═══════════════════════════════════════

# ═══════════════════════════════════════
# بەشی ١: ڕێکخستنەکان (لێرە دەستکاری بکە)
# ═══════════════════════════════════════

DEFAULT_VOLUME = 0.8          # دەنگی سەرەتا (٨٠٪)
MAX_VOLUME = 1.5              # بەرزترین دەنگ (١٥٠٪)
VOLUME_STEP = 0.1             # هەر کلیکێکی 🔉 / 🔊 چەند دەگۆڕێت (١٠٪)
MAX_QUEUE = 50                # زۆرترین گۆرانی لە ڕیزبەندیدا
MAX_SONG_MINUTES = 720        # درێژترین گۆرانی (بە خولەک). ٧٢٠ = ١٢ کاتژمێر. 0 = بێ سنوور
STREAM_OVER_MINUTES = 30      # گۆرانی لەمە درێژتر دانابەزێت و ڕاستەوخۆ stream دەکرێت (باشترە بۆ ڤیدیۆی ١٠ کاتژمێری). 0 = هەمووی دابەزێنە
MAX_STREAM_RETRIES = 8        # ئەگەر stream پچڕا، چەند جار دووبارە لەو شوێنەوە بەردەوام بێت
IDLE_DISCONNECT = 120         # ئەگەر هیچ نەلێدرا، دوای چەند چرکە بچێتە دەرەوە
ALONE_DISCONNECT = 60         # ئەگەر بوت تەنها مایەوە لە ڤۆیس، دوای چەند چرکە بچێتە دەرەوە
PROGRESS_REFRESH = 8          # نوێکردنەوەی شریتی کات (چرکە). لە ٥ کەمتر مەیکە، Discord سنووری هەیە
BAR_LENGTH = 14               # درێژی شریتی کات
QUEUE_PER_PAGE = 8            # چەند گۆرانی لە هەر پەڕەیەکی ڕیزبەندی
MENU_IMAGE = None             # وێنەی داشبۆرد (لینک). ئەگەر نەتەوێت: None
STAY_IN_VOICE = False         # True = بوت هەرگیز بە خۆی لە ڤۆیس دەرناچێت (٢٤/٧). تەنها بە z stop دەچێتە دەرەوە
AUDIO_FILTER = "dynaudnorm=f=150:g=15"  # دەنگی هاوسەنگ و ساف (دەنگی گۆرانییەکان یەکسان دەکات). نەتەوێت: ""
BIG_COVER = True              # True = وێنەی گۆرانی گەورە (وەک Spotify). False = وێنەی بچووک لە لاوە
UPNEXT_SHOWN = 3              # چەند گۆرانی داهاتوو لە کارتەکەدا نیشان بدرێت
SEEK_SECONDS = 10             # دوگمەکانی ⏪ / ⏩ چەند چرکە بپەڕێنن
HISTORY_SIZE = 20             # چەند گۆرانی پێشوو بۆ دوگمەی ⏮️ هەڵبگیرێت
DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# لێدانی ڤۆیس لە Termux پێویستی بە libopus هەیە
if not discord.opus.is_loaded():
    for _name in ("libopus.so", "libopus.so.0", "opus"):
        try:
            discord.opus.load_opus(_name)
            break
        except Exception:
            continue

YTDL_OPTIONS = {
    "format": "ba/b",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "extractor_args": {"youtube": {"player_client": ["ios", "web_creator", "android"]}},
    "http_headers": {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    },
}

def ffmpeg_options():
    opts = "-vn"
    if AUDIO_FILTER:
        opts += f" -af {shlex.quote(AUDIO_FILTER)}"
    return opts

# بیتڕەیتی ڤۆیس بەرز دەکاتەوە بۆ ئەوپەڕی ڕێگەپێدراوی ژوورەکە، و دەنگ بۆ مۆدی میوزیک دادەنێت
def tune_encoder(vc):
    enc = getattr(vc, "encoder", None)
    if not enc:
        return
    try:
        enc.set_bitrate(max(64, min(512, (vc.channel.bitrate or 96000) // 1000)))
    except Exception:
        pass
    for name, arg in (("set_signal_type", "music"), ("set_bandwidth", "full"), ("set_fec", True)):
        try:
            getattr(enc, name)(arg)
        except Exception:
            pass

# ناوی دۆخەکانی دووبارەکردنەوە
LOOP_TEXT = {"off": "ناچالاک", "song": "🔂 گۆرانی", "queue": "🔁 ڕیزبەندی"}
LOOP_NEXT = {"off": "song", "song": "queue", "queue": "off"}

# هونەرمەندان و گۆرانییەکانیان (بۆ z menu)
ARTISTS_DATA = {
    "bilind": {
        "name": "بلند ئیبراهیم",
        "description": "گۆرانیێن زۆر خۆش و ئەڤینیداریێن بلند ئیبراهیم",
        "songs": [
            {"label": "ڕێڤینگ", "query": "Bilind Ibrahim Reving", "desc": "گۆرانییا زۆر ناڤدار ڕێڤینگ"},
            {"label": "دیکۆن", "query": "Bilind Ibrahim Dikon", "desc": "گۆرانییا ئارام و خەمگین"},
            {"label": "دلا من", "query": "Bilind Ibrahim Dila Min", "desc": "گۆرانییا ئەڤینیداری دلا من"},
            {"label": "هێلینا ئەڤینێ", "query": "Bilind Ibrahim Helina Evine", "desc": "موزیکا زۆر خەمگین"},
        ],
    },
    "erdewan": {
        "name": "ئەردەوان زاخۆیی",
        "description": "گۆرانیێن ڕەسەن و خەمگینێن ئەردەوان زاخۆیی",
        "songs": [
            {"label": "پەشیمانم", "query": "Erdewan Zaxoyi Peshimanm", "desc": "گۆرانییا کلاسیک پەشیمانم"},
            {"label": "دەلالۆ", "query": "Erdewan Zaxoyi Delalo", "desc": "گۆرانییا ڕەسەنا دەلالۆ"},
            {"label": "کوردستان", "query": "Erdewan Zaxoyi Kurdistan", "desc": "گۆرانییا وڵاتپارێزی"},
            {"label": "ئەی فەلەک", "query": "Erdewan Zaxoyi Ey Felek", "desc": "گۆرانییا خەمگین ئەی فەلەک"},
        ],
    },
    "ayaz": {
        "name": "ئەییاز زاخۆیی",
        "description": "گۆرانیێن ڕەسەن و کلاسیكێن ئەییاز زاخۆیی",
        "songs": [
            {"label": "مەم و زێن", "query": "Ayaz Zaxoyi Mem u Zin", "desc": "گۆرانییا ناڤدار مەم و زێن"},
            {"label": "هیڤی ژ تە دکەم", "query": "Ayaz Zaxoyi Hivi Z Te Dkem", "desc": "گۆرانییا ئەڤینیداری هیڤی"},
            {"label": "چاوڕەشێ", "query": "Ayaz Zaxoyi Cawrese", "desc": "گۆرانییا کلاسیك ئەییاز"},
        ],
    },
    "romi": {
        "name": "رۆمی هەرکی",
        "description": "گۆرانیێن شاد و هەڵپەڕکێ یێن رۆمی هەرکی",
        "songs": [
            {"label": "شادی و هەڵپەڕکێ (مێدلی)", "query": "Romi Harki Halparke Medley", "desc": "دەتەکێ ڕیتما شاد بۆ زۆما"},
            {"label": "دڵێ من ژ تە تێر نەبوو", "query": "Romi Harki Dili Min", "desc": "گۆرانییا تازە و ترێند"},
            {"label": "داوەت و سەمایێ", "query": "Romi Harki Dawet", "desc": "موزیکا داوەت و هەڵپەڕکێ"},
        ],
    },
    "islam": {
        "name": "ئیسلام زاخۆیی",
        "description": "گۆرانیێن خەمگین و شادێن ئیسلام زاخۆیی",
        "songs": [
            {"label": "تو چوی", "query": "Islam Zaxoyi Tu Cuyi", "desc": "گۆرانییا خەمگین تو چوی"},
            {"label": "دیلانا شاد", "query": "Islam Zaxoyi Dilana Shad", "desc": "گۆرانییا داوەتێ ئیسلام"},
            {"label": "بێ تە نەژیم", "query": "Islam Zaxoyi Be Te Nezim", "desc": "گۆرانییا ئەڤینیداری"},
        ],
    },
    "karwan": {
        "name": "کاروان کامل",
        "description": "گۆرانیێن هێمن و ئەڤینیداریێن کاروان کامل",
        "songs": [
            {"label": "تو هاتی", "query": "Karwan Kamil Tu Hati", "desc": "گۆرانییا زۆر ناڤدار تو هاتی"},
            {"label": "چاوێن تە", "query": "Karwan Kamil Cawen Te", "desc": "موزیکا خەمگین و ئارام"},
        ],
    },
}

# ═══════════════════════════════════════
# بەشی ٢: فەرمانە یارمەتیدەرەکان
# ═══════════════════════════════════════

def fmt_time(seconds):
    seconds = max(int(seconds), 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def trim(text, limit):
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"

# شریتی کات: ▬▬▬🔘▬▬▬▬
def progress_bar(elapsed, total, length=BAR_LENGTH):
    if total <= 0:
        return "▬" * length
    ratio = min(max(elapsed / total, 0.0), 1.0)
    pos = min(int(length * ratio), length - 1)
    return "▬" * pos + "🔘" + "▬" * (length - pos - 1)

# شریتی دەنگ: ▰▰▰▰▰▱▱▱
def volume_bar(volume, length=8):
    filled = min(max(round(volume / MAX_VOLUME * length), 0), length)
    return "▰" * filled + "▱" * (length - filled)

# z seek: "90" / "1:30" / "1:02:03" ڕاستەوخۆ، یان "+30" / "-15" بەرامبەر بە ئێستا
def parse_seek(text, current):
    text = text.strip()
    sign = 0
    if text and text[0] in "+-":
        sign = 1 if text[0] == "+" else -1
        text = text[1:]
    parts = text.split(":")
    if not 1 <= len(parts) <= 3 or not all(p.isdigit() for p in parts):
        return None
    secs = 0
    for p in parts:
        secs = secs * 60 + int(p)
    return current + sign * secs if sign else secs

# کارتی هەڵە / ئاگاداری / سەرکەوتن
def error_embed(text, ctx=None):
    return make_embed("❌ هەڵە", text, color=ERROR, ctx=ctx)

def warn_embed(text, ctx=None):
    return make_embed("⚠️ ئاگاداری", text, color=WARN, ctx=ctx)

def ok_embed(title, text, ctx=None):
    return make_embed(title, text, color=PURPLE, ctx=ctx)

@dataclass
class Track:
    title: str
    url: str
    duration: int
    thumbnail: Optional[str]
    uploader: str
    requester: discord.Member
    is_live: bool = False
    filepath: Optional[str] = None
    retries: int = 0

    @property
    def duration_str(self):
        return fmt_time(self.duration) if self.duration else "؟"

def make_track(data, requester):
    return Track(
        title=data.get("title") or "Unknown",
        url=data.get("webpage_url") or data.get("original_url") or data.get("url"),
        duration=int(data.get("duration") or 0),
        thumbnail=data.get("thumbnail"),
        uploader=data.get("uploader") or data.get("channel") or "—",
        requester=requester,
        is_live=bool(data.get("is_live")),
    )

# yt-dlp: دەگەڕێت (download=False) یان دایدەبەزێنێت (download=True)
# لە executor کار دەکات، چونکە دەبێتە هۆی وەستانی بوت
def _extract(query, download, guild_id=0):
    opts = dict(YTDL_OPTIONS)
    opts["outtmpl"] = os.path.join(DOWNLOAD_DIR, f"%(id)s_{guild_id}.%(ext)s")
    if "tiktok.com" in query.lower():
        opts["format"] = "best/bestaudio"
    with yt_dlp.YoutubeDL(opts) as ytdl:
        data = ytdl.extract_info(query, download=download)
        if data and "entries" in data:
            entries = [e for e in data["entries"] if e]
            data = entries[0] if entries else None
        if data is None:
            raise RuntimeError("هیچ ئەنجامێک نەدۆزرایەوە")
        path = ytdl.prepare_filename(data) if download else None
    return data, path

class AudioSource(discord.PCMVolumeTransformer):
    def __init__(self, filepath, volume, start_at=0):
        before = f"-ss {int(start_at)}" if start_at > 0 else None
        super().__init__(discord.FFmpegPCMAudio(filepath, before_options=before, options=ffmpeg_options()), volume)
        self.filepath = filepath

# stream ی ڕاستەوخۆ (بێ دابەزاندن). start_at = لە چەند چرکەوە دەست پێ بکات
def make_stream_source(data, start_at, volume):
    headers = data.get("http_headers") or {}
    hdr = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
    before = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    if start_at > 0:
        before += f" -ss {int(start_at)}"
    if hdr:
        before += f" -headers {shlex.quote(hdr)}"
    source = discord.FFmpegPCMAudio(data["url"], before_options=before, options=ffmpeg_options())
    return discord.PCMVolumeTransformer(source, volume)

# دۆخی میوزیکی هەر سێرڤەرێک
class GuildState:
    def __init__(self):
        self.queue = []
        self.current = None
        self.loop = "off"          # off / song / queue
        self.volume = DEFAULT_VOLUME
        self.channel = None        # ژووری نووسینی دوایین داواکاری
        self.message = None        # کارتی "ئێستا لێدەدرێت"
        self.view = None
        self.started_at = 0.0
        self.paused_at = None
        self.paused_total = 0.0
        self.skipped = False
        self.history = []          # گۆرانییە پێشووەکان (بۆ ⏮️)
        self.override = None       # گۆرانییەک کە دەبێت دواتر ڕاستەوخۆ بلێت (⏮️ / جەمپ)
        self.going_back = False
        self.restart = False
        self.seek_to = None        # ⏪ / ⏩ / z seek: لە چ چرکەیەکەوە دەست پێ بکاتەوە
        self.lock = asyncio.Lock()
        self.progress_task = None
        self.idle_task = None
        self.alone_task = None

    def reset_clock(self):
        self.started_at = time.time()
        self.paused_at = None
        self.paused_total = 0.0

    def elapsed(self):
        now = self.paused_at if self.paused_at else time.time()
        return max(int(now - self.started_at - self.paused_total), 0)

# ═══════════════════════════════════════
# بەشی ٣: دوگمەکانی کۆنتڕۆڵ
# ═══════════════════════════════════════

class JumpSelect(discord.ui.Select):
    def __init__(self, cog, tracks):
        self.cog = cog
        options = [
            discord.SelectOption(
                label=f"{n}. {trim(t.title, 90)}",
                value=str(id(t)),
                description=f"{trim(t.uploader, 40)} • {t.duration_str}",
                emoji="🎵",
            )
            for n, t in enumerate(tracks, start=1)
        ]
        super().__init__(placeholder="🎯 گۆرانییەک لە ڕیزبەندی هەڵبژێرە و ڕاستەوخۆ لێیبدە...", options=options, row=2)

    async def callback(self, interaction):
        st = self.cog.states.get(interaction.guild.id)
        track = next((t for t in st.queue if str(id(t)) == self.values[0]), None) if st else None
        if track is None:
            return await interaction.response.send_message("❌ ئەم گۆرانییە ئیتر لە ڕیزبەندیدا نییە.", ephemeral=True)
        await interaction.response.defer()
        self.cog.do_jump(interaction.guild, track)

class MusicControls(discord.ui.View):
    def __init__(self, cog, guild_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
        self.jump = None

    # تەنها ئەو کەسانەی لە هەمان ڤۆیسدان دەتوانن کۆنتڕۆڵ بکەن
    async def interaction_check(self, interaction):
        vc = interaction.guild.voice_client if interaction.guild else None
        st = self.cog.states.get(self.guild_id)
        if not vc or not st or not st.current:
            await interaction.response.send_message("❌ هیچ گۆرانییەک نالێدرێت.", ephemeral=True)
            return False
        voice = getattr(interaction.user, "voice", None)
        if not voice or voice.channel != vc.channel:
            await interaction.response.send_message("❌ دەبێت لەگەڵ بوت لە هەمان ڤۆیس بیت.", ephemeral=True)
            return False
        return True

    # دۆخی دوگمەکان و لیستی جەمپ لەگەڵ دۆخی ڕاستەقینە یەک دەخات
    def sync(self, paused, loop, queue):
        self.pause_btn.emoji = "▶️" if paused else "⏸️"
        self.pause_btn.style = discord.ButtonStyle.success if paused else discord.ButtonStyle.primary
        self.loop_btn.emoji = "🔂" if loop == "song" else "🔁"
        self.loop_btn.style = discord.ButtonStyle.secondary if loop == "off" else discord.ButtonStyle.success
        if self.jump is not None:
            self.remove_item(self.jump)
            self.jump = None
        if queue:
            self.jump = JumpSelect(self.cog, queue[:25])
            self.add_item(self.jump)

    async def _update(self, interaction):
        guild = interaction.guild
        st = self.cog.states[guild.id]
        self.sync(guild.voice_client.is_paused(), st.loop, st.queue)
        await interaction.response.edit_message(embed=self.cog.now_embed(guild, st), view=self)

    # ڕیزی ١: 🔀 ⏮️ ⏯️ ⏭️ 🔁
    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, row=0)
    async def shuffle_btn(self, interaction, button):
        st = self.cog.states[interaction.guild.id]
        if len(st.queue) < 2:
            return await interaction.response.send_message("❌ پێویستە لانی کەم ٢ گۆرانی لە ڕیزبەندیدا بێت.", ephemeral=True)
        random.shuffle(st.queue)
        await self._update(interaction)

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, row=0)
    async def prev_btn(self, interaction, button):
        await interaction.response.defer()
        self.cog.do_previous(interaction.guild)

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.primary, row=0)
    async def pause_btn(self, interaction, button):
        st = self.cog.states[interaction.guild.id]
        self.cog.toggle_pause(st, interaction.guild.voice_client)
        await self._update(interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def skip_btn(self, interaction, button):
        await interaction.response.defer()
        self.cog.do_skip(interaction.guild)

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, row=0)
    async def loop_btn(self, interaction, button):
        st = self.cog.states[interaction.guild.id]
        st.loop = LOOP_NEXT[st.loop]
        await self._update(interaction)

    # ڕیزی ٢: ⏪ 🔉 ⏹️ 🔊 ⏩
    async def _seek(self, interaction, delta):
        guild = interaction.guild
        st = self.cog.states[guild.id]
        if not st.current.duration:
            return await interaction.response.send_message("❌ ماوەی ئەم گۆرانییە نەزانراوە.", ephemeral=True)
        await interaction.response.defer()
        self.cog.do_seek(guild, st.elapsed() + delta)

    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.secondary, row=1)
    async def back_btn(self, interaction, button):
        await self._seek(interaction, -SEEK_SECONDS)

    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.secondary, row=1)
    async def vol_down_btn(self, interaction, button):
        st = self.cog.states[interaction.guild.id]
        self.cog.set_volume(interaction.guild.voice_client, st, st.volume - VOLUME_STEP)
        await self._update(interaction)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, row=1)
    async def stop_btn(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild
        channel = self.cog.states[guild.id].channel
        await self.cog.destroy(guild)
        if channel:
            await channel.send(embed=warn_embed(f"⏹️ **{interaction.user.display_name}** میوزیکی ڕاگرت و بوت چووە دەرەوە."))

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.secondary, row=1)
    async def vol_up_btn(self, interaction, button):
        st = self.cog.states[interaction.guild.id]
        self.cog.set_volume(interaction.guild.voice_client, st, st.volume + VOLUME_STEP)
        await self._update(interaction)

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.secondary, row=1)
    async def fwd_btn(self, interaction, button):
        await self._seek(interaction, SEEK_SECONDS)

# ═══════════════════════════════════════
# بەشی ٤: ڕیزبەندی (پەڕە بە پەڕە)
# ═══════════════════════════════════════

class QueueView(discord.ui.View):
    def __init__(self, cog, guild_id, page=0):
        super().__init__(timeout=90)
        self.cog = cog
        self.guild_id = guild_id
        self.page = page

    def build(self):
        st = self.cog.states.get(self.guild_id)
        queue = st.queue if st else []
        pages = max(1, math.ceil(len(queue) / QUEUE_PER_PAGE))
        self.page = min(max(self.page, 0), pages - 1)
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page >= pages - 1

        desc = ""
        if st and st.current:
            t = st.current
            desc += f"**🎧 ئێستا لێدەدرێت**\n[{trim(t.title, 60)}]({t.url}) ┃ `{t.duration_str}`\n\n"
        if queue:
            start = self.page * QUEUE_PER_PAGE
            lines = [
                f"`{start + i:02d}` [{trim(t.title, 55)}]({t.url}) ┃ `{t.duration_str}`"
                for i, t in enumerate(queue[start:start + QUEUE_PER_PAGE], start=1)
            ]
            desc += "**📋 داهاتوو**\n" + "\n".join(lines)
        else:
            desc += "*ڕیزبەندی بەتاڵە. بنووسە* `" + PREFIX + " play <ناو>`"

        total = sum(t.duration for t in queue)
        embed = make_embed("📜 ڕیزبەندی میوزیک", desc, color=PURPLE)
        embed.set_footer(text=f"پەڕە {self.page + 1}/{pages} • {len(queue)} گۆرانی • {fmt_time(total)} • {BOT_NAME}")
        return embed

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction, button):
        self.page -= 1
        await interaction.response.edit_message(embed=self.build(), view=self)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction, button):
        self.page += 1
        await interaction.response.edit_message(embed=self.build(), view=self)

# ═══════════════════════════════════════
# بەشی ٥: داشبۆردی هونەرمەندان (z menu)
# ═══════════════════════════════════════

class SongSelect(discord.ui.Select):
    def __init__(self, cog, artist_key):
        self.cog = cog
        artist = ARTISTS_DATA[artist_key]
        options = [
            discord.SelectOption(label=s["label"][:100], value=s["query"], description=s["desc"][:100], emoji="🎵")
            for s in artist["songs"]
        ]
        super().__init__(placeholder=f"🎧 گۆرانییەکی {artist['name']} هەڵبژێرە...", options=options)

    async def callback(self, interaction):
        voice = getattr(interaction.user, "voice", None)
        if not voice or not voice.channel:
            return await interaction.response.send_message("❌ سەرەتا بچۆ ناو ڤۆیسێک.", ephemeral=True)
        query = self.values[0]
        await interaction.response.send_message(f"⚡ داواکرا: `{query}`", ephemeral=True)
        await self.cog.request(interaction.guild, interaction.channel, interaction.user, query)

class SongView(discord.ui.View):
    def __init__(self, cog, artist_key):
        super().__init__(timeout=120)
        self.add_item(SongSelect(cog, artist_key))

class ArtistSelect(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(label=d["name"], value=k, description=d["description"][:100], emoji="🎙️")
            for k, d in ARTISTS_DATA.items()
        ]
        super().__init__(placeholder="✨ هونەرمەندێک هەڵبژێرە...", options=options)

    async def callback(self, interaction):
        key = self.values[0]
        artist = ARTISTS_DATA[key]
        songs = "\n".join(f"🎵 **{s['label']}** ┕ {s['desc']}" for s in artist["songs"])
        embed = make_embed(f"🎙️ {artist['name']}", f"> {artist['description']}\n\n{songs}", color=PURPLE)
        await interaction.response.send_message(embed=embed, view=SongView(self.cog, key), ephemeral=True)

class ArtistView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.message = None
        self.add_item(ArtistSelect(cog))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

# ═══════════════════════════════════════
# بەشی ٦: Cog ی سەرەکی
# ═══════════════════════════════════════

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.states = {}
        # فایلە پاشماوەکانی جاری پێشوو بسڕەوە
        for name in os.listdir(DOWNLOAD_DIR):
            try:
                os.remove(os.path.join(DOWNLOAD_DIR, name))
            except OSError:
                pass

    async def cog_check(self, ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        return True

    async def cog_unload(self):
        for guild in list(self.bot.guilds):
            if guild.id in self.states or guild.voice_client:
                await self.destroy(guild)

    # ─── یارمەتیدەرەکان ───

    def state(self, guild_id):
        if guild_id not in self.states:
            self.states[guild_id] = GuildState()
        return self.states[guild_id]

    @staticmethod
    def _cancel(task):
        if task and task is not asyncio.current_task():
            task.cancel()

    @staticmethod
    def remove_file(track):
        if track and track.filepath:
            try:
                os.remove(track.filepath)
            except OSError:
                pass
            track.filepath = None

    def set_volume(self, vc, st, value):
        st.volume = min(max(value, VOLUME_STEP), MAX_VOLUME)
        if vc and vc.source and hasattr(vc.source, "volume"):
            vc.source.volume = st.volume

    def toggle_pause(self, st, vc):
        if vc.is_paused():
            vc.resume()
            if st.paused_at:
                st.paused_total += time.time() - st.paused_at
            st.paused_at = None
            return False
        if vc.is_playing():
            vc.pause()
            st.paused_at = time.time()
            return True
        return False

    def do_skip(self, guild):
        st = self.states.get(guild.id)
        vc = guild.voice_client
        if st and vc:
            st.skipped = True
            vc.stop()

    # ⏮️ ئەگەر زیاتر لە ٥ چرکە لێدرابێت، هەمان گۆرانی لە سەرەتاوە. ئەگەر نا، گۆرانی پێشوو
    def do_previous(self, guild):
        st = self.states.get(guild.id)
        vc = guild.voice_client
        if not st or not st.current or not vc:
            return
        if st.elapsed() > 5 or not st.history:
            st.restart = True
        else:
            back = st.history.pop()
            st.queue.insert(0, st.current)
            st.override = back
            st.going_back = True
            st.skipped = True
        vc.stop()

    # 🎯 ڕاستەوخۆ بچۆ سەر گۆرانییەک لە ڕیزبەندی
    def do_jump(self, guild, track):
        st = self.states.get(guild.id)
        vc = guild.voice_client
        if not st or not vc or track not in st.queue:
            return
        st.queue.remove(track)
        st.override = track
        st.skipped = True
        vc.stop()

    # ⏪ / ⏩ / z seek: هەمان گۆرانی لە چرکەیەکی تر دەست پێ دەکاتەوە
    def do_seek(self, guild, position):
        st = self.states.get(guild.id)
        vc = guild.voice_client
        if not st or not st.current or not vc or not st.current.duration:
            return False
        if not (vc.is_playing() or vc.is_paused()):
            return False
        st.seek_to = int(min(max(position, 0), max(st.current.duration - 2, 0)))
        vc.stop()
        return True

    # ─── کارتی "ئێستا لێدەدرێت" ───

    def now_embed(self, guild, st):
        t = st.current
        vc = guild.voice_client
        paused = bool(vc and vc.is_paused())
        elapsed = st.elapsed()
        if t.duration:
            elapsed = min(elapsed, t.duration)

        desc = (
            f"### [{trim(t.title, 200)}]({t.url})\n"
            f"**{trim(t.uploader, 60)}**\n\n"
            f"{'⏸️' if paused else '▶️'}  `{fmt_time(elapsed)}`  "
            f"{progress_bar(elapsed, t.duration)}  `{t.duration_str}`\n\n"
            f"🔊 {volume_bar(st.volume)} `{int(st.volume * 100)}%`  ┃  {LOOP_TEXT[st.loop] if st.loop != 'off' else '🔁 ناچالاک'}"
            f"  ┃  📋 `{len(st.queue)}` لە ڕیزبەندیدا"
        )
        if st.queue:
            lines = [
                f"`{n}` {trim(q.title, 48)} ┃ `{q.duration_str}`"
                for n, q in enumerate(st.queue[:UPNEXT_SHOWN], start=1)
            ]
            desc += "\n\n**⏭️ داهاتوو**\n" + "\n".join(lines)
            if len(st.queue) > UPNEXT_SHOWN:
                desc += f"\n*و {len(st.queue) - UPNEXT_SHOWN} گۆرانی تر...*"

        embed = make_embed("", desc, color=GOLD if paused else PURPLE)
        embed.title = None
        embed.set_author(
            name="وەستێنراوە • Paused" if paused else "ئێستا لێدەدرێت • Now Playing",
            icon_url=self.bot.user.display_avatar.url,
        )
        if t.thumbnail:
            if BIG_COVER:
                embed.set_image(url=t.thumbnail)
            else:
                embed.set_thumbnail(url=t.thumbnail)
        embed.set_footer(
            text=f"داواکراوە لەلایەن {t.requester.display_name} • {BOT_NAME} Music",
            icon_url=t.requester.display_avatar.url,
        )
        return embed

    async def refresh_message(self, guild):
        st = self.states.get(guild.id)
        if not st or not st.message or not st.current or not st.view:
            return
        vc = guild.voice_client
        st.view.sync(bool(vc and vc.is_paused()), st.loop, st.queue)
        try:
            await st.message.edit(embed=self.now_embed(guild, st), view=st.view)
        except discord.HTTPException:
            pass

    # کارتی "ئێستا لێدەدرێت" دەکات بە کارتێکی کورت (کاتێک گۆرانییەکە تەواو دەبێت)
    async def finish_message(self, st, track, stopped=False):
        self._cancel(st.progress_task)
        msg = st.message
        st.message = None
        st.view = None
        if not msg or not track:
            return
        if stopped:
            title = "⏹️ لێدان ڕاگیرا"
        elif st.skipped:
            title = "⏭️ پەڕێندرا"
        else:
            title = "✅ لێدان تەواو بوو"
        embed = make_embed(
            title,
            f"[{trim(track.title, 80)}]({track.url}) ┃ `{track.duration_str}`",
            color=0x4F545C,
        )
        embed.set_footer(text=f"{track.requester.display_name} • {BOT_NAME} Music")
        try:
            await msg.edit(embed=embed, view=None)
        except discord.HTTPException:
            pass

    # ─── لێدان ───

    async def request(self, guild, channel, member, query):
        voice = member.voice.channel if member.voice else None
        if voice is None:
            return await channel.send(embed=error_embed(f"**{member.display_name}**، سەرەتا بچۆ ناو ڤۆیسێک."))
        vc = guild.voice_client
        if vc and vc.channel != voice:
            return await channel.send(embed=error_embed(f"بوت لە {vc.channel.mention} دایە. بچۆ ئەوێ یان `{PREFIX} stop` بنووسە."))

        st = self.state(guild.id)
        if len(st.queue) >= MAX_QUEUE:
            return await channel.send(embed=warn_embed(f"ڕیزبەندی پڕە (**{MAX_QUEUE}** گۆرانی)."))

        status = await channel.send(embed=ok_embed("🔎 گەڕان...", f"`{trim(query, 100)}`"))
        try:
            data, _ = await self.bot.loop.run_in_executor(None, _extract, query, False)
        except Exception as e:
            return await status.edit(embed=error_embed(f"گۆرانییەکە نەدۆزرایەوە.\n`{trim(e, 150)}`"))

        track = make_track(data, member)
        if track.is_live:
            return await status.edit(embed=warn_embed("لایڤ (Live) پشتگیری ناکرێت."))
        if MAX_SONG_MINUTES and track.duration > MAX_SONG_MINUTES * 60:
            return await status.edit(embed=warn_embed(f"گۆرانییەکە زۆر درێژە. زۆرترین ماوە **{MAX_SONG_MINUTES} خولەک**ـە."))

        if guild.voice_client is None:
            try:
                await voice.connect(reconnect=True, self_deaf=True)
            except Exception as e:
                return await status.edit(embed=error_embed(f"نەتوانرا بچمە ناو ڤۆیس.\n`{trim(e, 150)}`"))

        self._cancel(st.idle_task)
        st.channel = channel

        async with st.lock:
            idle = st.current is None
            if idle:
                st.current = track
            else:
                wait = max((st.current.duration - st.elapsed()) if st.current.duration else 0, 0)
                wait += sum(t.duration for t in st.queue)
                st.queue.append(track)
                position = len(st.queue)

        if idle:
            try:
                await status.delete()
            except discord.HTTPException:
                pass
            await self.start_track(guild, track)
            return

        embed = ok_embed("➕ زیاد کرا بۆ ڕیزبەندی", f"[{trim(track.title, 100)}]({track.url})")
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        embed.add_field(name="⏱️ ماوە", value=f"`{track.duration_str}`")
        embed.add_field(name="📍 شوێن", value=f"`#{position}`")
        embed.add_field(name="⏳ چاوەڕوانی", value=f"`~{fmt_time(wait)}`")
        embed.set_footer(
            text=f"داواکراوە لەلایەن {member.display_name} • {BOT_NAME} Music",
            icon_url=member.display_avatar.url,
        )
        await status.edit(embed=embed)
        await self.refresh_message(guild)

    async def download(self, track, guild_id):
        if track.filepath and os.path.exists(track.filepath):
            return track.filepath
        _, path = await self.bot.loop.run_in_executor(None, _extract, track.url, True, guild_id)
        track.filepath = path
        return path

    def is_stream(self, track):
        return STREAM_OVER_MINUTES > 0 and track.duration > STREAM_OVER_MINUTES * 60

    # st.current پێشتر دانراوە. ئەم فەرمانە دایدەبەزێنێت (یان stream دەکات) و دەستی پێ دەکات
    async def start_track(self, guild, track, reuse=False, start_at=0):
        st = self.state(guild.id)
        path, data = None, None
        try:
            if self.is_stream(track):
                # هەر جارێک لینکی نوێ وەردەگرین، چونکە لینکی YouTube دوای چەند کاتژمێرێک بەسەر دەچێت
                data, _ = await self.bot.loop.run_in_executor(None, _extract, track.url, False)
            else:
                path = await self.download(track, guild.id)
        except Exception as e:
            st.current = None
            if st.channel:
                await st.channel.send(embed=error_embed(f"نەتوانرا **{trim(track.title, 60)}** بارکرێت.\n`{trim(e, 150)}`"))
            return await self.play_next(guild)

        vc = guild.voice_client
        if vc is None or not vc.is_connected() or st.current is not track:
            self.remove_file(track)
            return

        def after(error):
            if error:
                print(f"هەڵەی لێدان: {error}")
            asyncio.run_coroutine_threadsafe(self._after(guild, track, error), self.bot.loop)

        try:
            source = make_stream_source(data, start_at, st.volume) if data else AudioSource(path, st.volume, start_at)
            vc.play(source, after=after)
            tune_encoder(vc)
        except Exception as e:
            st.current = None
            self.remove_file(track)
            if st.channel:
                await st.channel.send(embed=error_embed(f"هەڵە لە لێدان.\n`{trim(e, 150)}`"))
            return

        st.reset_clock()
        st.started_at -= start_at
        view = MusicControls(self, guild.id)
        view.sync(False, st.loop, st.queue)
        embed = self.now_embed(guild, st)
        if (reuse or start_at) and st.message:
            try:
                view = st.view or view
                view.sync(False, st.loop, st.queue)
                await st.message.edit(embed=embed, view=view)
            except discord.HTTPException:
                st.message = await st.channel.send(embed=embed, view=view)
        else:
            st.message = await st.channel.send(embed=embed, view=view)
        st.view = view
        self._cancel(st.progress_task)
        if track.duration:
            st.progress_task = self.bot.loop.create_task(self.progress_loop(guild, track))

    async def _after(self, guild, track, error=None):
        st = self.states.get(guild.id)
        if st is None or st.current is not track:
            self.remove_file(track)
            return
        # seek: هەمان گۆرانی لە شوێنی نوێوە دەست پێ دەکاتەوە (فایلەکە ناسڕدرێتەوە)
        if st.seek_to is not None:
            pos, st.seek_to = st.seek_to, None
            return await self.start_track(guild, track, reuse=True, start_at=pos)
        # ئەگەر لە ناوەڕاستدا پچڕا (هەڵە یان stream ی پچڕاو)، لەو شوێنەوە بەردەوام دەبێت
        if (error or self.is_stream(track)) and track.duration and not st.skipped and not st.restart and st.override is None:
            elapsed = st.elapsed()
            if track.duration - elapsed > 20:
                if track.retries < MAX_STREAM_RETRIES:
                    track.retries += 1
                    return await self.start_track(guild, track, reuse=True, start_at=elapsed)
                if st.channel:
                    await st.channel.send(embed=warn_embed(f"لێدانی **{trim(track.title, 60)}** پچڕا و نەگەڕایەوە."))
        keep = bool((st.loop == "song" and not st.skipped) or st.restart)
        if not keep:
            self.remove_file(track)
        await self.play_next(guild)

    async def play_next(self, guild):
        st = self.states.get(guild.id)
        if st is None:
            return
        vc = guild.voice_client
        if vc is None or not vc.is_connected():
            return await self.cleanup(guild.id)

        prev = st.current
        going_back = st.going_back
        nxt = None
        if st.override is not None:
            nxt = st.override
            if prev and st.loop == "queue" and not going_back:
                st.queue.append(prev)
        elif prev and st.restart:
            nxt = prev
        elif prev and st.loop == "song" and not st.skipped:
            nxt = prev
        elif prev and st.loop == "queue":
            st.queue.append(prev)
        if nxt is None and st.queue:
            nxt = st.queue.pop(0)

        st.override = None
        st.going_back = False
        reuse = nxt is not None and nxt is prev
        if prev and not reuse:
            if not going_back:
                st.history.append(prev)
                del st.history[:-HISTORY_SIZE]
            await self.finish_message(st, prev)
        st.restart = False
        st.skipped = False
        st.current = nxt

        if nxt is None:
            self._cancel(st.idle_task)
            st.idle_task = self.bot.loop.create_task(self._idle(guild))
            return
        nxt.retries = 0
        await self.start_track(guild, nxt, reuse=reuse)

    # شریتی کات نوێ دەکاتەوە
    async def progress_loop(self, guild, track):
        try:
            while True:
                await asyncio.sleep(PROGRESS_REFRESH)
                st = self.states.get(guild.id)
                vc = guild.voice_client
                if not st or st.current is not track or not st.message or not vc:
                    break
                if track.duration and st.elapsed() > track.duration + 3:
                    break
                if vc.is_playing() or vc.is_paused():
                    await st.message.edit(embed=self.now_embed(guild, st))
        except (discord.HTTPException, asyncio.CancelledError):
            pass

    # ─── دەرچوون و پاککردنەوە ───

    async def _idle(self, guild):
        if STAY_IN_VOICE:
            return
        try:
            await asyncio.sleep(IDLE_DISCONNECT)
        except asyncio.CancelledError:
            return
        st = self.states.get(guild.id)
        vc = guild.voice_client
        if st and st.current is None and not st.queue and vc and not vc.is_playing():
            channel = st.channel
            await self.destroy(guild)
            if channel:
                await channel.send(embed=make_embed(
                    "👋 چوومە دەرەوە", f"بەهۆی بێ‌چالاکی {IDLE_DISCONNECT // 60} خولەک.", color=WARN))

    async def _alone(self, guild):
        if STAY_IN_VOICE:
            return
        try:
            await asyncio.sleep(ALONE_DISCONNECT)
        except asyncio.CancelledError:
            return
        vc = guild.voice_client
        if vc and vc.channel and not any(not m.bot for m in vc.channel.members):
            st = self.states.get(guild.id)
            channel = st.channel if st else None
            await self.destroy(guild)
            if channel:
                await channel.send(embed=make_embed(
                    "👋 چوومە دەرەوە", "هیچ کەسێک لە ڤۆیس نەما.", color=WARN))
        elif guild.id in self.states:
            self.states[guild.id].alone_task = None

    async def cleanup(self, guild_id):
        st = self.states.pop(guild_id, None)
        if not st:
            return
        for task in (st.progress_task, st.idle_task, st.alone_task):
            self._cancel(task)
        self.remove_file(st.current)

    # بوت لە ڤۆیس دەردەچێت و هەموو شتێک پاک دەکاتەوە
    async def destroy(self, guild):
        st = self.states.get(guild.id)
        if st:
            track = st.current
            st.queue.clear()
            st.loop = "off"
            await self.finish_message(st, track, stopped=True)
            st.current = None
            self.remove_file(track)
        vc = guild.voice_client
        if vc:
            try:
                await vc.disconnect()
            except Exception:
                pass
        await self.cleanup(guild.id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild = member.guild
        if member.id == self.bot.user.id:
            if before.channel and after.channel is None:
                await self.cleanup(guild.id)
            return
        vc = guild.voice_client
        st = self.states.get(guild.id)
        if not vc or not vc.channel or not st:
            return
        if any(not m.bot for m in vc.channel.members):
            self._cancel(st.alone_task)
            st.alone_task = None
        elif before.channel == vc.channel and st.alone_task is None:
            st.alone_task = self.bot.loop.create_task(self._alone(guild))

    # ─── پشکنینی فەرمانەکان ───

    async def check(self, ctx, need_playing=True):
        vc = ctx.guild.voice_client
        st = self.states.get(ctx.guild.id)
        if not vc or not vc.is_connected():
            await ctx.send(embed=error_embed("بوت لە ڤۆیس نییە."), delete_after=8)
            return None
        voice = ctx.author.voice
        if not voice or voice.channel != vc.channel:
            await ctx.send(embed=error_embed("دەبێت لەگەڵ بوت لە هەمان ڤۆیس بیت."), delete_after=8)
            return None
        if need_playing and (not st or not st.current):
            await ctx.send(embed=error_embed("هیچ گۆرانییەک نالێدرێت."), delete_after=8)
            return None
        return st, vc

    # ═══════════════════════════════════════
    # بەشی ٧: فەرمانەکان
    # ═══════════════════════════════════════

    # z play <ناو / لینک>
    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, search: str = None):
        if not search:
            return await ctx.send(embed=ok_embed(
                "🎶 چۆن لێبدەم؟",
                f"`{PREFIX} play <ناوی گۆرانی یان لینکی YouTube/TikTok>`\n"
                f"چەند گۆرانی بە یەکجار: هەر یەک لە دێڕێکدا.", ctx=ctx))
        queries = [q.strip() for q in search.split("\n") if q.strip()][:10]
        for q in queries:
            await self.request(ctx.guild, ctx.channel, ctx.author, q)

    # z join
    @commands.command(name="join", aliases=["j"])
    async def join(self, ctx):
        voice = ctx.author.voice
        if not voice or not voice.channel:
            return await ctx.send(embed=error_embed("سەرەتا بچۆ ناو ڤۆیسێک."), delete_after=8)
        vc = ctx.guild.voice_client
        if vc and vc.channel == voice.channel:
            return await ctx.send(embed=warn_embed("بوت پێشتر لێرەیە."), delete_after=8)
        if vc:
            await vc.move_to(voice.channel)
        else:
            await voice.channel.connect(reconnect=True, self_deaf=True)
        self.state(ctx.guild.id).channel = ctx.channel
        await ctx.send(embed=ok_embed("🔊 هاتمە ناو ڤۆیس", f"{voice.channel.mention}\nبنووسە `{PREFIX} play <ناو>`", ctx=ctx))

    # z pause / z resume
    @commands.command(name="pause")
    async def pause(self, ctx):
        res = await self.check(ctx)
        if not res:
            return
        st, vc = res
        if vc.is_paused():
            return await ctx.send(embed=warn_embed("پێشتر وەستێنراوە."), delete_after=8)
        self.toggle_pause(st, vc)
        await self.refresh_message(ctx.guild)
        await ctx.message.add_reaction("⏸️")

    @commands.command(name="resume", aliases=["unpause"])
    async def resume(self, ctx):
        res = await self.check(ctx)
        if not res:
            return
        st, vc = res
        if not vc.is_paused():
            return await ctx.send(embed=warn_embed("گۆرانییەکە وەستێنراو نییە."), delete_after=8)
        self.toggle_pause(st, vc)
        await self.refresh_message(ctx.guild)
        await ctx.message.add_reaction("▶️")

    # z skip
    @commands.command(name="skip", aliases=["sk", "next"])
    async def skip(self, ctx):
        res = await self.check(ctx)
        if not res:
            return
        self.do_skip(ctx.guild)
        await ctx.message.add_reaction("⏭️")

    # z stop
    @commands.command(name="stop", aliases=["leave", "disconnect", "dc"])
    async def stop(self, ctx):
        res = await self.check(ctx, need_playing=False)
        if not res:
            return
        await self.destroy(ctx.guild)
        await ctx.send(embed=warn_embed("⏹️ میوزیک ڕاگیرا و بوت چووە دەرەوە."))

    # z loop [off/song/queue]
    @commands.command(name="loop", aliases=["repeat"])
    async def loop_cmd(self, ctx, mode: str = None):
        res = await self.check(ctx)
        if not res:
            return
        st, _ = res
        names = {"off": "off", "no": "off", "song": "song", "one": "song", "track": "song", "queue": "queue", "all": "queue"}
        new_mode = names.get(mode.lower()) if mode else LOOP_NEXT[st.loop]
        if new_mode is None:
            return await ctx.send(embed=error_embed(f"`{PREFIX} loop` ‧ `{PREFIX} loop song` ‧ `{PREFIX} loop queue` ‧ `{PREFIX} loop off`"), delete_after=10)
        st.loop = new_mode
        await self.refresh_message(ctx.guild)
        await ctx.send(embed=ok_embed("🔁 دووبارەکردنەوە", f"دۆخ: **{LOOP_TEXT[st.loop]}**", ctx=ctx))

    # z volume [1-150]
    @commands.command(name="volume", aliases=["vol", "v"])
    async def volume(self, ctx, amount: int = None):
        res = await self.check(ctx, need_playing=False)
        if not res:
            return
        st, vc = res
        if amount is None:
            return await ctx.send(embed=ok_embed("🔊 دەنگ", f"ئێستا: **{int(st.volume * 100)}%**", ctx=ctx))
        if not 1 <= amount <= int(MAX_VOLUME * 100):
            return await ctx.send(embed=error_embed(f"ژمارەیەک لە نێوان `1` و `{int(MAX_VOLUME * 100)}` بنووسە."), delete_after=8)
        self.set_volume(vc, st, amount / 100)
        await self.refresh_message(ctx.guild)
        await ctx.send(embed=ok_embed("🔊 دەنگ گۆڕدرا", f"**{int(st.volume * 100)}%**", ctx=ctx))

    # z shuffle
    @commands.command(name="shuffle", aliases=["mix"])
    async def shuffle(self, ctx):
        res = await self.check(ctx)
        if not res:
            return
        st, _ = res
        if len(st.queue) < 2:
            return await ctx.send(embed=warn_embed("پێویستە لانی کەم ٢ گۆرانی لە ڕیزبەندیدا بێت."), delete_after=8)
        random.shuffle(st.queue)
        await self.refresh_message(ctx.guild)
        await ctx.send(embed=ok_embed("🔀 ڕیزبەندی تێکەڵ کرا", f"**{len(st.queue)}** گۆرانی", ctx=ctx))

    # z queue [پەڕە]
    @commands.command(name="queue", aliases=["q", "list"])
    async def queue_cmd(self, ctx, page: int = 1):
        st = self.states.get(ctx.guild.id)
        if not st or (not st.current and not st.queue):
            return await ctx.send(embed=warn_embed(f"هیچ شتێک نییە. `{PREFIX} play <ناو>` بنووسە."), delete_after=8)
        view = QueueView(self, ctx.guild.id, page - 1)
        await ctx.send(embed=view.build(), view=view)

    # z nowplaying
    @commands.command(name="nowplaying", aliases=["np", "current"])
    async def nowplaying(self, ctx):
        st = self.states.get(ctx.guild.id)
        if not st or not st.current:
            return await ctx.send(embed=warn_embed("هیچ گۆرانییەک نالێدرێت."), delete_after=8)
        await ctx.send(embed=self.now_embed(ctx.guild, st))

    # z removesong <ژمارە>
    @commands.command(name="removesong", aliases=["rs"])
    async def removesong(self, ctx, number: int):
        res = await self.check(ctx, need_playing=False)
        if not res:
            return
        st, _ = res
        if not 1 <= number <= len(st.queue):
            return await ctx.send(embed=error_embed(f"ژمارەیەک لە نێوان `1` و `{len(st.queue)}` بنووسە."), delete_after=8)
        track = st.queue.pop(number - 1)
        await ctx.send(embed=ok_embed("🗑️ لابرا لە ڕیزبەندی", f"[{trim(track.title, 80)}]({track.url})", ctx=ctx))

    # z clearqueue
    @commands.command(name="clearqueue", aliases=["cq"])
    async def clearqueue(self, ctx):
        res = await self.check(ctx, need_playing=False)
        if not res:
            return
        st, _ = res
        count = len(st.queue)
        st.queue.clear()
        await self.refresh_message(ctx.guild)
        await ctx.send(embed=ok_embed("🧹 ڕیزبەندی پاک کرایەوە", f"**{count}** گۆرانی لابرا.", ctx=ctx))

    # z previous
    @commands.command(name="previous", aliases=["prev", "back"])
    async def previous(self, ctx):
        res = await self.check(ctx)
        if not res:
            return
        self.do_previous(ctx.guild)
        await ctx.message.add_reaction("⏮️")

    # z jump <ژمارە>
    @commands.command(name="jump", aliases=["skipto"])
    async def jump(self, ctx, number: int):
        res = await self.check(ctx)
        if not res:
            return
        st, _ = res
        if not 1 <= number <= len(st.queue):
            return await ctx.send(embed=error_embed(f"ژمارەیەک لە نێوان `1` و `{len(st.queue)}` بنووسە."), delete_after=8)
        self.do_jump(ctx.guild, st.queue[number - 1])
        await ctx.message.add_reaction("🎯")

    # z seek <1:30 / 90 / +30 / -15>
    @commands.command(name="seek", aliases=["goto"])
    async def seek(self, ctx, *, position: str = None):
        res = await self.check(ctx)
        if not res:
            return
        st, _ = res
        target = parse_seek(position, st.elapsed()) if position else None
        if target is None or not st.current.duration:
            return await ctx.send(embed=ok_embed(
                "⏩ Seek",
                f"`{PREFIX} seek 1:30` ‧ `{PREFIX} seek 90` ‧ `{PREFIX} seek +30` ‧ `{PREFIX} seek -15`", ctx=ctx), delete_after=12)
        if self.do_seek(ctx.guild, target):
            await ctx.message.add_reaction("⏩")

    # z menu
    @commands.command(name="menu", aliases=["songs", "artists", "playlist"])
    async def menu(self, ctx):
        if not ctx.author.voice:
            return await ctx.send(embed=error_embed("سەرەتا بچۆ ناو ڤۆیسێک."), delete_after=8)
        artists = "\n".join(f"🎙️ **{d['name']}** ─ `{len(d['songs'])}` گۆرانی" for d in ARTISTS_DATA.values())
        embed = make_embed(
            "🎶 Zero Music ─ داشبۆرد",
            (
                f"👋 سڵاو **{discord.utils.escape_markdown(ctx.author.display_name)}**!\n"
                f"هونەرمەندێک لە خوارەوە هەڵبژێرە و گۆرانییەکەی لێبدە.\n\n"
                f"{'─' * 18}\n{artists}\n{'─' * 18}\n\n"
                f"💡 یان ڕاستەوخۆ: `{PREFIX} play <ناو یان لینکی YouTube/TikTok>`"
            ),
            color=PURPLE,
            ctx=ctx,
        )
        embed.set_author(name=f"{BOT_NAME} • Music", icon_url=self.bot.user.display_avatar.url)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        if MENU_IMAGE:
            embed.set_image(url=MENU_IMAGE)
        view = ArtistView(self)
        view.message = await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Music(bot))
