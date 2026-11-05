import asyncio
import math
import os
import random
import shlex
import sqlite3
import time
from dataclasses import dataclass
from typing import Optional

import discord
from discord.ext import commands
import yt_dlp

from database import db
from utils import make_embed, PREFIX, BOT_NAME, PURPLE, GOLD, SUCCESS, ERROR, WARN

# ═══════════════════════════════════════
# Zero Music ─ بەشێ میوزیکێ
# - کارت ب make_embed یا utils.py دهێنە چێکرن (هەمان دیزاینا بوتی)
# - هێما ژ utils.py دهێتە وەرگرتن: z play / zero play / z! play
# - ل bot.py دا زێدە بکە:  await bot.load_extension("cogs.music")
# پێدڤی: pip install yt-dlp PyNaCl   +   pkg install ffmpeg libopus (Termux)
# ═══════════════════════════════════════

# ═══════════════════════════════════════
# بەشێ ١: ڕێکخستن (ل ڤێرە دەستکاری بکە)
# ═══════════════════════════════════════

DEFAULT_VOLUME = 0.8          # دەنگێ دەستپێکێ (٪٨٠)
MAX_VOLUME = 1.5              # بلندترین دەنگ (٪١٥٠)
VOLUME_STEP = 0.1             # هەر کلیکەکا 🔉 / 🔊 چەند دگۆڕیت (٪١٠)
MAX_QUEUE = 50                # زۆرترین گۆرانی د ڕیزێ دا
MAX_SONG_MINUTES = 720        # درێژترین گۆرانی (ب خولەک). ٧٢٠ = ١٢ دەمژمێر. 0 = بێ سنوور
STREAM_OVER_MINUTES = 30      # گۆرانیێن ژ ڤێ درێژتر دانابەزن و ڕاستەخۆ stream دبن (باشترە بۆ ڤیدیۆیا ١٠ دەمژمێران). 0 = هەمیان دابەزینە
MAX_STREAM_RETRIES = 8        # ئەگەر stream پچڕی، چەند جاران دوبارە ژ وی جهی بەردەوام بیت
IDLE_DISCONNECT = 120         # ئەگەر چ نەهاتە لێدان، پشتی چەند چرکەیان بچیتە دەر
ALONE_DISCONNECT = 60         # ئەگەر بوت تەنێ مایەوە ل ڤۆیسێ، پشتی چەند چرکەیان بچیتە دەر
PROGRESS_REFRESH = 8          # نویکرنا شریتا دەمی (چرکە). ژ ٥ کێمتر نەکە، Discord سنوور هەیە
BAR_LENGTH = 14               # درێژیا شریتا دەمی
QUEUE_PER_PAGE = 8            # چەند گۆرانی ل هەر لاپەڕەکا ڕیزێ
MENU_IMAGE = None             # وێنەیێ داشبۆردێ (لینک). ئەگەر نەڤێت: None
STAY_IN_VOICE = False         # True = بوت چ جاران ب خۆ ژ ڤۆیسێ دەرناکەڤیت (٢٤/٧). تەنێ ب z stop دچیتە دەر
AUDIO_FILTER = "dynaudnorm=f=150:g=15"  # دەنگێ هاوسەنگ و ساف (دەنگێ گۆرانیان وەک ئێک دکەت). نەڤێت: ""
BIG_COVER = True              # True = وێنەیێ گۆرانیێ مەزن (وەک Spotify). False = وێنەیێ بچووک ل لاکێ
UPNEXT_SHOWN = 3              # چەند گۆرانیێن ل دویڤ د کارتێ دا بهێنە نیشاندان
SEEK_SECONDS = 10             # دوگمەیێن ⏪ / ⏩ چەند چرکەیان بپەڕینن
HISTORY_SIZE = 20             # چەند گۆرانیێن بەری نوکە بۆ دوگمەیا ⏮️ بهێنە هەلگرتن
MAX_PLAYLISTS = 10            # هەر کەسەک چەند لیستێن خوە چێبکەت
MAX_PLAYLIST_TRACKS = 100     # زۆرترین گۆرانی د یەک لیستێ دا
MAX_PLAYLIST_NAME = 30        # زۆرترین پیتێن ناڤێ لیستێ
RECENT_LIMIT = 25             # چەند دویماهیک گۆرانی بهێنە هەلگرتن (Recently Played)
LIB_PER_PAGE = 8              # چەند گۆرانی ل هەر لاپەڕەکا کتێبخانێ
DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# لێدانا ڤۆیسێ ل Termux پێدڤی ب libopus یە
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

# بیتڕەیتا ڤۆیسێ بلند دکەت هەتا ئەوپەڕێ ڕێپێدایی یێ ژوورێ، و دەنگی بۆ مۆدا میوزیکێ دانیت
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

# ناڤێن دۆخێن دوبارەکرنەڤە
LOOP_TEXT = {"off": "ناچالاک", "song": "🔂 گۆرانی", "queue": "🔁 ڕیز"}
LOOP_NEXT = {"off": "song", "song": "queue", "queue": "off"}

# هونەرمەند و گۆرانیێن وان (بۆ z menu)
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
# بەشێ ٢: فەرمانێن هاریکار
# ═══════════════════════════════════════

def fmt_time(seconds):
    seconds = max(int(seconds), 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def trim(text, limit):
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1] + "…"

# شریتا دەمی: ▬▬▬🔘▬▬▬▬
def progress_bar(elapsed, total, length=BAR_LENGTH):
    if total <= 0:
        return "▬" * length
    ratio = min(max(elapsed / total, 0.0), 1.0)
    pos = min(int(length * ratio), length - 1)
    return "▬" * pos + "🔘" + "▬" * (length - pos - 1)

# شریتا دەنگی: ▰▰▰▰▰▱▱▱
def volume_bar(volume, length=8):
    filled = min(max(round(volume / MAX_VOLUME * length), 0), length)
    return "▰" * filled + "▱" * (length - filled)

# z seek: "90" / "1:30" / "1:02:03" ڕاستەخۆ، یان "+30" / "-15" بەرامبەری نوکە
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

# کارتا خەلەتیێ / ئاگەهداریێ / سەرکەفتنێ
def error_embed(text, ctx=None):
    return make_embed("❌ خەلەتی", text, color=ERROR, ctx=ctx)

def warn_embed(text, ctx=None):
    return make_embed("⚠️ ئاگەهداری", text, color=WARN, ctx=ctx)

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

# yt-dlp: دگەڕیت (download=False) یان دابەزینیت (download=True)
# ل executor کار دکەت، چونکی دبیتە ئەگەرێ ڕاوەستانا بوتی
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
            raise RuntimeError("چ ئەنجام نەهاتنە دیتن")
        path = ytdl.prepare_filename(data) if download else None
    return data, path

class AudioSource(discord.PCMVolumeTransformer):
    def __init__(self, filepath, volume, start_at=0):
        before = f"-ss {int(start_at)}" if start_at > 0 else None
        super().__init__(discord.FFmpegPCMAudio(filepath, before_options=before, options=ffmpeg_options()), volume)
        self.filepath = filepath

# streamا ڕاستەخۆ (بێ دابەزاندن). start_at = ژ چەند چرکەیان دەست پێ بکەت
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

