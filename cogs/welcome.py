import asyncio
import json
import os
import re

import discord
from discord.ext import commands

from database import db, DB_PATH
from utils import make_embed, PREFIX, MAIN, SUCCESS, ERROR, WARN

# ═══════════════════════════════════════
# بەشی ١: داتابەیس
# ═══════════════════════════════════════
db.executescript(
    """
    CREATE TABLE IF NOT EXISTS guild_msgs (
        guild_id INTEGER NOT NULL,
        kind     TEXT    NOT NULL,
        data     TEXT    NOT NULL,
        PRIMARY KEY (guild_id, kind)
    );
    CREATE TABLE IF NOT EXISTS setup_channels (
        guild_id   INTEGER PRIMARY KEY,
        channel_id INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS invite_joins (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id   INTEGER NOT NULL,
        inviter_id INTEGER NOT NULL,
        member_id  INTEGER NOT NULL,
        ts         REAL    NOT NULL,
        has_left   INTEGER NOT NULL DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS idx_invite_joins_inviter ON invite_joins (guild_id, inviter_id);
    CREATE INDEX IF NOT EXISTS idx_invite_joins_member  ON invite_joins (guild_id, member_id);
    """
)

# ئەو وێنە و GIFانەی خەڵک بار دەکەن لێرە پاشەکەوت دەکرێن (لەتەنیشت economy.db)
ASSET_DIR = os.path.join(os.path.dirname(DB_PATH), "welcome_assets")
MAX_UPLOAD = 8 * 1024 * 1024
ALLOWED_EXT = (".gif", ".png", ".jpg", ".jpeg", ".webp")

# ═══════════════════════════════════════
# بەشی ٢: جۆرەکانی نامە و دەقە بنەڕەتییەکان
# ═══════════════════════════════════════
KINDS = {
    "welcome": {"emoji": "👋", "name": "Welcome", "desc": "دەمێ ئەندامەک دهێتە ناڤ سێرڤەری"},
    "invite": {"emoji": "🔗", "name": "Invite", "desc": "کێ ئەندامێ نوی بانگهێشت کر"},
    "leave": {"emoji": "🚪", "name": "Left", "desc": "دەمێ ئەندامەک ژ سێرڤەری دچیتە دەر"},
}

DEFAULTS = {
    "welcome": {
        "enabled": False,
        "channel": 0,
        "content": "{user}",
        "title": "🎉 بخێر بێی {name}!",
        "description": "ئەم گەلەک دلخۆشن کو تو هاتییە ناڤ **{server}** 💙\nتو ئەندامێ ژمارە **#{count}** یی.",
        "color": 0x2ECC71,
        "image": "",
        "thumb": "user",
        "footer": "{server}",
        "role": 0,
    },
    "invite": {
        "enabled": False,
        "channel": 0,
        "content": "",
        "title": "🔗 ئەندامەکێ نوی هات",
        "description": "{user} هاتە ناڤ سێرڤەری\n📨 بانگهێشتکەر: {inviter}\n📊 ژمارا بانگهێشتێن وی: **{invites}**",
        "color": 0x5865F2,
        "image": "",
        "thumb": "user",
        "footer": "{server}",
    },
    "leave": {
        "enabled": False,
        "channel": 0,
        "content": "",
        "title": "🚪 ئەندامەک دەرکەت",
        "description": "**{username}** ژ سێرڤەری دەرکەت 😢\nنوکە **{count}** ئەندام ماینە.",
        "color": 0xE74C3C,
        "image": "",
        "thumb": "user",
        "footer": "{server}",
    },
}

VARIABLES_HELP = (
    "`{user}` mention • `{name}` ناڤێ دیار • `{username}` یوزەرنەیم • `{id}` ئایدی\n"
    "`{server}` ناڤێ سێرڤەری • `{count}` ژمارا ئەندامان\n"
    "`{created}` دروستبوونا ئەکاونتی • `{joined}` دەمێ هاتنێ\n"
    "`{inviter}` بانگهێشتکەر • `{inviter_name}` ناڤێ وی • `{invites}` ژمارا بانگهێشتێن وی"
)

