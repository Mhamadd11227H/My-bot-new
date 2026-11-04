"""
Studio: پانێلا تایبەت بۆ خاوەنێ بوتی (تەنێ تو دبینی) ب button و لیست
ژ ڤێرێ دشێی: ئیمۆجییان ب وێنە/GIF بگوهۆڕی، ناڤ بۆ دانی، وێنەیان بەڕێڤە ببەی
هەمی ل ناڤ Discord ــێ، بێ دەستکاریکرنا کۆدی.

فەرمان:  z studio   ← دوگمەیەکێ دنێریت، تو لێ دەگریت و پانێلا تایبەت (ephemeral) بۆ تە دکەڤیت
"""
import asyncio
import math
import os
import re
import uuid
from collections import Counter

import discord
from discord.ext import commands

import emoji_swap as ES
import media_store as M
from utils import make_embed, PREFIX, MAIN, SUCCESS
from cogs.emoji import _shrink_sync, EMOJI_MAX_BYTES, TAG_RE, TYPE_TO_EXT

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PER = 25   # سنوورێ Select ل Discord

# ئیمۆجی ل هەر پارچەیەکێ بوتی ژ سەر کۆدی دهێنە دۆزین
SECTIONS = {
    "help":    ("📖 Help",              ["help.py"]),
    "economy": ("💰 Economy",           ["economy.py", "database.py"]),
    "slots":   ("🎰 Slots",             ["slots.py"]),
    "hunt":    ("🐾 Hunt",              ["hunt.py", "hunt_core.py"]),
    "animals": ("🦌 Hunt: ئاژەل و داتا", ["hunt_data.py"]),
    "welcome": ("👋 Welcome",           ["welcome.py"]),
    "general": ("⚙️ گشتی (bot/utils)",  ["bot.py", "utils.py", "owner.py"]),
}
CHANGED = "__changed__"

EMOJI_RE = re.compile(
    r"<a?:\w+:\d+>"
    r"|[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\u25B6\u25C0]\ufe0f?"
)


def _src(fn):
    for d in (BASE, os.path.join(BASE, "cogs")):
        p = os.path.join(d, fn)
        if os.path.isfile(p):
            return p
    return None


def _disp(key):
    """ئیمۆجییەکێ ب شێوازێ ئیمۆجی نیشان بدە (نەک دەق)"""
    if key.startswith("<") or len(key) != 1 or ord(key) >= 0x1F000:
        return key
    return key + ES.FE0F


def _show(key):
    """بێ ئەوەی ب emoji_swap بهێتە گوهۆڕین نیشان بدە"""
    return _disp(key) + ES.BYPASS


def _label(key):
    if key.startswith("<"):
        m = re.fullmatch(r"<a?:(\w+):\d+>", key)
        return "custom:" + (m.group(1) if m else "?")
    return _disp(key)


def _emoji_name(name):
    base = re.sub(r"[^A-Za-z0-9_]", "", name or "")
    if len(base) < 2:
        base = "ze"
    return (base[:26] + "_" + uuid.uuid4().hex[:4])[:32]


def _thumb(tag):
    m = re.fullmatch(r"<(a?):\w+:(\d+)>", tag or "")
    if not m:
        return None
    return f"https://cdn.discordapp.com/emojis/{m.group(2)}.{'gif' if m.group(1) else 'png'}?size=96"


def _mb(n):
    return f"{n / 1024 / 1024:.1f}MB" if n >= 1024 * 1024 else f"{max(1, n // 1024)}KB"


# ═══════════════════════════════════════
# Modal ی ناڤ / تێکست
# ═══════════════════════════════════════
class TextModal(discord.ui.Modal):
    def __init__(self, title, label, callback, default=None, required=True, placeholder=None, max_length=64):
        super().__init__(title=title[:45])
        self.cb = callback
        self.inp = discord.ui.TextInput(
            label=label[:45], default=default or None, required=required,
            placeholder=placeholder, max_length=max_length,
        )
        self.add_item(self.inp)

    async def on_submit(self, inter):
        await self.cb(inter, (self.inp.value or "").strip())