# دۆخێ میوزیکێ یێ هەر سێرڤەرەکی
class GuildState:
    def __init__(self):
        self.queue = []
        self.current = None
        self.loop = "off"          # off / song / queue
        self.volume = DEFAULT_VOLUME
        self.channel = None        # ژوورا نڤیسینێ یا دویماهیک داخوازیێ
        self.message = None        # کارتا "نوکە دهێتە لێدان"
        self.view = None
        self.started_at = 0.0
        self.paused_at = None
        self.paused_total = 0.0
        self.skipped = False
        self.history = []          # گۆرانیێن بەری نوکە (بۆ ⏮️)
        self.override = None       # گۆرانیەک کو دڤێت پاشی ڕاستەخۆ بهێتە لێدان (⏮️ / جەمپ)
        self.going_back = False
        self.restart = False
        self.seek_to = None        # ⏪ / ⏩ / z seek: ژ چ چرکەیەکێ دەست پێ بکەتەڤە
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
# بەشێ ٣: دوگمەیێن کۆنتڕۆلێ
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
        super().__init__(placeholder="🎯 گۆرانیەکێ ژ ڕیزێ هەلبژێرە و ڕاستەخۆ لێدە...", options=options, row=2)

    async def callback(self, interaction):
        st = self.cog.states.get(interaction.guild.id)
        track = next((t for t in st.queue if str(id(t)) == self.values[0]), None) if st else None
        if track is None:
            return await interaction.response.send_message("❌ ئەڤ گۆرانی ئی د ڕیزێ دا نینە.", ephemeral=True)
        await interaction.response.defer()
        self.cog.do_jump(interaction.guild, track)

class MusicControls(discord.ui.View):
    def __init__(self, cog, guild_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
        self.jump = None

    # تەنێ ئەو کەسێن ل هەمان ڤۆیسێ دا دشێن کۆنتڕۆل بکەن
    async def interaction_check(self, interaction):
        vc = interaction.guild.voice_client if interaction.guild else None
        st = self.cog.states.get(self.guild_id)
        if not vc or not st or not st.current:
            await interaction.response.send_message("❌ چ گۆرانی ناهێنە لێدان.", ephemeral=True)
            return False
        voice = getattr(interaction.user, "voice", None)
        if not voice or voice.channel != vc.channel:
            await interaction.response.send_message("❌ دڤێت دگەل بوتی ل هەمان ڤۆیسێ بی.", ephemeral=True)
            return False
        return True

    # دۆخێ دوگمەیان و لیستا جەمپێ دگەل دۆخێ ڕاستەقینە وەک ئێک دکەت
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

    # ڕیزا ١: 🔀 ⏮️ ⏯️ ⏭️ 🔁
    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, row=0)
    async def shuffle_btn(self, interaction, button):
        st = self.cog.states[interaction.guild.id]
        if len(st.queue) < 2:
            return await interaction.response.send_message("❌ پێدڤییە لانیکەم ٢ گۆرانی د ڕیزێ دا هەبن.", ephemeral=True)
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

    # ڕیزا ٢: ⏪ 🔉 ⏹️ 🔊 ⏩
    async def _seek(self, interaction, delta):
        guild = interaction.guild
        st = self.cog.states[guild.id]
        if not st.current.duration:
            return await interaction.response.send_message("❌ دەمێ ڤێ گۆرانیێ نەهاتیە زانین.", ephemeral=True)
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

    @discord.ui.button(emoji="https://cdn.discordapp.com/attachments/1567978061914181733/1567978181300985986/dU5an1eJ0V.gif?ex=6aee24fa&is=6aecd37a&hm=1335f504e2406bd21ab86e8606efcd5b3573fc191745b559b7b7714f35d05cbf&", style=discord.ButtonStyle.danger, row=1)
    async def stop_btn(self, interaction, button):
        await interaction.response.defer()
        guild = interaction.guild
        channel = self.cog.states[guild.id].channel
        await self.cog.destroy(guild)
        if channel:
            await channel.send(embed=warn_embed(f"⏹️ **{interaction.user.display_name}** میوزیک ڕاگرت و بوت چوو دەر."))

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.secondary, row=1)
    async def vol_up_btn(self, interaction, button):
        st = self.cog.states[interaction.guild.id]
        self.cog.set_volume(interaction.guild.voice_client, st, st.volume + VOLUME_STEP)
        await self._update(interaction)

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.secondary, row=1)
    async def fwd_btn(self, interaction, button):
        await self._seek(interaction, SEEK_SECONDS)

    # ڕیزا ٤: ❤️ Like ┃ 💾 پاشەکەفتکرن بۆ لیستێ
    @discord.ui.button(emoji="❤️", label="Like", style=discord.ButtonStyle.secondary, row=3)
    async def like_btn(self, interaction, button):
        track = self.cog.states[interaction.guild.id].current
        res = lib_toggle_fav(interaction.user.id, track)
        text = {
            "added": "❤️ هاتە زێدەکرن بۆ **Favorites**ێن تە.",
            "removed": "💔 ژ **Favorites**ێن تە هاتە لابرن.",
            "full": f"❌ Favorites تژییە (**{MAX_PLAYLIST_TRACKS}** گۆرانی).",
        }[res]
        await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(emoji="💾", label="پاشەکەفتکرن", style=discord.ButtonStyle.secondary, row=3)
    async def save_btn(self, interaction, button):
        track = self.cog.states[interaction.guild.id].current
        pls = lib_custom(interaction.user.id)
        if not pls:
            return await interaction.response.send_message(
                f"❌ چ لیستێن تە نینن. `{PREFIX} playlist` بنڤیسە و دوگمەیا ➕ بگوشە.", ephemeral=True)
        view = discord.ui.View(timeout=60)
        view.add_item(SaveSelect(track, pls))
        await interaction.response.send_message("💾 بۆ کیژ لیستێ پاشەکەفت بکەم؟", view=view, ephemeral=True)

# ═══════════════════════════════════════
# بەشێ ٤: ڕیز (لاپەڕە ب لاپەڕە)
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
            desc += f"**🎧 نوکە دهێتە لێدان**\n[{trim(t.title, 60)}]({t.url}) ┃ `{t.duration_str}`\n\n"
        if queue:
            start = self.page * QUEUE_PER_PAGE
            lines = [
                f"`{start + i:02d}` [{trim(t.title, 55)}]({t.url}) ┃ `{t.duration_str}`"
                for i, t in enumerate(queue[start:start + QUEUE_PER_PAGE], start=1)
            ]
            desc += "**📋 یێ ل دویف**\n" + "\n".join(lines)
        else:
            desc += "*ڕیز ڤالایە. بنڤیسە* `" + PREFIX + " play <ناڤ>`"

        total = sum(t.duration for t in queue)
        embed = make_embed("📜 ڕیزا میوزیکێ", desc, color=PURPLE)
        embed.set_footer(text=f"لاپەڕە {self.page + 1}/{pages} • {len(queue)} گۆرانی • {fmt_time(total)} • {BOT_NAME}")
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
# بەشێ ٥: داشبۆردا هونەرمەندان (z menu)
# ═══════════════════════════════════════

class SongSelect(discord.ui.Select):
    def __init__(self, cog, artist_key):
        self.cog = cog
        artist = ARTISTS_DATA[artist_key]
        options = [
            discord.SelectOption(label=s["label"][:100], value=s["query"], description=s["desc"][:100], emoji="🎵")
            for s in artist["songs"]
        ]
        super().__init__(placeholder=f"🎧 گۆرانیەکا {artist['name']} هەلبژێرە...", options=options)

    async def callback(self, interaction):
        voice = getattr(interaction.user, "voice", None)
        if not voice or not voice.channel:
            return await interaction.response.send_message("❌ سەرەتا بچە ناڤ ڤۆیسەکێ.", ephemeral=True)
        query = self.values[0]
        await interaction.response.send_message(f"⚡ هاتە داخوازکرن: `{query}`", ephemeral=True)
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
        super().__init__(placeholder="✨ هونەرمەندەکێ هەلبژێرە...", options=options)

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
# بەشێ ٥ب: کتێبخانەیا میوزیکێ ─ Favorites / Recently Played / Playlists
# هەمی تشت ل هەمان economy.db دا دهێنە هەلگرتن (ژ بەر هندێ backupا بوتی دێ وان بگریت)
# ═══════════════════════════════════════