NAMED_COLORS = {
    "red": 0xE74C3C, "سوور": 0xE74C3C, "sor": 0xE74C3C,
    "blue": 0x3498DB, "شین": 0x3498DB,
    "green": 0x2ECC71, "سەوز": 0x2ECC71,
    "yellow": 0xF1C40F, "زەرد": 0xF1C40F,
    "orange": 0xE67E22, "پرتەقاڵی": 0xE67E22,
    "purple": 0x9B59B6, "مۆر": 0x9B59B6,
    "pink": 0xFF69B4, "پەمەیی": 0xFF69B4,
    "cyan": 0x1ABC9C, "ئاسمانی": 0x1ABC9C,
    "gold": 0xFFC700, "زێڕین": 0xFFC700,
    "black": 0x000001, "ڕەش": 0x000001,
    "white": 0xFFFFFF, "سپی": 0xFFFFFF,
}

# ═══════════════════════════════════════
# بەشی ٣: فەرمانێن یارمەتیدەر
# ═══════════════════════════════════════
def load_cfg(guild_id, kind):
    cfg = dict(DEFAULTS[kind])
    row = db.execute(
        "SELECT data FROM guild_msgs WHERE guild_id=? AND kind=?", (guild_id, kind)
    ).fetchone()
    if row:
        try:
            cfg.update(json.loads(row[0]))
        except ValueError:
            pass
    return cfg


def save_cfg(guild_id, kind, cfg):
    db.execute(
        "INSERT INTO guild_msgs (guild_id, kind, data) VALUES (?, ?, ?) "
        "ON CONFLICT(guild_id, kind) DO UPDATE SET data=excluded.data",
        (guild_id, kind, json.dumps(cfg)),
    )
    db.commit()


def fill(text, variables):
    """گۆڕاوان دانە: {user} {server} ... تێکستا نەناسراو وەک خۆی دمینیت"""
    if not text:
        return ""
    return re.sub(r"\{(\w+)\}", lambda m: variables.get(m.group(1), m.group(0)), text)


def parse_color(text):
    t = (text or "").strip().lower().lstrip("#")
    if t in NAMED_COLORS:
        return NAMED_COLORS[t]
    if len(t) == 3:
        t = "".join(c * 2 for c in t)
    if len(t) == 6:
        try:
            return int(t, 16)
        except ValueError:
            return None
    return None


def cut(text, n):
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "…"


def local_image_path(cfg):
    img = cfg.get("image", "")
    if img.startswith("file:"):
        name = os.path.basename(img[5:])
        path = os.path.join(ASSET_DIR, name)
        if os.path.isfile(path):
            return name, path
    return None, None


def delete_local_images(guild_id, kind, keep=None):
    for ext in ALLOWED_EXT:
        name = f"{guild_id}_{kind}{ext}"
        if name == keep:
            continue
        path = os.path.join(ASSET_DIR, name)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass


def invite_stats(guild_id, user_id):
    row = db.execute(
        "SELECT COALESCE(SUM(has_left = 0), 0), COALESCE(SUM(has_left = 1), 0) "
        "FROM invite_joins WHERE guild_id=? AND inviter_id=?",
        (guild_id, user_id),
    ).fetchone()
    return int(row[0]), int(row[1])


def make_vars(guild, member, inviter_id=None, inviter_name=None, invites=0):
    return {
        "user": member.mention,
        "username": member.name,
        "name": member.display_name,
        "id": str(member.id),
        "server": guild.name,
        "count": str(guild.member_count),
        "created": discord.utils.format_dt(member.created_at, "R"),
        "joined": discord.utils.format_dt(member.joined_at, "R") if member.joined_at else "؟",
        "inviter": f"<@{inviter_id}>" if inviter_id else "نەدیار",
        "inviter_name": inviter_name or "نەدیار",
        "invites": str(invites),
    }