# ═══════════════════════════════════════
# دوگمەیا کرنا پانێلێ
# ═══════════════════════════════════════
class OpenView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog
        b = discord.ui.Button(label="🎛️ پانێلێ ڤەکە", style=discord.ButtonStyle.primary)
        b.callback = self.open
        self.add_item(b)

    async def interaction_check(self, inter):
        if await self.cog.bot.is_owner(inter.user):
            return True
        await inter.response.send_message("❌ ئەڤە تەنێ بۆ خاوەنێ بوتییە", ephemeral=True)
        return False

    async def open(self, inter):
        view = Studio(self.cog, inter)
        await inter.response.send_message(embed=view.embed(), view=view, ephemeral=True)
        try:
            await inter.message.delete()
        except discord.HTTPException:
            pass
        self.stop()


# ═══════════════════════════════════════
# پانێلا سەرەکی
# ═══════════════════════════════════════
class Studio(discord.ui.View):
    def __init__(self, cog, root):
        super().__init__(timeout=840)   # کێمتر ژ ١٥ خولەکان (کاتێ token ی interaction)
        self.cog = cog
        self.root = root                # interaction ێ کو پانێل پێ هاتیە ڤەکرن
        self.mode = "home"
        self.section = None
        self.items = []                 # [(key, count)]
        self.page = 0
        self.sel = None                 # ئیمۆجیێ هەلبژارتی
        self.mpage = 0
        self.msel = None                # وێنەیێ هەلبژارتی ل گەنجینێ
        self.note = None
        self.build()

    async def interaction_check(self, inter):
        if await self.cog.bot.is_owner(inter.user):
            return True
        await inter.response.send_message("❌ ئەڤە تەنێ بۆ خاوەنێ بوتییە", ephemeral=True)
        return False

    # ── هاریکار ──
    def _btn(self, label, cb, style=discord.ButtonStyle.secondary, row=None, disabled=False):
        b = discord.ui.Button(label=label, style=style, row=row, disabled=disabled)
        b.callback = cb
        self.add_item(b)

    def _pages(self, n):
        return max(1, math.ceil(n / PER))

    async def refresh(self, inter):
        self.build()
        await inter.response.edit_message(embed=self.embed(), view=self)

    async def refresh_root(self):
        self.build()
        try:
            await self.root.edit_original_response(embed=self.embed(), view=self)
        except discord.HTTPException:
            pass

    # ── ئێمبێد ──
    def embed(self):
        note = f"\n\n{self.note}" if self.note else ""
        if self.mode == "home":
            return make_embed(
                "🎛️  Studio",
                "> تەنێ تو ڤێ پانێلێ دبینی\n"
                "───────────────────────────\n"
                "**١.** پارچەیەکێ بوتی هەلبژێرە (Help، Slots، Hunt...)\n"
                "**٢.** ئیمۆجییەکێ هەلبژێرە\n"
                "**٣.** ب وێنە/GIF ێ خۆ بگوهۆڕە و ناڤەکی بۆ دانە\n"
                "───────────────────────────\n"
                f"✅ گوهۆڕدراو: **{len(ES.get_all())}** · 🖼️ وێنە ل گەنجینێ: **{len(M.names())}**" + note,
                color=MAIN)
        if self.mode == "section":
            total = self._pages(len(self.items))
            chunk = self.items[self.page * PER:(self.page + 1) * PER]
            title = "✅ گوهۆڕدراو" if self.section == CHANGED else SECTIONS[self.section][0]
            lines = []
            for k, c in chunk:
                ent = ES.get(k)
                if ent:
                    nm = f" · **{ent['name']}**" if ent.get("name") else ""
                    lines.append(f"{_show(k)} ➜ {ent['tag']}{nm}")
                else:
                    lines.append(f"{_show(k)} · ×{c}")
            body = "\n".join(lines) or "*هیچ ئیمۆجییەک نەهاتە دۆزین*"
            return make_embed(f"{title}  ({self.page + 1}/{total})",
                              body + "\n\n> ئیمۆجییەکێ ژ لیستا خوارێ هەلبژێرە" + note, color=MAIN)
        if self.mode in ("emoji", "pick_media"):
            k = self.sel
            ent = ES.get(k)
            if ent:
                cur = f"{ent['tag']}" + (f"\n**ناڤ:** `{ent['name']}`" if ent.get("name") else "\n**ناڤ:** *نەهاتیە دانان*")
            else:
                cur = "*ڕەسەنە، نەهاتیە گوهۆڕین*"
            where = [lab for key, (lab, _) in SECTIONS.items()
                     if any(x == k for x, _c in self.cog.items_for(key))]
            e = make_embed(
                f"🎨  {_show(k)}  {'(گەنجینە)' if self.mode == 'pick_media' else ''}",
                f"**ئێستا:** {cur}\n**ل ڤان پارچان:** {', '.join(where) or '—'}" + note,
                color=MAIN)
            th = _thumb(ent["tag"]) if ent else None
            if th:
                e.set_thumbnail(url=th)
            return e
        if self.mode == "media":
            items = M.names()
            total = self._pages(len(items))
            slots = M.get_slots()
            used = {}
            for s, n in slots.items():
                used.setdefault(n, []).append(s)
            chunk = items[self.mpage * PER:(self.mpage + 1) * PER]
            lines = [f"▫️ **{k}** · `{os.path.splitext(f)[1][1:].upper()}` · `{_mb(sz)}`"
                     + (f" · 📌 {', '.join(used[k])}" if k in used else "")
                     for k, f, sz in chunk]
            return make_embed(f"🖼️  گەنجینەی وێنەیان  ({self.mpage + 1}/{total})",
                              ("\n".join(lines) or "*ڤاڵایە. ب ➕ وێنەیەکێ زێدە بکە*") + note, color=MAIN)
        if self.mode == "media_item":
            return make_embed(f"🖼️  {self.msel}",
                              "وێنەیەکێ ل گەنجینێ. دشێی ناڤێ وێ بگوهۆڕی، بسڕی، یان بۆ پارچەیەکێ بکاربینی" + note,
                              color=MAIN)
        return make_embed("🎛️  Studio", note or None, color=MAIN)

    # ── کۆمپۆنێنت ──
    def build(self):
        self.clear_items()
        m = self.mode
        if m in ("home", "section"):
            self._add_section_select()
        if m == "home":
            self._btn("🖼️ گەنجینەی وێنەیان", self.go_media, discord.ButtonStyle.primary, row=1)
            self._btn("✖ داخە", self.close, discord.ButtonStyle.danger, row=1)
        elif m == "section":
            if self.items:
                self._add_emoji_select()
            total = self._pages(len(self.items))
            self._btn("◀", self.prev, row=2, disabled=self.page <= 0)
            self._btn("▶", self.next, row=2, disabled=self.page >= total - 1)
            self._btn("🏠", self.go_home, row=2)
        elif m == "emoji":
            ent = ES.get(self.sel)
            self._btn("🖼️ وێنە بنێرە", self.ask_upload, discord.ButtonStyle.primary, row=0)
            self._btn("📚 ژ گەنجینێ", self.go_pick_media, row=0)
            self._btn("🔗 ئیمۆجیێ ئامادە", self.ask_tag, row=0)
            self._btn("✏️ ناڤ", self.ask_rename, row=1, disabled=not ent)
            self._btn("♻️ ڤەگەڕاندن", self.do_reset, discord.ButtonStyle.danger, row=1, disabled=not ent)
            self._btn("⬅️ ڤەگەڕە", self.back_section, row=1)
        elif m == "pick_media":
            names = M.names()
            if names:
                chunk = names[self.mpage * PER:(self.mpage + 1) * PER]
                sel = discord.ui.Select(
                    placeholder="وێنەیەکێ هەلبژێرە...", row=0,
                    options=[discord.SelectOption(label=k[:100], value=k,
                                                  description=f"{os.path.splitext(f)[1][1:].upper()} · {_mb(sz)}")
                             for k, f, sz in chunk])
                sel.callback = self.pick_media_cb
                self.add_item(sel)
            total = self._pages(len(names))
            self._btn("◀", self.mprev, row=1, disabled=self.mpage <= 0)
            self._btn("▶", self.mnext, row=1, disabled=self.mpage >= total - 1)
            self._btn("⬅️ ڤەگەڕە", self.back_emoji, row=1)
        elif m == "media":
            names = M.names()
            if names:
                chunk = names[self.mpage * PER:(self.mpage + 1) * PER]
                sel = discord.ui.Select(
                    placeholder="وێنەیەکێ هەلبژێرە...", row=0,
                    options=[discord.SelectOption(label=k[:100], value=k,
                                                  description=f"{os.path.splitext(f)[1][1:].upper()} · {_mb(sz)}")
                             for k, f, sz in chunk])
                sel.callback = self.media_pick_cb
                self.add_item(sel)
            total = self._pages(len(names))
            self._btn("➕ زێدەکرن", self.ask_media_add, discord.ButtonStyle.success, row=1)
            self._btn("◀", self.mprev, row=1, disabled=self.mpage <= 0)
            self._btn("▶", self.mnext, row=1, disabled=self.mpage >= total - 1)
            self._btn("🏠", self.go_home, row=1)
        elif m == "media_item":
            opts = [discord.SelectOption(label=f"📌 بکاربینە بۆ: {s}", value=s, description=d[:100])
                    for s, d in M.SLOTS.items()]
            opts.append(discord.SelectOption(label="❎ ژ هەمی پارچان لابە", value="__unset__"))
            sel = discord.ui.Select(placeholder="بکاربینە بۆ پارچەیەکێ بوتی...", options=opts[:25], row=0)
            sel.callback = self.slot_cb
            self.add_item(sel)
            self._btn("👁️ ببینە", self.media_preview, row=1)
            self._btn("✏️ ناڤ", self.ask_media_rename, row=1)
            self._btn("🗑️ بسڕە", self.media_delete, discord.ButtonStyle.danger, row=1)
            self._btn("⬅️ ڤەگەڕە", self.go_media, row=1)

    def _add_section_select(self):
        opts = [discord.SelectOption(label=lab, value=key, default=(key == self.section))
                for key, (lab, _f) in SECTIONS.items()]
        opts.append(discord.SelectOption(label=f"✅ گوهۆڕدراو ({len(ES.get_all())})", value=CHANGED,
                                         default=(self.section == CHANGED)))
        sel = discord.ui.Select(placeholder="پارچەیەکێ بوتی هەلبژێرە...", options=opts, row=0)
        sel.callback = self.section_cb
        self.add_item(sel)

    def _add_emoji_select(self):
        chunk = self.items[self.page * PER:(self.page + 1) * PER]
        opts = []
        for i, (k, c) in enumerate(chunk):
            ent = ES.get(k)
            lab = ("✅ " if ent else "") + _label(k) + (f" · {ent['name']}" if ent and ent.get("name") else "")
            opts.append(discord.SelectOption(label=lab[:100], value=str(self.page * PER + i),
                                             description=(f"×{c}" if c else None)))
        sel = discord.ui.Select(placeholder="ئیمۆجییەکێ هەلبژێرە...", options=opts, row=1)
        sel.callback = self.emoji_cb
        self.add_item(sel)

    # ── گەڕان ──
    async def go_home(self, inter):
        self.mode, self.note = "home", None
        await self.refresh(inter)

    async def close(self, inter):
        await inter.response.edit_message(content="✖ پانێل هاتە داخستن", embed=None, view=None)
        self.stop()

    async def section_cb(self, inter):
        self.section = inter.data["values"][0]
        self.items = self.cog.items_for(self.section)
        self.page, self.mode, self.note = 0, "section", None
        await self.refresh(inter)

    async def prev(self, inter):
        self.page -= 1
        await self.refresh(inter)

    async def next(self, inter):
        self.page += 1
        await self.refresh(inter)

    async def mprev(self, inter):
        self.mpage -= 1
        await self.refresh(inter)

    async def mnext(self, inter):
        self.mpage += 1
        await self.refresh(inter)

    async def emoji_cb(self, inter):
        idx = int(inter.data["values"][0])
        self.sel = self.items[idx][0]
        self.mode, self.note = "emoji", None
        await self.refresh(inter)

    async def back_section(self, inter):
        if self.section == CHANGED:
            self.items = self.cog.items_for(CHANGED)
        self.mode, self.note = "section", None
        await self.refresh(inter)

    async def back_emoji(self, inter):
        self.mode, self.note = "emoji", None
        await self.refresh(inter)

    # ── گوهۆڕینا ئیمۆجیێ ──
    async def ask_upload(self, inter):
        ent = ES.get(self.sel)
        await inter.response.send_modal(TextModal(
            "ناڤ بۆ ڤێ گوهۆڕینێ", "ناڤ (ئارەزوومەندانە)", self.after_name_upload,
            default=(ent or {}).get("name"), required=False, placeholder="نموونە: شێر، دراو..."))

    async def after_name_upload(self, inter, name):
        self.note = "📤 **وێنە یان GIF ێ ل ڤێ چەناڵێ بنێرە** (٩٠ چرکە)"
        self.build()
        await inter.response.edit_message(embed=self.embed(), view=self)
        got = await self.cog.wait_image(inter.user.id, inter.channel_id)
        if isinstance(got, str):
            self.note = f"❌ {got}"
        else:
            self.note = await self.cog.apply(self.sel, got[0], got[1], name or None, inter.guild)
        await self.refresh_root()

    async def go_pick_media(self, inter):
        self.mode, self.mpage, self.note = "pick_media", 0, None
        await self.refresh(inter)

    async def pick_media_cb(self, inter):
        name = inter.data["values"][0]
        found = M.find(name)
        if not found:
            self.note = "❌ وێنە نەهاتە دۆزین"
            return await self.refresh(inter)
        self.mode = "emoji"
        self.note = "⏳ دهێتە چێکرن..."
        self.build()
        await inter.response.edit_message(embed=self.embed(), view=self)
        path, fn = found
        with open(path, "rb") as f:
            data = f.read()
        ext = "." + fn.rsplit(".", 1)[-1]
        ent = ES.get(self.sel)
        self.note = await self.cog.apply(self.sel, data, ext, (ent or {}).get("name") or name, inter.guild)
        await self.refresh_root()

    async def ask_tag(self, inter):
        await inter.response.send_modal(TextModal(
            "ئیمۆجیێ ئامادە", "ئیمۆجی (custom)", self.after_tag,
            placeholder="<:ناڤ:123456789> یان <a:ناڤ:123456789>", max_length=100))

    async def after_tag(self, inter, text):
        m = TAG_RE.search(text)
        if not m:
            self.note = "❌ فۆرمات نەدروستە. نموونە: `<:name:123456789>`"
        else:
            tag = m.group(0)
            prev = ES.get(self.sel)
            ES.set_mapping(self.sel, tag, emoji_id=re.search(r":(\d+)>", tag).group(1), created=None)
            if prev:
                await self.cog.delete_created(prev)
            self.note = "✅ هاتە گوهۆڕین"
        await self.refresh(inter)

    async def ask_rename(self, inter):
        ent = ES.get(self.sel) or {}
        await inter.response.send_modal(TextModal(
            "ناڤ بگوهۆڕە", "ناڤێ نوی", self.after_rename, default=ent.get("name"), required=False))

    async def after_rename(self, inter, name):
        ent = ES.get(self.sel)
        if ent:
            ES.set_name(self.sel, name or None)
            await self.cog.rename_discord_emoji(ent, name)
            self.note = f"✅ ناڤ بوو `{name}`" if name else "✅ ناڤ هاتە لابرن"
        await self.refresh(inter)

    async def do_reset(self, inter):
        entry = ES.remove_mapping(self.sel)
        if entry:
            await self.cog.delete_created(entry)
        self.note = "♻️ ڤەگەڕیا بۆ ئیمۆجیێ ڕەسەن"
        await self.refresh(inter)

    # ── گەنجینەی وێنەیان ──
    async def go_media(self, inter):
        self.mode, self.mpage, self.note = "media", 0, None
        await self.refresh(inter)

    async def media_pick_cb(self, inter):
        self.msel = inter.data["values"][0]
        self.mode, self.note = "media_item", None
        await self.refresh(inter)

    async def ask_media_add(self, inter):
        await inter.response.send_modal(TextModal(
            "وێنەیەکێ نوی", "ناڤ", self.after_media_add, placeholder="نموونە: zero-neon", max_length=M.MAX_NAME))

    async def after_media_add(self, inter, name):
        if M.clean_name(name) is None:
            self.note = f"❌ ناڤ دڤێت ژ ١ هەتا {M.MAX_NAME} پیت بیت"
            return await self.refresh(inter)
        self.note = "📤 **وێنە یان GIF ێ ل ڤێ چەناڤێ بنێرە** (٩٠ چرکە)"
        self.build()
        await inter.response.edit_message(embed=self.embed(), view=self)
        got = await self.cog.wait_image(inter.user.id, inter.channel_id)
        if isinstance(got, str):
            self.note = f"❌ {got}"
        else:
            key, replaced = M.add(name, got[0], got[1])
            if key is None:
                self.note = "❌ " + {"bad_name": "ناڤ نەدروستە", "bad_type": "جۆرێ فایلی نەدروستە",
                                     "too_big": f"زۆر مەزنە (زۆرترین {_mb(M.MAX_BYTES)})"}.get(replaced, "هەڵەیەک چێبوو")
            else:
                self.note = f"✅ `{key}` " + ("هاتە گوهۆڕین" if replaced else "هاتە پاراستن")
        await self.refresh_root()

    async def media_preview(self, inter):
        file, ref = M.as_discord_file(self.msel)
        if file is None:
            self.note = "❌ وێنە نەهاتە دۆزین"
            return await self.refresh(inter)
        e = make_embed(f"🖼️  {self.msel}", color=MAIN)
        e.set_image(url=ref)
        await inter.response.send_message(embed=e, file=file, ephemeral=True)

    async def ask_media_rename(self, inter):
        await inter.response.send_modal(TextModal(
            "ناڤێ وێنەی", "ناڤێ نوی", self.after_media_rename, default=self.msel, max_length=M.MAX_NAME))

    async def after_media_rename(self, inter, new):
        res = M.rename(self.msel, new)
        if res == "ok":
            self.msel = M.clean_name(new)
            self.note = f"✅ ناڤ بوو `{self.msel}`"
        else:
            self.note = {"missing": "❌ وێنە نەهاتە دۆزین", "exists": "❌ ئەڤ ناڤە هەیە",
                         "bad_name": "❌ ناڤ نەدروستە"}[res]
        await self.refresh(inter)

    async def media_delete(self, inter):
        freed = M.remove(self.msel)
        self.mode = "media"
        self.note = f"🗑️ `{self.msel}` هاتە سڕین" + (f" (ژ ڤان پارچان هاتە لابرن: {', '.join(freed)})" if freed else "")
        await self.refresh(inter)

    async def slot_cb(self, inter):
        v = inter.data["values"][0]
        if v == "__unset__":
            for s, n in M.get_slots().items():
                if n == self.msel:
                    M.unset_slot(s)
            self.note = "❎ ژ هەمی پارچان هاتە لابرن"
        else:
            res = M.set_slot(v, self.msel)
            self.note = f"✅ `{self.msel}` بوو وێنەیێ پارچا `{v}`" if res == "ok" else "❌ نەشیا"
        await self.refresh(inter)