db.execute(
    "CREATE TABLE IF NOT EXISTS music_playlists ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "user_id INTEGER NOT NULL, name TEXT NOT NULL, "
    "is_fav INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL)"
)
db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_music_pl_name ON music_playlists(user_id, name COLLATE NOCASE)")
db.execute(
    "CREATE TABLE IF NOT EXISTS music_playlist_tracks ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, playlist_id INTEGER NOT NULL, "
    "title TEXT, url TEXT NOT NULL, duration INTEGER NOT NULL DEFAULT 0, "
    "uploader TEXT, thumbnail TEXT, added REAL NOT NULL)"
)
db.execute("CREATE INDEX IF NOT EXISTS idx_music_plt_pl ON music_playlist_tracks(playlist_id)")
db.execute(
    "CREATE TABLE IF NOT EXISTS music_recent ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, "
    "title TEXT, url TEXT NOT NULL, duration INTEGER NOT NULL DEFAULT 0, "
    "uploader TEXT, thumbnail TEXT, played REAL NOT NULL)"
)
db.execute("CREATE INDEX IF NOT EXISTS idx_music_recent_user ON music_recent(user_id, played)")
db.commit()

FAV_TITLE = "❤️ Favorites"
RESERVED_NAMES = {"favorites", "favorite", "favs", "fav", "like", "likes", "liked", "love",
                  "recent", "recently", "recently played", "history", "❤️ favorites"}
FAV_WORDS = {"fav", "favs", "favorite", "favorites", "like", "likes", "liked", "love"}
RECENT_WORDS = {"recent", "recently", "history"}

@dataclass
class LibRef:
    kind: str       # fav / recent / playlist
    id: int
    name: str
    user_id: int

    @property
    def title(self):
        if self.kind == "fav":
            return FAV_TITLE
        if self.kind == "recent":
            return "🕘 Recently Played"
        return f"🎼 {self.name}"

def lib_fav_id(user_id):
    row = db.execute("SELECT id FROM music_playlists WHERE user_id = ? AND is_fav = 1", (user_id,)).fetchone()
    if row:
        return row[0]
    cur = db.execute(
        "INSERT INTO music_playlists (user_id, name, is_fav, created) VALUES (?, ?, 1, ?)",
        (user_id, FAV_TITLE, time.time()),
    )
    db.commit()
    return cur.lastrowid

# لیستێن کەسەکی (بێ Favorites): (id, name, ژمارا گۆرانیان)
def lib_custom(user_id):
    return db.execute(
        "SELECT p.id, p.name, (SELECT COUNT(*) FROM music_playlist_tracks t WHERE t.playlist_id = p.id) "
        "FROM music_playlists p WHERE p.user_id = ? AND p.is_fav = 0 ORDER BY p.id",
        (user_id,),
    ).fetchall()

def lib_count(playlist_id):
    return db.execute("SELECT COUNT(*) FROM music_playlist_tracks WHERE playlist_id = ?", (playlist_id,)).fetchone()[0]

def lib_recent_count(user_id):
    return db.execute("SELECT COUNT(*) FROM music_recent WHERE user_id = ?", (user_id,)).fetchone()[0]

# ناڤ یان ژمارێ دکەتە LibRef: fav / recent / ژمارا لیستێ (وەک ل داشبۆردێ) / ناڤێ لیستێ
def lib_resolve(user_id, text):
    t = " ".join(text.split()).lower()
    if t in FAV_WORDS:
        return LibRef("fav", lib_fav_id(user_id), FAV_TITLE, user_id)
    if t in RECENT_WORDS:
        return LibRef("recent", 0, "Recently Played", user_id)
    pls = lib_custom(user_id)
    if t.isdigit() and 1 <= int(t) <= len(pls):
        pid, name, _ = pls[int(t) - 1]
        return LibRef("playlist", pid, name, user_id)
    for pid, name, _ in pls:
        if name.lower() == t:
            return LibRef("playlist", pid, name, user_id)
    return None

# گۆرانیێن لیستەکێ: (title, url, duration, uploader, thumbnail)
def lib_tracks(ref):
    if ref.kind == "recent":
        return db.execute(
            "SELECT title, url, duration, uploader, thumbnail FROM music_recent "
            "WHERE user_id = ? ORDER BY played DESC, id DESC", (ref.user_id,)).fetchall()
    return db.execute(
        "SELECT title, url, duration, uploader, thumbnail FROM music_playlist_tracks "
        "WHERE playlist_id = ? ORDER BY id", (ref.id,)).fetchall()

# دزڤڕینیتەڤە: ok / exists / full
def lib_add(playlist_id, track):
    if db.execute("SELECT 1 FROM music_playlist_tracks WHERE playlist_id = ? AND url = ?",
                  (playlist_id, track.url)).fetchone():
        return "exists"
    if lib_count(playlist_id) >= MAX_PLAYLIST_TRACKS:
        return "full"
    db.execute(
        "INSERT INTO music_playlist_tracks (playlist_id, title, url, duration, uploader, thumbnail, added) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (playlist_id, track.title, track.url, track.duration, track.uploader, track.thumbnail, time.time()),
    )
    db.commit()
    return "ok"

# دزڤڕینیتەڤە: added / removed / full
def lib_toggle_fav(user_id, track):
    pid = lib_fav_id(user_id)
    row = db.execute("SELECT id FROM music_playlist_tracks WHERE playlist_id = ? AND url = ?",
                     (pid, track.url)).fetchone()
    if row:
        db.execute("DELETE FROM music_playlist_tracks WHERE id = ?", (row[0],))
        db.commit()
        return "removed"
    return "added" if lib_add(pid, track) == "ok" else "full"

# ژمارێ (١ ژ سەرەڤە) ناڤێ گۆرانیا لابری دزڤڕینیتەڤە، یان None
def lib_remove_track(playlist_id, number):
    ids = [r[0] for r in db.execute(
        "SELECT id FROM music_playlist_tracks WHERE playlist_id = ? ORDER BY id", (playlist_id,)).fetchall()]
    if not 1 <= number <= len(ids):
        return None
    title = db.execute("SELECT title FROM music_playlist_tracks WHERE id = ?", (ids[number - 1],)).fetchone()[0]
    db.execute("DELETE FROM music_playlist_tracks WHERE id = ?", (ids[number - 1],))
    db.commit()
    return title or "Unknown"

# دزڤڕینیتەڤە: ok / invalid / reserved / limit / exists
def lib_create(user_id, name):
    name = " ".join(str(name).split())[:MAX_PLAYLIST_NAME]
    if not name:
        return "invalid"
    if name.lower() in RESERVED_NAMES:
        return "reserved"
    if len(lib_custom(user_id)) >= MAX_PLAYLISTS:
        return "limit"
    try:
        db.execute("INSERT INTO music_playlists (user_id, name, is_fav, created) VALUES (?, ?, 0, ?)",
                   (user_id, name, time.time()))
        db.commit()
    except sqlite3.IntegrityError:
        return "exists"
    return "ok"

def lib_delete(playlist_id):
    db.execute("DELETE FROM music_playlist_tracks WHERE playlist_id = ?", (playlist_id,))
    db.execute("DELETE FROM music_playlists WHERE id = ? AND is_fav = 0", (playlist_id,))
    db.commit()