def build_message(guild, member, cfg, variables):
    """(content, embed, file) ئامادە دکەت"""
    content = fill(cfg.get("content"), variables) or None
    embed = discord.Embed(
        title=cut(fill(cfg.get("title"), variables), 256) or None,
        description=cut(fill(cfg.get("description"), variables), 4000) or None,
        color=cfg.get("color", MAIN),
        timestamp=discord.utils.utcnow(),
    )
    thumb = cfg.get("thumb", "user")
    if thumb == "user":
        embed.set_thumbnail(url=member.display_avatar.url)
    elif thumb == "server" and guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    footer = fill(cfg.get("footer"), variables)
    if footer:
        embed.set_footer(text=cut(footer, 2048))

    file = None
    name, path = local_image_path(cfg)
    if name:
        file = discord.File(path, filename=name)
        embed.set_image(url=f"attachment://{name}")
    elif cfg.get("image", "").startswith(("http://", "https://")):
        embed.set_image(url=cfg["image"])

    # کارتێ بێ هیچ ناڤەڕۆکەکێ Discord قەبوول ناکەت
    if not (embed.title or embed.description or footer or file or cfg.get("image")):
        embed.description = "\u200b"
    return content, embed, file


async def owner_only(interaction):
    guild = interaction.guild
    if guild and interaction.user.id == guild.owner_id:
        return True
    await interaction.response.send_message(
        "❌ تەنێ خودانێ سێرڤەری دشێت ڤێ بکاربینیت.", ephemeral=True
    )
    return False


def main_embed(guild):
    lines = []
    for kind, meta in KINDS.items():
        cfg = load_cfg(guild.id, kind)
        ch = guild.get_channel(cfg["channel"]) if cfg["channel"] else None
        state = "✅" if cfg["enabled"] and ch else "⛔"
        where = ch.mention if ch else "`نەهاتییە دیارکرن`"
        lines.append(f"{state} {meta['emoji']} **{meta['name']}** ─ {meta['desc']}\n　📍 {where}")
    return make_embed(
        "⚙️ ناوەندێ ڕێکخستنێ",
        (
            "ئەڤ ژوورە **تەنێ بۆ تە یە**، کەس نابینیت 🔒\n"
            "بەشەکی هەلبژێرە و هەمی تشتان ب دلێ خوە بگوهۆڕە: دەق، ڕەنگ، وێنە و GIF.\n\n"
            + "\n".join(lines)
        ),
        color=MAIN,
    )


# ═══════════════════════════════════════
# بەشی ٤: مۆداڵ (فۆرمێن نڤیسینێ)
# ═══════════════════════════════════════
class TextModal(discord.ui.Modal, title="✏️ دەق و ناڤونیشان"):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        cfg = editor.cfg
        self.f_content = discord.ui.TextInput(
            label="نامەیا دەرڤەیێ کارتی (mention)",
            default=cfg["content"][:300],
            required=False,
            max_length=300,
            placeholder="{user}",
        )
        self.f_title = discord.ui.TextInput(
            label="ناڤونیشان",
            default=cfg["title"][:256],
            required=False,
            max_length=256,
            placeholder="🎉 بخێر بێی {name}!",
        )
        self.f_desc = discord.ui.TextInput(
            label="دەقێ سەرەکی",
            style=discord.TextStyle.paragraph,
            default=cfg["description"][:2000],
            required=False,
            max_length=2000,
            placeholder="{user} {server} {count} ...",
        )
        self.f_footer = discord.ui.TextInput(
            label="دەقێ خوارێ (footer)",
            default=cfg["footer"][:200],
            required=False,
            max_length=200,
            placeholder="{server}",
        )
        for item in (self.f_content, self.f_title, self.f_desc, self.f_footer):
            self.add_item(item)

    async def on_submit(self, interaction):
        cfg = self.editor.cfg
        cfg["content"] = self.f_content.value.strip()
        cfg["title"] = self.f_title.value.strip()
        cfg["description"] = self.f_desc.value.strip()
        cfg["footer"] = self.f_footer.value.strip()
        await self.editor.save_and_redraw(interaction)


class ColorModal(discord.ui.Modal, title="🎨 ڕەنگێ هێلا کارتی"):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.f_color = discord.ui.TextInput(
            label="ڕەنگ (HEX یان ناڤ)",
            default=f"#{editor.cfg['color']:06X}",
            max_length=20,
            placeholder="#FF0000 یان red / سوور / شین / مۆر",
        )
        self.add_item(self.f_color)

    async def on_submit(self, interaction):
        color = parse_color(self.f_color.value)
        if color is None:
            await interaction.response.send_message(
                "❌ ڕەنگ خەلەتە. نموونە: `#FF0000` یان `red`", ephemeral=True
            )
            return
        self.editor.cfg["color"] = color
        await self.editor.save_and_redraw(interaction)