# ═══════════════════════════════════════
# Cog
# ═══════════════════════════════════════
class StudioCog(commands.Cog, name="Studio"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        ES.install()   # ئەگەر ژ پێش دامەزراندبیت، چ نادەت

    async def cog_check(self, ctx):
        if not await ctx.bot.is_owner(ctx.author):
            raise commands.NotOwner()
        return True

    @commands.command(name="studio", aliases=["panel", "ui"])
    async def studio(self, ctx):
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        await ctx.send(
            embed=make_embed("🎛️  Studio", "> دوگمێ بکە دا پانێلا تایبەت بۆ تە ڤەبیت. تەنێ تو دبینی", color=MAIN),
            view=OpenView(self))

    # ── پشکنینا کۆدی بۆ دۆزینا ئیمۆجییان ──
    def items_for(self, section):
        if section == CHANGED:
            return [(k, 0) for k in ES.get_all()]
        cnt = Counter()
        for fn in SECTIONS[section][1]:
            p = _src(fn)
            if not p:
                continue
            try:
                with open(p, encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                continue
            for m in EMOJI_RE.findall(text):
                cnt[ES.norm(m)] += 1
        return sorted(cnt.items(), key=lambda kv: -kv[1])

    # ── چاڤەڕێکرنا وێنەیێ ژ تە ──
    async def wait_image(self, uid, channel_id, timeout=90):
        def check(m):
            return m.author.id == uid and m.channel.id == channel_id and bool(m.attachments)
        try:
            m = await self.bot.wait_for("message", check=check, timeout=timeout)
        except asyncio.TimeoutError:
            return "کات بوری. دووبارە هەوڵ بدە"
        att = m.attachments[0]
        ext = os.path.splitext(att.filename)[1].lower() or TYPE_TO_EXT.get((att.content_type or "").split(";")[0], "")
        if ext not in M.ALLOWED_EXT:
            return "تەنێ gif png jpg webp دهێنە قبوولکرن"
        try:
            data = await att.read()
        except discord.HTTPException:
            return "نەشیا وێنە دابەزیت"
        try:
            await m.delete()   # نامەیا وێنەی دسڕین دا چەناڵ پاقژ بمینیت (ئەگەر مۆڵەت هەبیت)
        except discord.HTTPException:
            pass
        return data, ext

    # ── دروستکرنا ئیمۆجیێ و بەستن ──
    async def _create(self, name, data, guild):
        if hasattr(self.bot, "create_application_emoji"):
            e = await self.bot.create_application_emoji(name=name, image=data)
            return e, "app"
        if guild is None:
            raise commands.CommandError("ئەڤ وەشانا discord.py ناشێت ئیمۆجیێ بوتی دروست بکەت. ل ناڤ سێرڤەری بکاربینە یان `pip install -U discord.py`")
        e = await guild.create_custom_emoji(name=name, image=data)
        return e, f"guild:{guild.id}"

    async def apply(self, key, data, ext, name, guild):
        """وێنە دکەتە ئیمۆجی و ب key ڤە دبەستیت. دەقێکێ ئەنجامی دگەڕینیتەڤە"""
        prev = ES.get(key)
        if len(data) > EMOJI_MAX_BYTES:
            small = await asyncio.get_running_loop().run_in_executor(None, _shrink_sync, data, ext)
            if small is None:
                return (f"❌ وێنە زۆر مەزنە (**{len(data) // 1024}KB**) و Discord تەنێ **٢٥٦KB** قبوول دکەت. "
                        "وێنەیەکێ بچووکتر بکاربینە یان `pip install pillow` بکە")
            data = small
        try:
            e, where = await self._create(_emoji_name(name), data, guild)
        except commands.CommandError as ex:
            return f"❌ {ex}"
        except discord.HTTPException as ex:
            return f"❌ Discord ڕەتکر: `{ex.text or ex}`"
        ES.set_mapping(key, str(e), emoji_id=str(e.id), created=where, name=name)
        if prev:
            await self.delete_created(prev)
        return "✅ هاتە گوهۆڕین. ئێستا ل هەمی جهان ب ڤی شێوەیی دیار دبیت"

    async def delete_created(self, entry):
        emo = self.bot.get_cog("Emoji")
        if emo is not None:
            await emo._delete_created(entry)

    async def rename_discord_emoji(self, entry, name):
        """ناڤێ ئیمۆجیێ ل Discord ژی دگوهۆڕیت (ئەگەر بوتی خۆ دروست کربیت)"""
        try:
            if not name or not entry.get("id"):
                return
            created = entry.get("created") or ""
            if created == "app" and hasattr(self.bot, "fetch_application_emoji"):
                e = await self.bot.fetch_application_emoji(int(entry["id"]))
                await e.edit(name=_emoji_name(name))
            elif created.startswith("guild:"):
                g = self.bot.get_guild(int(created.split(":")[1]))
                if g:
                    e = await g.fetch_emoji(int(entry["id"]))
                    await e.edit(name=_emoji_name(name))
        except Exception:
            pass


async def setup(bot):
    await bot.add_cog(StudioCog(bot))