# هەر گۆرانیەک دەست ب لێدانێ بکەت، بۆ داخوازکەرێ وێ دهێتە تۆمارکرن (خەلەتیا داتابەیسێ چ جاران میوزیکێ ڕاناوەستینیت)
def record_recent(user_id, track):
    try:
        db.execute("DELETE FROM music_recent WHERE user_id = ? AND url = ?", (user_id, track.url))
        db.execute(
            "INSERT INTO music_recent (user_id, title, url, duration, uploader, thumbnail, played) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, track.title, track.url, track.duration, track.uploader, track.thumbnail, time.time()),
        )
        db.execute(
            "DELETE FROM music_recent WHERE user_id = ? AND id NOT IN "
            "(SELECT id FROM music_recent WHERE user_id = ? ORDER BY played DESC, id DESC LIMIT ?)",
            (user_id, user_id, RECENT_LIMIT),
        )
        db.commit()
    except Exception as e:
        print(f"خەلەتیا Recently Played: {e}")

def row_to_track(row, requester):
    title, url, duration, uploader, thumbnail = row
    return Track(title=title or "Unknown", url=url, duration=int(duration or 0),
                 thumbnail=thumbnail, uploader=uploader or "—", requester=requester)

CREATE_ERRORS = {
    "invalid": "ناڤێ لیستێ ڤالایە.",
    "reserved": "ئەڤ ناڤە تایبەتە (Favorites / Recent). ناڤەکێ دی هەلبژێرە.",
    "limit": f"تو دشێی زۆرترین **{MAX_PLAYLISTS}** لیستان هەبیت.",
    "exists": "ئەڤ ناڤە بەری نوکە هەیە.",
}
ADD_TEXT = {
    "ok": "✅ هاتە زێدەکرن بۆ لیستێ.",
    "exists": "⚠️ ئەڤ گۆرانی بەری نوکە د وی لیستێ دایە.",
    "full": f"❌ ئەو لیست تژییە (**{MAX_PLAYLIST_TRACKS}** گۆرانی).",
}

# ─── پاشەکەفتکرنا گۆرانیا نوکە ژ پلەیەرێ (💾) ───

class SaveSelect(discord.ui.Select):
    def __init__(self, track, pls):
        self.track = track
        options = [
            discord.SelectOption(label=name[:100], value=str(pid), description=f"{cnt} گۆرانی", emoji="🎼")
            for pid, name, cnt in pls
        ]
        super().__init__(placeholder="🎼 لیستەکێ هەلبژێرە...", options=options)

    async def callback(self, interaction):
        pid = int(self.values[0])
        owned = db.execute("SELECT 1 FROM music_playlists WHERE id = ? AND user_id = ? AND is_fav = 0",
                           (pid, interaction.user.id)).fetchone()
        if not owned:
            return await interaction.response.edit_message(content="❌ ئەڤ لیست ئی نینە.", view=None)
        await interaction.response.edit_message(content=ADD_TEXT[lib_add(pid, self.track)], view=None)

# ─── لیستا گۆرانیان (Favorites / Recent / Playlist) ───

class LibTrackSelect(discord.ui.Select):
    def __init__(self, lv, chunk, start):
        self.lv = lv
        options = [
            discord.SelectOption(
                label=f"{start + i}. {trim(r[0] or 'Unknown', 90)}",
                value=str(start + i - 1),
                description=trim(f"{r[3] or '—'} • {fmt_time(r[2]) if r[2] else '؟'}", 100),
                emoji="🎵",
            )
            for i, r in enumerate(chunk, start=1)
        ]
        super().__init__(placeholder="🎧 گۆرانیەکێ هەلبژێرە و لێدە...", options=options, row=1)

    async def callback(self, interaction):
        cog = self.lv.cog
        if not await cog.ensure_voice(interaction):
            return
        rows = lib_tracks(self.lv.ref)
        idx = int(self.values[0])
        if idx >= len(rows):
            return await interaction.response.send_message("❌ ئەڤ گۆرانی ئی د ڤێ لیستێ دا نینە.", ephemeral=True)
        await interaction.response.defer()
        await cog.enqueue_saved(interaction.guild, interaction.channel, interaction.user,
                                [rows[idx]], label=trim(rows[idx][0] or "", 60))

class ListView(discord.ui.View):
    def __init__(self, cog, owner, ref, page=0, dashboard=False):
        super().__init__(timeout=180)
        self.cog = cog
        self.owner = owner
        self.ref = ref
        self.page = page
        self.message = None
        self.select = None
        if not dashboard:
            self.remove_item(self.home_btn)

    # تەنێ خودانێ لیستێ دشێت بکاربینیت
    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(
                f"❌ ئەڤ لیستە یا **{self.owner.display_name}**ە. بۆ خوە بنڤیسە `{PREFIX} playlist`.", ephemeral=True)
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

    def build(self):
        rows = lib_tracks(self.ref)
        pages = max(1, math.ceil(len(rows) / LIB_PER_PAGE))
        self.page = min(max(self.page, 0), pages - 1)
        start = self.page * LIB_PER_PAGE
        chunk = rows[start:start + LIB_PER_PAGE]
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page >= pages - 1
        self.play_btn.disabled = self.shuffle_btn.disabled = not rows
        if self.select is not None:
            self.remove_item(self.select)
            self.select = None
        if chunk:
            self.select = LibTrackSelect(self, chunk, start)
            self.add_item(self.select)

        if rows:
            desc = "\n".join(
                f"`{start + i:02d}` [{trim(r[0] or 'Unknown', 55)}]({r[1]}) ┃ `{fmt_time(r[2]) if r[2] else '؟'}`"
                for i, r in enumerate(chunk, start=1)
            )
        elif self.ref.kind == "fav":
            desc = f"*هێشتا چ Favoriteەکێ تە نینە.*\nدەمێ گۆرانیەک دهێتە لێدان ❤️ بگوشە، یان `{PREFIX} like` بنڤیسە."
        elif self.ref.kind == "recent":
            desc = "*هێشتا چ گۆرانیەک ژ تە نەهاتیە لێدان.*"
        else:
            desc = f"*ئەڤ لیستە ڤالایە.*\nگۆرانیەکێ لێدە و 💾 بگوشە، یان `{PREFIX} pl add {self.ref.name}` بنڤیسە."

        total = sum((r[2] or 0) for r in rows)
        embed = make_embed(self.ref.title, desc, color=PURPLE)
        embed.set_author(name=self.owner.display_name, icon_url=self.owner.display_avatar.url)
        embed.set_footer(text=f"لاپەڕە {self.page + 1}/{pages} • {len(rows)} گۆرانی • {fmt_time(total)} • {BOT_NAME}")
        return embed

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary, row=0)
    async def prev_btn(self, interaction, button):
        self.page -= 1
        await interaction.response.edit_message(embed=self.build(), view=self)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary, row=0)
    async def next_btn(self, interaction, button):
        self.page += 1
        await interaction.response.edit_message(embed=self.build(), view=self)

    @discord.ui.button(emoji="🎶", label="هەمیان لێدە", style=discord.ButtonStyle.success, row=0)
    async def play_btn(self, interaction, button):
        if not await self.cog.ensure_voice(interaction):
            return
        await interaction.response.defer()
        await self.cog.enqueue_saved(interaction.guild, interaction.channel, interaction.user,
                                     lib_tracks(self.ref), label=self.ref.title)

    @discord.ui.button(emoji="🔀", label="تێکەل", style=discord.ButtonStyle.primary, row=0)
    async def shuffle_btn(self, interaction, button):
        if not await self.cog.ensure_voice(interaction):
            return
        await interaction.response.defer()
        await self.cog.enqueue_saved(interaction.guild, interaction.channel, interaction.user,
                                     lib_tracks(self.ref), shuffle=True, label=self.ref.title)

    @discord.ui.button(emoji="🏠", style=discord.ButtonStyle.secondary, row=0)
    async def home_btn(self, interaction, button):
        dash = DashboardView(self.cog, self.owner)
        dash.message = interaction.message
        await interaction.response.edit_message(embed=dash.build(), view=dash)