class ImageUrlModal(discord.ui.Modal, title="🔗 لینکێ وێنە یان GIF"):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        current = editor.cfg["image"] if editor.cfg["image"].startswith("http") else ""
        self.f_url = discord.ui.TextInput(
            label="لینکێ ڕاستەوخۆ (بەتاڵ = ژێبرن)",
            default=current[:400],
            required=False,
            max_length=400,
            placeholder="https://.../image.gif",
        )
        self.add_item(self.f_url)

    async def on_submit(self, interaction):
        url = self.f_url.value.strip()
        ed = self.editor
        if url and not url.startswith(("http://", "https://")):
            await interaction.response.send_message(
                "❌ لینک دڤێت ب `https://` دەست پێ بکەت.", ephemeral=True
            )
            return
        delete_local_images(ed.guild.id, ed.kind)
        ed.cfg["image"] = url
        await ed.save_and_redraw(interaction)


# ═══════════════════════════════════════
# بەشی ٥: لیستێن هەلبژارتنێ
# ═══════════════════════════════════════
class ChannelPick(discord.ui.ChannelSelect):
    def __init__(self, editor):
        super().__init__(
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
            placeholder="📍 کەناڵێ هنارتنێ هەلبژێرە...",
            min_values=1,
            max_values=1,
            row=0,
        )
        self.editor = editor

    async def callback(self, interaction):
        ed = self.editor
        first_time = not ed.cfg["channel"]
        ed.cfg["channel"] = self.values[0].id
        if first_time:
            ed.cfg["enabled"] = True  # یەکەم جار کەناڵ هاتە دیارکرن، خۆکار چالاک دبیت
        await ed.save_and_redraw(interaction)


class RolePick(discord.ui.RoleSelect):
    def __init__(self, editor):
        super().__init__(
            placeholder="🎭 ڕۆلێ خۆکار بۆ ئەندامێن نوی (دلخواز)",
            min_values=0,
            max_values=1,
            row=3,
        )
        self.editor = editor

    async def callback(self, interaction):
        ed = self.editor
        if not self.values:
            ed.cfg["role"] = 0
            await ed.save_and_redraw(interaction)
            return
        role = self.values[0]
        if role.is_default() or role.managed:
            await interaction.response.send_message("❌ ئەڤ ڕۆلە نەشێت بهێتە دان.", ephemeral=True)
            return
        if role >= ed.guild.me.top_role:
            await interaction.response.send_message(
                "❌ ڕۆلێ بۆتی دڤێت ل سەرووی ڤی ڕۆلی بیت (Server Settings ← Roles).",
                ephemeral=True,
            )
            return
        ed.cfg["role"] = role.id
        await ed.save_and_redraw(interaction)


# ═══════════════════════════════════════
# بەشی ٦: پەنێلێ سەرەکی و دەستکاریکەر
# ═══════════════════════════════════════
class MainPanelView(discord.ui.View):
    """پەنێلا سەرەکی. پشتی ڕێستارتێ ژی کار دکەت (persistent)"""

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        for kind, meta in KINDS.items():
            button = discord.ui.Button(
                label=meta["name"],
                emoji=meta["emoji"],
                style=discord.ButtonStyle.primary,
                custom_id=f"zb:panel:{kind}",
            )
            button.callback = self._make_callback(kind)
            self.add_item(button)

    def _make_callback(self, kind):
        async def callback(interaction):
            editor = EditorView(self.cog, interaction.guild, kind)
            editor.message = interaction.message
            await interaction.response.edit_message(embed=editor.build_embed(), view=editor)

        return callback

    async def interaction_check(self, interaction):
        return await owner_only(interaction)