# ─── داشبۆردا کتێبخانێ (z playlist) ───

class CreateModal(discord.ui.Modal, title="🎼 لیستەکا نوی"):
    name = discord.ui.TextInput(label="ناڤێ لیستێ", placeholder="بۆ نموونە: Chill", max_length=MAX_PLAYLIST_NAME)

    def __init__(self, cog, owner):
        super().__init__()
        self.cog = cog
        self.owner = owner

    async def on_submit(self, interaction):
        res = lib_create(self.owner.id, str(self.name))
        if res != "ok":
            return await interaction.response.send_message(f"❌ {CREATE_ERRORS[res]}", ephemeral=True)
        dash = DashboardView(self.cog, self.owner)
        dash.message = interaction.message
        await interaction.response.edit_message(embed=dash.build(), view=dash)

class LibrarySelect(discord.ui.Select):
    def __init__(self, owner):
        self.owner = owner
        options = [
            discord.SelectOption(label="Favorites", value="fav", emoji="❤️",
                                 description=f"{lib_count(lib_fav_id(owner.id))} گۆرانی"),
            discord.SelectOption(label="Recently Played", value="recent", emoji="🕘",
                                 description=f"{lib_recent_count(owner.id)} گۆرانی"),
        ]
        for pid, name, cnt in lib_custom(owner.id):
            options.append(discord.SelectOption(label=name[:100], value=f"pl:{pid}", emoji="🎼",
                                                description=f"{cnt} گۆرانی"))
        super().__init__(placeholder="📂 لیستەکێ هەلبژێرە...", options=options, row=0)

    async def callback(self, interaction):
        value = self.values[0]
        uid = self.owner.id
        if value == "fav":
            ref = LibRef("fav", lib_fav_id(uid), FAV_TITLE, uid)
        elif value == "recent":
            ref = LibRef("recent", 0, "Recently Played", uid)
        else:
            pid = int(value.split(":")[1])
            row = next((p for p in lib_custom(uid) if p[0] == pid), None)
            if row is None:
                return await interaction.response.send_message("❌ ئەڤ لیستە ئی نینە.", ephemeral=True)
            ref = LibRef("playlist", pid, row[1], uid)
        view = ListView(self.view.cog, self.owner, ref, dashboard=True)
        view.message = interaction.message
        await interaction.response.edit_message(embed=view.build(), view=view)

class DashboardView(discord.ui.View):
    def __init__(self, cog, owner):
        super().__init__(timeout=180)
        self.cog = cog
        self.owner = owner
        self.message = None
        self.add_item(LibrarySelect(owner))

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message(
                f"❌ ئەڤ کتێبخانە یا **{self.owner.display_name}**ە. بۆ خوە بنڤیسە `{PREFIX} playlist`.", ephemeral=True)
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

    def build(self):
        uid = self.owner.id
        pls = lib_custom(uid)
        desc = (
            f"❤️ **Favorites** ─ `{lib_count(lib_fav_id(uid))}` گۆرانی\n"
            f"🕘 **Recently Played** ─ `{lib_recent_count(uid)}` گۆرانی\n\n"
            f"{'─' * 18}\n"
        )
        if pls:
            desc += "\n".join(
                f"`{n}` 🎼 **{discord.utils.escape_markdown(name)}** ─ `{cnt}` گۆرانی"
                for n, (pid, name, cnt) in enumerate(pls, start=1)
            )
        else:
            desc += "*هێشتا چ لیستێن تە نینن. دوگمەیا ➕ بگوشە.*"
        desc += f"\n\n💡 `{PREFIX} like` ┃ `{PREFIX} pl play <ناو>` ┃ `{PREFIX} recent`"
        embed = make_embed("🎧 کتێبخانەیا میوزیکێ یا تە", desc, color=PURPLE)
        embed.set_author(name=self.owner.display_name, icon_url=self.owner.display_avatar.url)
        embed.set_thumbnail(url=self.owner.display_avatar.url)
        embed.set_footer(text=f"{len(pls)}/{MAX_PLAYLISTS} لیست • {BOT_NAME} Music")
        return embed

    @discord.ui.button(emoji="➕", label="لیستەکا نوی", style=discord.ButtonStyle.primary, row=1)
    async def create_btn(self, interaction, button):
        await interaction.response.send_modal(CreateModal(self.cog, self.owner))