class EditorView(discord.ui.View):
    def __init__(self, cog, guild, kind):
        super().__init__(timeout=900)
        self.cog = cog
        self.guild = guild
        self.kind = kind
        self.cfg = load_cfg(guild.id, kind)
        self.message = None

        self.add_item(ChannelPick(self))
        self.b_text = self._button("دەق", "✏️", discord.ButtonStyle.primary, 1, self.on_text)
        self.b_color = self._button("ڕەنگ", "🎨", discord.ButtonStyle.primary, 1, self.on_color)
        self.b_url = self._button("لینک", "🔗", discord.ButtonStyle.primary, 1, self.on_url)
        self.b_upload = self._button("بارکرن", "📤", discord.ButtonStyle.primary, 1, self.on_upload)
        self.b_thumb = self._button("ئەندام", "👤", discord.ButtonStyle.secondary, 1, self.on_thumb)

        self.b_toggle = self._button("چالاکە", "🔔", discord.ButtonStyle.success, 2, self.on_toggle)
        self._button("پێشبینین", "👁️", discord.ButtonStyle.secondary, 2, self.on_preview)
        self._button("تاقیکرن", "📨", discord.ButtonStyle.secondary, 2, self.on_test)
        self._button("ڕێست", "♻️", discord.ButtonStyle.danger, 2, self.on_reset)
        self._button("ڤەگەڕ", "↩️", discord.ButtonStyle.secondary, 2, self.on_back)

        if kind == "welcome":
            self.add_item(RolePick(self))
        self.sync_buttons()

    def _button(self, label, emoji, style, row, callback):
        button = discord.ui.Button(label=label, emoji=emoji, style=style, row=row)
        button.callback = callback
        self.add_item(button)
        return button

    async def interaction_check(self, interaction):
        return await owner_only(interaction)

    def sync_buttons(self):
        on = self.cfg["enabled"]
        self.b_toggle.label = "چالاکە" if on else "ناچالاکە"
        self.b_toggle.style = discord.ButtonStyle.success if on else discord.ButtonStyle.secondary
        mode = self.cfg["thumb"]
        self.b_thumb.label = {"user": "ئەندام", "server": "سێرڤەر", "none": "نینە"}[mode]
        self.b_thumb.emoji = {"user": "👤", "server": "🏠", "none": "🚫"}[mode]

    def build_embed(self):
        cfg, meta = self.cfg, KINDS[self.kind]
        ch = self.guild.get_channel(cfg["channel"]) if cfg["channel"] else None
        img = cfg["image"]
        if img.startswith("file:"):
            img_txt = "📤 فایلەکێ بارکری"
        elif img:
            img_txt = "🔗 لینک"
        else:
            img_txt = "نینە"
        thumb_txt = {"user": "وێنەیێ ئەندامی", "server": "لۆگۆیێ سێرڤەری", "none": "نینە"}[cfg["thumb"]]

        lines = [
            f"📍 **کەناڵ:** {ch.mention if ch else '`هێشتا نەهاتییە دیارکرن`'}",
            f"🔔 **دۆخ:** {'✅ چالاکە' if cfg['enabled'] else '⛔ ناچالاکە'}",
            f"🎨 **ڕەنگ:** `#{cfg['color']:06X}`",
            f"🖼️ **وێنە/GIF:** {img_txt}",
            f"👤 **وێنەیێ بچووک:** {thumb_txt}",
        ]
        if self.kind == "welcome":
            role = self.guild.get_role(cfg["role"]) if cfg["role"] else None
            lines.append(f"🎭 **ڕۆلێ خۆکار:** {role.mention if role else 'نینە'}")
        if ch:
            perms = ch.permissions_for(self.guild.me)
            if not (perms.send_messages and perms.embed_links):
                lines.append("⚠️ **بۆت ل ڤێ کەناڵێ مۆڵەتا نڤیسینێ و embed ی نینە!**")

        embed = discord.Embed(
            title=f"{meta['emoji']} {meta['name']} ─ ڕێکخستن",
            description="\n".join(lines),
            color=cfg["color"],
        )
        current = f"**{cut(cfg['title'], 120) or '─'}**\n{cut(cfg['description'], 300) or '─'}"
        embed.add_field(name="✏️ دەقێ ئێستا", value=current, inline=False)
        embed.add_field(name="🧩 گۆڕاو (variables)", value=VARIABLES_HELP, inline=False)
        embed.add_field(
            name="💡 ئامۆژگاری",
            value=(
                "• **GIFا جولاو:** 📤 بکلیک بکە و GIFەکێ بۆ ڤێرێ بنێرە، یان لینکەکێ ڕاستەوخۆ یێ `.gif` بدە\n"
                "• 👤 دوگمەیا دوماهیێ وێنەیێ بچووکێ سەرەوە دگوهۆڕیت\n"
                "• 📨 نامەیەکا تاقیکرنێ دنێریتە کەناڵێ"
            ),
            inline=False,
        )
        return embed

    async def save_and_redraw(self, interaction):
        save_cfg(self.guild.id, self.kind, self.cfg)
        self.sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    # ─── دوگمەکان ───
    async def on_text(self, interaction):
        await interaction.response.send_modal(TextModal(self))

    async def on_color(self, interaction):
        await interaction.response.send_modal(ColorModal(self))

    async def on_url(self, interaction):
        await interaction.response.send_modal(ImageUrlModal(self))

    async def on_upload(self, interaction):
        await interaction.response.send_message(
            "📤 نوکە وێنە یان GIFەکێ د ڤێ ژوورێ دا بنێرە (٦٠ چرکە).\n"
            "فۆرمات: gif / png / jpg / webp ─ تا ٨MB.",
            ephemeral=True,
        )

        def check(m):
            return (
                m.author.id == interaction.user.id
                and m.channel.id == interaction.channel_id
                and m.attachments
            )

        try:
            msg = await self.cog.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏱️ دەم ب دوماهی هات. دووبارە بکە.", ephemeral=True)
            return

        att = msg.attachments[0]
        ext = os.path.splitext(att.filename.lower())[1]
        if ext not in ALLOWED_EXT:
            await interaction.followup.send("❌ تەنێ gif / png / jpg / webp.", ephemeral=True)
            return
        if att.size > MAX_UPLOAD:
            await interaction.followup.send("❌ فایل ژ ٨MB مەزنترە.", ephemeral=True)
            return

        data = await att.read()
        os.makedirs(ASSET_DIR, exist_ok=True)
        name = f"{self.guild.id}_{self.kind}{ext}"
        delete_local_images(self.guild.id, self.kind, keep=name)
        with open(os.path.join(ASSET_DIR, name), "wb") as f:
            f.write(data)

        self.cfg["image"] = f"file:{name}"
        save_cfg(self.guild.id, self.kind, self.cfg)
        try:
            await msg.delete()  # کۆپییەک د بۆتی دا هاتە پاراستن
        except discord.HTTPException:
            pass
        self.sync_buttons()
        await interaction.message.edit(embed=self.build_embed(), view=self)
        await interaction.followup.send("✅ وێنە هاتە پاراستن.", ephemeral=True)

    async def on_thumb(self, interaction):
        order = ["user", "server", "none"]
        self.cfg["thumb"] = order[(order.index(self.cfg["thumb"]) + 1) % len(order)]
        await self.save_and_redraw(interaction)

    async def on_toggle(self, interaction):
        if not self.cfg["enabled"] and not self.cfg["channel"]:
            await interaction.response.send_message(
                "❌ بەری چالاککرنێ کەناڵەکێ هەلبژێرە.", ephemeral=True
            )
            return
        self.cfg["enabled"] = not self.cfg["enabled"]
        await self.save_and_redraw(interaction)

    async def on_preview(self, interaction):
        member = interaction.user
        variables = self.cog.sample_vars(self.guild, member)
        content, embed, file = build_message(self.guild, member, self.cfg, variables)
        kwargs = {"embed": embed, "ephemeral": True}
        kwargs["content"] = (content + "\n" if content else "") + "👁️ *پێشبینین (تەنێ تو دبینی)*"
        if file:
            kwargs["file"] = file
        await interaction.response.send_message(**kwargs)

    async def on_test(self, interaction):
        member = interaction.user
        variables = self.cog.sample_vars(self.guild, member)
        ok, err = await self.cog.deliver(self.guild, self.kind, member, variables, force=True)
        if ok:
            ch = self.guild.get_channel(self.cfg["channel"])
            text = f"✅ نامەیا تاقیکرنێ هاتە هنارتن ل {ch.mention}"
        elif err == "no_channel":
            text = "❌ بەری کەناڵەکێ هەلبژێرە."
        elif err == "forbidden":
            text = "❌ بۆت مۆڵەتا نڤیسینێ ل وێ کەناڵێ نینە."
        else:
            text = f"❌ هەلەیەک چێبوو: {err}"
        await interaction.response.send_message(text, ephemeral=True)

    async def on_reset(self, interaction):
        old_channel = self.cfg["channel"]
        delete_local_images(self.guild.id, self.kind)
        self.cfg = dict(DEFAULTS[self.kind])
        self.cfg["channel"] = old_channel
        await self.save_and_redraw(interaction)

    async def on_back(self, interaction):
        self.stop()
        await interaction.response.edit_message(
            embed=main_embed(self.guild), view=MainPanelView(self.cog)
        )

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(embed=main_embed(self.guild), view=MainPanelView(self.cog))
            except discord.HTTPException:
                pass