# ═══════════════════════════════════════
# بەشێ ٦: Cogا سەرەکی
# ═══════════════════════════════════════

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.states = {}
        # ئەو فایلێن ژ جارا بەری مایین ژێببە
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

    # ─── هاریکار ───

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

    # ⏮️ ئەگەر پتر ژ ٥ چرکەیان هاتبیتە لێدان، هەمان گۆرانی ژ دەستپێکێ. ئەگەر نە، گۆرانیا بەری نوکە
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

    # 🎯 ڕاستەخۆ بچە سەر گۆرانیەکێ ل ڕیزێ
    def do_jump(self, guild, track):
        st = self.states.get(guild.id)
        vc = guild.voice_client
        if not st or not vc or track not in st.queue:
            return
        st.queue.remove(track)
        st.override = track
        st.skipped = True
        vc.stop()

    # ⏪ / ⏩ / z seek: هەمان گۆرانی ژ چرکەیەکا دی دەست پێ دکەتەڤە
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

    # ─── گۆرانیا پاشەکەفتکری (لیست / Favorites / Recent) ───

    async def ensure_voice(self, interaction):
        voice = getattr(interaction.user, "voice", None)
        if not voice or not voice.channel:
            await interaction.response.send_message("❌ سەرەتا بچە ناڤ ڤۆیسەکێ.", ephemeral=True)
            return False
        return True

    # rows = (title, url, duration, uploader, thumbnail). گۆرانیان دکەتە ڕیزێ و ئەگەر چ نەهاتبیتە لێدان، دەست پێ دکەت
    async def enqueue_saved(self, guild, channel, member, rows, shuffle=False, label=None):
        rows = list(rows)
        if not rows:
            return await channel.send(embed=warn_embed("ئەڤ لیستە ڤالایە."))
        voice = member.voice.channel if member.voice else None
        if voice is None:
            return await channel.send(embed=error_embed(f"**{member.display_name}**، سەرەتا بچە ناڤ ڤۆیسەکێ."))
        vc = guild.voice_client
        if vc and vc.channel != voice:
            return await channel.send(embed=error_embed(f"بوت ل {vc.channel.mention} دایە. بچە وێرێ یان `{PREFIX} stop` بنڤیسە."))

        st = self.state(guild.id)
        room = MAX_QUEUE - len(st.queue) + (1 if st.current is None else 0)
        if room <= 0:
            return await channel.send(embed=warn_embed(f"ڕیز تژییە (**{MAX_QUEUE}** گۆرانی)."))
        if shuffle:
            random.shuffle(rows)
        cut = len(rows) > room
        tracks = [row_to_track(r, member) for r in rows[:room]]

        if guild.voice_client is None:
            try:
                await voice.connect(reconnect=True, self_deaf=True)
            except Exception as e:
                return await channel.send(embed=error_embed(f"نەشیام بچمە ناڤ ڤۆیسێ.\n`{trim(e, 150)}`"))

        self._cancel(st.idle_task)
        st.channel = channel
        async with st.lock:
            idle = st.current is None
            if idle:
                st.current = tracks[0]
                st.queue.extend(tracks[1:])
            else:
                st.queue.extend(tracks)

        text = f"**{discord.utils.escape_markdown(label or 'لیست')}** ─ `{len(tracks)}` گۆرانی"
        if cut:
            text += f"\n⚠️ تەنێ {len(tracks)} گۆرانی جهێ وان هەبوو (سنوورێ ڕیزێ)."
        embed = ok_embed("🔀 هاتە تێکەلکرن و زێدەکرن" if shuffle else "➕ هاتە زێدەکرن بۆ ڕیزێ", text)
        embed.set_footer(text=f"ژ لایێ {member.display_name} ڤە هاتیە داخوازکرن • {BOT_NAME} Music",
                         icon_url=member.display_avatar.url)
        await channel.send(embed=embed)
        if idle:
            await self.start_track(guild, tracks[0])

    # ─── کارتا "نوکە دهێتە لێدان" ───

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
            f"  ┃  📋 `{len(st.queue)}` د ڕیزێ دا"
        )
        if st.queue:
            lines = [
                f"`{n}` {trim(q.title, 48)} ┃ `{q.duration_str}`"
                for n, q in enumerate(st.queue[:UPNEXT_SHOWN], start=1)
            ]
            desc += "\n\n**⏭️ یێ ل دویف**\n" + "\n".join(lines)
            if len(st.queue) > UPNEXT_SHOWN:
                desc += f"\n*و {len(st.queue) - UPNEXT_SHOWN} گۆرانیێن دی...*"

        embed = make_embed("", desc, color=GOLD if paused else PURPLE)
        embed.title = None
        embed.set_author(
            name="ڕاوەستیایە • Paused" if paused else "نوکە دهێتە لێدان • Now Playing",
            icon_url=self.bot.user.display_avatar.url,
        )
        if t.thumbnail:
            if BIG_COVER:
                embed.set_image(url=t.thumbnail)
            else:
                embed.set_thumbnail(url=t.thumbnail)
        embed.set_footer(
            text=f"ژ لایێ {t.requester.display_name} ڤە هاتیە داخوازکرن • {BOT_NAME} Music",
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

    # کارتا "نوکە دهێتە لێدان" دکەتە کارتەکا کورت (دەمێ گۆرانی تەمام دبیت)
    async def finish_message(self, st, track, stopped=False):
        self._cancel(st.progress_task)
        msg = st.message
        st.message = None
        st.view = None
        if not msg or not track:
            return
        if stopped:
            title = "⏹️ لێدان ڕاوەستیا"
        elif st.skipped:
            title = "⏭️ هاتە پەڕاندن"
        else:
            title = "✅ لێدان تەمام بوو"
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
            return await channel.send(embed=error_embed(f"**{member.display_name}**، سەرەتا بچە ناڤ ڤۆیسەکێ."))
        vc = guild.voice_client
        if vc and vc.channel != voice:
            return await channel.send(embed=error_embed(f"بوت ل {vc.channel.mention} دایە. بچە وێرێ یان `{PREFIX} stop` بنڤیسە."))

        st = self.state(guild.id)
        if len(st.queue) >= MAX_QUEUE:
            return await channel.send(embed=warn_embed(f"ڕیز تژییە (**{MAX_QUEUE}** گۆرانی)."))

        status = await channel.send(embed=ok_embed("🔎 گەڕیان...", f"`{trim(query, 100)}`"))
        try:
            data, _ = await self.bot.loop.run_in_executor(None, _extract, query, False)
        except Exception as e:
            return await status.edit(embed=error_embed(f"گۆرانی نەهاتە دیتن.\n`{trim(e, 150)}`"))

        track = make_track(data, member)
        if track.is_live:
            return await status.edit(embed=warn_embed("لایڤ (Live) پشتگیری ناهێتە کرن."))
        if MAX_SONG_MINUTES and track.duration > MAX_SONG_MINUTES * 60:
            return await status.edit(embed=warn_embed(f"گۆرانی گەلەک درێژە. زۆرترین دەم **{MAX_SONG_MINUTES} خولەکە**."))

        if guild.voice_client is None:
            try:
                await voice.connect(reconnect=True, self_deaf=True)
            except Exception as e:
                return await status.edit(embed=error_embed(f"نەشیام بچمە ناڤ ڤۆیسێ.\n`{trim(e, 150)}`"))

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

        embed = ok_embed("➕ هاتە زێدەکرن بۆ ڕیزێ", f"[{trim(track.title, 100)}]({track.url})")
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        embed.add_field(name="⏱️ دەم", value=f"`{track.duration_str}`")
        embed.add_field(name="📍 جه", value=f"`#{position}`")
        embed.add_field(name="⏳ چاڤەڕێکرن", value=f"`~{fmt_time(wait)}`")
        embed.set_footer(
            text=f"ژ لایێ {member.display_name} ڤە هاتیە داخوازکرن • {BOT_NAME} Music",
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

    # st.current بەری نوکە هاتیە دانان. ئەڤ فەرمانە دابەزینیت (یان stream دکەت) و دەستپێ دکەت
    async def start_track(self, guild, track, reuse=False, start_at=0):
        st = self.state(guild.id)
        path, data = None, None
        try:
            if self.is_stream(track):
                # هەر جارەکێ لینکەکێ نوی وەردگرین، چونکی لینکێ YouTube پشتی چەند دەمژمێران بسەر دچیت
                data, _ = await self.bot.loop.run_in_executor(None, _extract, track.url, False)
            else:
                path = await self.download(track, guild.id)
        except Exception as e:
            st.current = None
            if st.channel:
                await st.channel.send(embed=error_embed(f"نەهاتە شیان **{trim(track.title, 60)}** بهێتە بارکرن.\n`{trim(e, 150)}`"))
            return await self.play_next(guild)

        vc = guild.voice_client
        if vc is None or not vc.is_connected() or st.current is not track:
            self.remove_file(track)
            return

        def after(error):
            if error:
                print(f"خەلەتیا لێدانێ: {error}")
            asyncio.run_coroutine_threadsafe(self._after(guild, track, error), self.bot.loop)

        try:
            source = make_stream_source(data, start_at, st.volume) if data else AudioSource(path, st.volume, start_at)
            vc.play(source, after=after)
            tune_encoder(vc)
            if not start_at:
                record_recent(track.requester.id, track)
        except Exception as e:
            st.current = None
            self.remove_file(track)
            if st.channel:
                await st.channel.send(embed=error_embed(f"خەلەتی د لێدانێ دا.\n`{trim(e, 150)}`"))
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
        # seek: هەمان گۆرانی ژ جهەکێ نوی دەست پێ دکەتەڤە (فایل ناهێتە ژێبرن)
        if st.seek_to is not None:
            pos, st.seek_to = st.seek_to, None
            return await self.start_track(guild, track, reuse=True, start_at=pos)
        # ئەگەر د ناڤەڕاستێ دا پچڕی (خەلەتی یان streamا پچڕایی)، ژ وی جهی بەردەوام دبیت
        if (error or self.is_stream(track)) and track.duration and not st.skipped and not st.restart and st.override is None:
            elapsed = st.elapsed()
            if track.duration - elapsed > 20:
                if track.retries < MAX_STREAM_RETRIES:
                    track.retries += 1
                    return await self.start_track(guild, track, reuse=True, start_at=elapsed)
                if st.channel:
                    await st.channel.send(embed=warn_embed(f"لێدانا **{trim(track.title, 60)}** پچڕی و نەزڤڕییەڤە."))
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

    # شریتا دەمی نوی دکەتەڤە
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

    # ─── دەرکەفتن و پاقژکرن ───

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
                    "👋 چوومە دەر", f"ژ بەر بێ چالاکیێ {IDLE_DISCONNECT // 60} خولەکان.", color=WARN))

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
                    "👋 چوومە دەر", "چ کەس ل ڤۆیسێ نەما.", color=WARN))
        elif guild.id in self.states:
            self.states[guild.id].alone_task = None

    async def cleanup(self, guild_id):
        st = self.states.pop(guild_id, None)
        if not st:
            return
        for task in (st.progress_task, st.idle_task, st.alone_task):
            self._cancel(task)
        self.remove_file(st.current)

    # بوت ژ ڤۆیسێ دەردکەڤیت و هەمی تشتان پاقژ دکەت
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

    # ─── پشکنینا فەرمانان ───

    async def check(self, ctx, need_playing=True):
        vc = ctx.guild.voice_client
        st = self.states.get(ctx.guild.id)
        if not vc or not vc.is_connected():
            await ctx.send(embed=error_embed("بوت ل ڤۆیسێ نینە."), delete_after=8)
            return None
        voice = ctx.author.voice
        if not voice or voice.channel != vc.channel:
            await ctx.send(embed=error_embed("دڤێت دگەل بوتی ل هەمان ڤۆیسێ بی."), delete_after=8)
            return None
        if need_playing and (not st or not st.current):
            await ctx.send(embed=error_embed("چ گۆرانی ناهێنە لێدان."), delete_after=8)
            return None
        return st, vc

    # ═══════════════════════════════════════
    # بەشێ ٧: فەرمان
    # ═══════════════════════════════════════

    # z play <ناڤ / لینک>
    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, search: str = None):
        if not search:
            return await ctx.send(embed=ok_embed(
                "🎶 چەوا لێدەم؟",
                f"`{PREFIX} play <ناڤێ گۆرانیێ یان لینکێ YouTube/TikTok>`\n"
                f"چەند گۆرانی ب جارەکێ: هەر یەک د دێڕەکێ دا.", ctx=ctx))
        queries = [q.strip() for q in search.split("\n") if q.strip()][:10]
        for q in queries:
            await self.request(ctx.guild, ctx.channel, ctx.author, q)

    # z join
    @commands.command(name="join", aliases=["j"])
    async def join(self, ctx):
        voice = ctx.author.voice
        if not voice or not voice.channel:
            return await ctx.send(embed=error_embed("سەرەتا بچە ناڤ ڤۆیسەکێ."), delete_after=8)
        vc = ctx.guild.voice_client
        if vc and vc.channel == voice.channel:
            return await ctx.send(embed=warn_embed("بوت بەری نوکە ل ڤێرەیە."), delete_after=8)
        if vc:
            await vc.move_to(voice.channel)
        else:
            await voice.channel.connect(reconnect=True, self_deaf=True)
        self.state(ctx.guild.id).channel = ctx.channel
        await ctx.send(embed=ok_embed("🔊 ئەز هاتمە ناڤ ڤۆیسێ", f"{voice.channel.mention}\nبنڤیسە `{PREFIX} play <ناڤ>`", ctx=ctx))

    # z pause / z resume
    @commands.command(name="pause")
    async def pause(self, ctx):
        res = await self.check(ctx)
        if not res:
            return
        st, vc = res
        if vc.is_paused():
            return await ctx.send(embed=warn_embed("بەری نوکە ڕاوەستیایە."), delete_after=8)
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
            return await ctx.send(embed=warn_embed("گۆرانی ڕانەوەستیایە."), delete_after=8)
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
        await ctx.send(embed=warn_embed("⏹️ میوزیک ڕاوەستیا و بوت چوو دەر."))

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
        await ctx.send(embed=ok_embed("🔁 دوبارەکرنەڤە", f"دۆخ: **{LOOP_TEXT[st.loop]}**", ctx=ctx))

    # z volume [1-150]
    @commands.command(name="volume", aliases=["vol", "v"])
    async def volume(self, ctx, amount: int = None):
        res = await self.check(ctx, need_playing=False)
        if not res:
            return
        st, vc = res
        if amount is None:
            return await ctx.send(embed=ok_embed("🔊 دەنگ", f"نوکە: **{int(st.volume * 100)}%**", ctx=ctx))
        if not 1 <= amount <= int(MAX_VOLUME * 100):
            return await ctx.send(embed=error_embed(f"ژمارەکێ د ناڤبەرا `1` و `{int(MAX_VOLUME * 100)}` دا بنڤیسە."), delete_after=8)
        self.set_volume(vc, st, amount / 100)
        await self.refresh_message(ctx.guild)
        await ctx.send(embed=ok_embed("🔊 دەنگ هاتە گوهۆڕین", f"**{int(st.volume * 100)}%**", ctx=ctx))

    # z shuffle
    @commands.command(name="shuffle", aliases=["mix"])
    async def shuffle(self, ctx):
        res = await self.check(ctx)
        if not res:
            return
        st, _ = res
        if len(st.queue) < 2:
            return await ctx.send(embed=warn_embed("پێدڤییە لانیکەم ٢ گۆرانی د ڕیزێ دا هەبن."), delete_after=8)
        random.shuffle(st.queue)
        await self.refresh_message(ctx.guild)
        await ctx.send(embed=ok_embed("🔀 ڕیز هاتە تێکەلکرن", f"**{len(st.queue)}** گۆرانی", ctx=ctx))

    # z queue [لاپەڕە]
    @commands.command(name="queue", aliases=["q", "list"])
    async def queue_cmd(self, ctx, page: int = 1):
        st = self.states.get(ctx.guild.id)
        if not st or (not st.current and not st.queue):
            return await ctx.send(embed=warn_embed(f"چ تشت نینن. `{PREFIX} play <ناڤ>` بنڤیسە."), delete_after=8)
        view = QueueView(self, ctx.guild.id, page - 1)
        await ctx.send(embed=view.build(), view=view)

    # z nowplaying
    @commands.command(name="nowplaying", aliases=["np", "current"])
    async def nowplaying(self, ctx):
        st = self.states.get(ctx.guild.id)
        if not st or not st.current:
            return await ctx.send(embed=warn_embed("چ گۆرانی ناهێنە لێدان."), delete_after=8)
        await ctx.send(embed=self.now_embed(ctx.guild, st))

    # z removesong <ژمارە>
    @commands.command(name="removesong", aliases=["rs"])
    async def removesong(self, ctx, number: int):
        res = await self.check(ctx, need_playing=False)
        if not res:
            return
        st, _ = res
        if not 1 <= number <= len(st.queue):
            return await ctx.send(embed=error_embed(f"ژمارەکێ د ناڤبەرا `1` و `{len(st.queue)}` دا بنڤیسە."), delete_after=8)
        track = st.queue.pop(number - 1)
        await ctx.send(embed=ok_embed("🗑️ ژ ڕیزێ هاتە لابرن", f"[{trim(track.title, 80)}]({track.url})", ctx=ctx))

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
        await ctx.send(embed=ok_embed("🧹 ڕیز هاتە پاقژکرن", f"**{count}** گۆرانی هاتنە لابرن.", ctx=ctx))

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
            return await ctx.send(embed=error_embed(f"ژمارەکێ د ناڤبەرا `1` و `{len(st.queue)}` دا بنڤیسە."), delete_after=8)
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

    # ═══ کتێبخانە: z playlist / z like / z recent ═══

    # z playlist ─ داشبۆردا کتێبخانێ
    @commands.group(name="playlist", aliases=["pl", "playlists", "library", "lib"], invoke_without_command=True)
    async def playlist(self, ctx):
        view = DashboardView(self, ctx.author)
        view.message = await ctx.send(embed=view.build(), view=view)

    # z pl create <ناڤ>
    @playlist.command(name="create", aliases=["new"])
    async def pl_create(self, ctx, *, name: str):
        res = lib_create(ctx.author.id, name)
        if res != "ok":
            return await ctx.send(embed=error_embed(CREATE_ERRORS[res], ctx=ctx), delete_after=10)
        await ctx.send(embed=ok_embed("🎼 لیست هاتە چێکرن", f"**{discord.utils.escape_markdown(' '.join(name.split())[:MAX_PLAYLIST_NAME])}**\n"
                                       f"گۆرانیەکێ لێدە و 💾 بگوشە، یان `{PREFIX} pl add <ناڤ>` بنڤیسە.", ctx=ctx))

    # z pl delete <ناڤ/ژمارە>
    @playlist.command(name="delete", aliases=["del"])
    async def pl_delete(self, ctx, *, ref: str):
        r = lib_resolve(ctx.author.id, ref)
        if r is None or r.kind != "playlist":
            return await ctx.send(embed=error_embed("ئەو لیست نەهاتە دیتن (Favorites/Recent ناهێنە ژێبرن)."), delete_after=10)
        lib_delete(r.id)
        await ctx.send(embed=ok_embed("🗑️ لیست هاتە ژێبرن", f"**{discord.utils.escape_markdown(r.name)}**", ctx=ctx))

    # z pl add <ناڤ/ژمارە/fav> ─ گۆرانیا نوکە دکەتە ناڤ لیستێ
    @playlist.command(name="add")
    async def pl_add(self, ctx, *, ref: str):
        st = self.states.get(ctx.guild.id)
        if not st or not st.current:
            return await ctx.send(embed=error_embed("چ گۆرانی ناهێنە لێدان بۆ زێدەکرنێ."), delete_after=8)
        r = lib_resolve(ctx.author.id, ref)
        if r is None or r.kind == "recent":
            return await ctx.send(embed=error_embed(f"ئەو لیست نەهاتە دیتن. `{PREFIX} playlist` ببینە."), delete_after=10)
        res = lib_add(r.id, st.current)
        await ctx.send(embed=ok_embed(r.title, f"{ADD_TEXT[res]}\n[{trim(st.current.title, 80)}]({st.current.url})", ctx=ctx))

    # z pl remove <ناڤ/ژمارا لیستێ> <ژمارا گۆرانیێ>
    @playlist.command(name="remove", aliases=["rm"])
    async def pl_remove(self, ctx, *, args: str):
        parts = args.rsplit(None, 1)
        if len(parts) != 2 or not parts[1].isdigit():
            return await ctx.send(embed=error_embed(f"`{PREFIX} pl remove <ناڤێ لیستێ> <ژمارا گۆرانیێ>`"), delete_after=10)
        r = lib_resolve(ctx.author.id, parts[0])
        if r is None or r.kind == "recent":
            return await ctx.send(embed=error_embed("ئەو لیست نەهاتە دیتن."), delete_after=10)
        title = lib_remove_track(r.id, int(parts[1]))
        if title is None:
            return await ctx.send(embed=error_embed("ئەو ژمارە د لیستێ دا نینە."), delete_after=10)
        await ctx.send(embed=ok_embed("🗑️ هاتە لابرن", f"**{trim(title, 80)}** ژ {r.title}", ctx=ctx))

    # z pl play <ناڤ/ژمارە> / z pl shuffle <ناڤ/ژمارە>
    async def _pl_play(self, ctx, ref, shuffle):
        r = lib_resolve(ctx.author.id, ref)
        if r is None:
            return await ctx.send(embed=error_embed(f"ئەو لیست نەهاتە دیتن. `{PREFIX} playlist` ببینە."), delete_after=10)
        await self.enqueue_saved(ctx.guild, ctx.channel, ctx.author, lib_tracks(r), shuffle=shuffle, label=r.title)

    @playlist.command(name="play", aliases=["p"])
    async def pl_play(self, ctx, *, ref: str):
        await self._pl_play(ctx, ref, False)

    @playlist.command(name="shuffle", aliases=["mix"])
    async def pl_shuffle(self, ctx, *, ref: str):
        await self._pl_play(ctx, ref, True)

    # z pl view <ناڤ/ژمارە>
    @playlist.command(name="view", aliases=["open", "show"])
    async def pl_view(self, ctx, *, ref: str):
        r = lib_resolve(ctx.author.id, ref)
        if r is None:
            return await ctx.send(embed=error_embed(f"ئەو لیست نەهاتە دیتن. `{PREFIX} playlist` ببینە."), delete_after=10)
        view = ListView(self, ctx.author, r)
        view.message = await ctx.send(embed=view.build(), view=view)

    # z like ─ گۆرانیا نوکە دکەتە / لادبەت ژ ❤️ Favorites
    @commands.command(name="like", aliases=["love"])
    async def like(self, ctx):
        st = self.states.get(ctx.guild.id)
        if not st or not st.current:
            return await ctx.send(embed=error_embed("چ گۆرانی ناهێنە لێدان."), delete_after=8)
        res = lib_toggle_fav(ctx.author.id, st.current)
        title = {"added": "❤️ هاتە زێدەکرن بۆ Favorites", "removed": "💔 ژ Favorites هاتە لابرن", "full": "❌ Favorites تژییە"}[res]
        await ctx.send(embed=ok_embed(title, f"[{trim(st.current.title, 80)}]({st.current.url})", ctx=ctx))

    # z likes ─ لیستا Favorites
    @commands.command(name="likes", aliases=["favs", "favorites"])
    async def likes(self, ctx):
        view = ListView(self, ctx.author, LibRef("fav", lib_fav_id(ctx.author.id), FAV_TITLE, ctx.author.id))
        view.message = await ctx.send(embed=view.build(), view=view)

    # z recent ─ Recently Played
    @commands.command(name="recent", aliases=["recently"])
    async def recent(self, ctx):
        view = ListView(self, ctx.author, LibRef("recent", 0, "Recently Played", ctx.author.id))
        view.message = await ctx.send(embed=view.build(), view=view)

    # z menu
    @commands.command(name="menu", aliases=["songs", "artists"])
    async def menu(self, ctx):
        if not ctx.author.voice:
            return await ctx.send(embed=error_embed("سەرەتا بچە ناڤ ڤۆیسەکێ."), delete_after=8)
        artists = "\n".join(f"🎙️ **{d['name']}** ─ `{len(d['songs'])}` گۆرانی" for d in ARTISTS_DATA.values())
        embed = make_embed(
            "🎶 Zero Music ─ داشبۆرد",
            (
                f"👋 سلاڤ **{discord.utils.escape_markdown(ctx.author.display_name)}**!\n"
                f"هونەرمەندەکێ ل خوارێ هەلبژێرە و گۆرانیا وی لێدە.\n\n"
                f"{'─' * 18}\n{artists}\n{'─' * 18}\n\n"
                f"💡 یان ڕاستەخۆ: `{PREFIX} play <ناڤ یان لینکێ YouTube/TikTok>`"
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