# ═══════════════════════════════════════
# بەشی ٧: Cog ی سەرەکی
# ═══════════════════════════════════════
class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # guild_id -> {code: (uses, inviter_id, max_uses)}
        self.invites = {}

    async def cog_load(self):
        self.bot.add_view(MainPanelView(self))

    # ─── invite tracking ───
    async def cache_invites(self, guild):
        try:
            invs = await guild.invites()
        except (discord.Forbidden, discord.HTTPException):
            self.invites.pop(guild.id, None)
            return
        self.invites[guild.id] = {
            i.code: (i.uses or 0, i.inviter.id if i.inviter else 0, i.max_uses or 0) for i in invs
        }

    async def find_inviter(self, guild):
        """ئایدیێ بانگهێشتکەری دزڤڕینیت (یان None)"""
        old = self.invites.get(guild.id)
        try:
            current = await guild.invites()
        except (discord.Forbidden, discord.HTTPException):
            return None
        new = {i.code: i for i in current}
        self.invites[guild.id] = {
            c: (i.uses or 0, i.inviter.id if i.inviter else 0, i.max_uses or 0) for c, i in new.items()
        }
        if old is None:
            return None

        # ١) بانگهێشتەک کو ژمارا بکارئینانا وێ زێدە بوویە
        for code, inv in new.items():
            if (inv.uses or 0) > old.get(code, (0, 0, 0))[0] and inv.inviter:
                return inv.inviter.id
        # ٢) بانگهێشتا ئێک-جاری کو پشتی بکارئینانێ هاتییە ژێبرن
        for code, (uses, inviter_id, max_uses) in old.items():
            if code not in new and max_uses and uses + 1 >= max_uses and inviter_id:
                return inviter_id
        return None

    async def inviter_name(self, user_id):
        if not user_id:
            return None
        user = self.bot.get_user(user_id)
        if user is None:
            try:
                user = await self.bot.fetch_user(user_id)
            except discord.HTTPException:
                return None
        return user.name

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            await self.cache_invites(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.cache_invites(guild)

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        if invite.guild:
            self.invites.setdefault(invite.guild.id, {})[invite.code] = (
                invite.uses or 0,
                invite.inviter.id if invite.inviter else 0,
                invite.max_uses or 0,
            )

    # ─── ناردن ───
    def sample_vars(self, guild, member):
        return make_vars(guild, member, member.id, member.name, 5)

    async def deliver(self, guild, kind, member, variables, force=False):
        cfg = load_cfg(guild.id, kind)
        if not force and not cfg["enabled"]:
            return False, None
        channel = guild.get_channel(cfg["channel"]) if cfg["channel"] else None
        if channel is None:
            return False, "no_channel"
        content, embed, file = build_message(guild, member, cfg, variables)
        try:
            await channel.send(
                content=content,
                embed=embed,
                file=file,
                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
            )
        except discord.Forbidden:
            return False, "forbidden"
        except discord.HTTPException as e:
            return False, str(e)
        return True, None

    # ─── ڕووداو ───
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        guild = member.guild

        inviter_id = await self.find_inviter(guild)
        if inviter_id:
            db.execute(
                "INSERT INTO invite_joins (guild_id, inviter_id, member_id, ts) VALUES (?, ?, ?, strftime('%s','now'))",
                (guild.id, inviter_id, member.id),
            )
            db.commit()
        active, _ = invite_stats(guild.id, inviter_id) if inviter_id else (0, 0)
        variables = make_vars(guild, member, inviter_id, await self.inviter_name(inviter_id), active)

        # ڕۆلێ خۆکار (سەربەخۆ ژ چالاکبوونا نامەیێ)
        role_id = load_cfg(guild.id, "welcome").get("role", 0)
        role = guild.get_role(role_id) if role_id else None
        if role:
            try:
                await member.add_roles(role, reason="Welcome auto role")
            except discord.HTTPException:
                print("بۆت نەشێت ڕۆلێ بدەت: ڕۆلێ بۆتی دڤێت بلندتر بیت")

        for kind in ("welcome", "invite"):
            ok, err = await self.deliver(guild, kind, member, variables)
            if err and err != "no_channel":
                print(f"[{kind}] هەلە: {err}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            return
        guild = member.guild
        row = db.execute(
            "SELECT id, inviter_id FROM invite_joins "
            "WHERE guild_id=? AND member_id=? AND has_left=0 ORDER BY id DESC LIMIT 1",
            (guild.id, member.id),
        ).fetchone()
        inviter_id = None
        if row:
            inviter_id = row[1]
            db.execute("UPDATE invite_joins SET has_left=1 WHERE id=?", (row[0],))
            db.commit()
        active, _ = invite_stats(guild.id, inviter_id) if inviter_id else (0, 0)
        variables = make_vars(guild, member, inviter_id, await self.inviter_name(inviter_id), active)
        ok, err = await self.deliver(guild, "leave", member, variables)
        if err and err != "no_channel":
            print(f"[leave] هەلە: {err}")

    # ─── فەرمان ───
    @commands.command(name="setup", aliases=["panel", "ڕێکخستن"])
    @commands.guild_only()
    async def setup_cmd(self, ctx):
        guild = ctx.guild
        if ctx.author.id != guild.owner_id:
            await ctx.send("❌ تەنێ خودانێ سێرڤەری دشێت ڤێ فەرمانێ بکاربینیت.", delete_after=8)
            return

        row = db.execute("SELECT channel_id FROM setup_channels WHERE guild_id=?", (guild.id,)).fetchone()
        channel = guild.get_channel(row[0]) if row else None

        if channel is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True,
                    manage_messages=True,
                ),
                ctx.author: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    attach_files=True,
                    read_message_history=True,
                ),
            }
            try:
                channel = await guild.create_text_channel(
                    "zero-setup",
                    overwrites=overwrites,
                    topic="🔒 تەنێ خودانێ سێرڤەری ڤێ دبینیت ─ ڕێکخستنا Welcome / Invite / Left",
                    reason="Zero Bot setup channel",
                )
            except discord.Forbidden:
                await ctx.send("❌ بۆت مۆڵەتا **Manage Channels** ی نینە.", delete_after=8)
                return
            db.execute(
                "INSERT INTO setup_channels (guild_id, channel_id) VALUES (?, ?) "
                "ON CONFLICT(guild_id) DO UPDATE SET channel_id=excluded.channel_id",
                (guild.id, channel.id),
            )
            db.commit()

        await channel.send(embed=main_embed(guild), view=MainPanelView(self))
        await ctx.send(
            f"✅ ژوورا نهێنی ئامادەیە: {channel.mention}\n"
            "🔒 تەنێ تو و بۆت دبینن. (ئەو کەسێن مۆڵەتا Administrator یێ هەی ژی دشێن ببینن، ڤە ژ سنوورێ Discord یە، بەلێ ناشێن بکاربینن.)",
            delete_after=15,
        )

    @commands.command(name="invites", aliases=["inv", "بانگهێشت"])
    @commands.guild_only()
    async def invites_cmd(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        active, left = invite_stats(ctx.guild.id, member.id)
        embed = make_embed(
            f"🔗 بانگهێشتێن {member.display_name}",
            color=MAIN,
            ctx=ctx,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="✅ ماینە", value=f"`{active}`")
        embed.add_field(name="🚪 دەرکەتین", value=f"`{left}`")
        embed.add_field(name="📊 کۆ", value=f"`{active + left}`")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
