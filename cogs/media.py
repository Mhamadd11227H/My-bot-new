"""
Media: بەڕێوەبردنی وێنە و GIF ی بوتەکە لە Discord ـەوە (تەنها خاوەنی بوت)
فەرمانەکان:  z media add / list / show / rename / remove / set / unset / slots
"""
import os

import discord
from discord.ext import commands

import media_store as M
from utils import make_embed, PREFIX, SUCCESS, ERROR, MAIN

TYPE_TO_EXT = {
    "image/gif": ".gif", "image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp",
}


def _ext(att):
    ext = os.path.splitext(att.filename)[1].lower()
    if ext in M.ALLOWED_EXT:
        return ext
    return TYPE_TO_EXT.get((att.content_type or "").split(";")[0], ext)


def _mb(n):
    return f"{n / 1024 / 1024:.1f}MB" if n >= 1024 * 1024 else f"{max(1, n // 1024)}KB"


class MediaCog(commands.Cog, name="Media"):
    def __init__(self, bot):
        self.bot = bot

    # تەنها خاوەنی بوت. بۆ هەموو کەسێکی تر بێدەنگ دەبێت (bot.py هەڵەی NotOwner پشتگوێ دەخات)
    async def cog_check(self, ctx):
        if not await ctx.bot.is_owner(ctx.author):
            raise commands.NotOwner()
        return True

    async def _find_attachment(self, ctx):
        """وێنەکە لە نامەکەی خۆت یان لەو نامەیەی reply ت لێکردووە دەدۆزێتەوە"""
        if ctx.message.attachments:
            return ctx.message.attachments[0]
        ref = ctx.message.reference
        if ref and ref.message_id:
            msg = ref.resolved if isinstance(ref.resolved, discord.Message) else None
            if msg is None:
                try:
                    msg = await ctx.channel.fetch_message(ref.message_id)
                except discord.HTTPException:
                    msg = None
            if msg and msg.attachments:
                return msg.attachments[0]
        return None

    @commands.group(name="media", aliases=["img", "image", "gif", "pic"], invoke_without_command=True)
    async def media(self, ctx):
        p = PREFIX
        embed = make_embed(
            "🖼️  گەنجینەی وێنە و GIF",
            (
                "> تەنها تۆ دەتوانیت بەکاری بهێنیت\n"
                "───────────────────────────\n"
                f"➕ `{p} media add <ناو>` ── وێنە یان GIF ێک بنێرە لەگەڵ فەرمانەکە (یان reply ی بکە)\n"
                f"📋 `{p} media list` ── لیستی هەموو وێنەکان\n"
                f"👁️ `{p} media show <ناو>` ── وێنەیەک ببینە\n"
                f"✏️ `{p} media rename \"ناوی کۆن\" \"ناوی نوێ\"` ── ناو بگۆڕە\n"
                f"🗑️ `{p} media remove <ناو>` ── بیسڕەوە\n"
                "───────────────────────────\n"
                "**بەکارهێنان لە بەشەکانی بوت**\n"
                f"📌 `{p} media slots` ── بەشەکان کە وێنەیان بۆ دادەنرێت\n"
                f"🔗 `{p} media set <بەش> <ناو>` ── وێنەیەک دابنێ بۆ بەشێک\n"
                f"❎ `{p} media unset <بەش>` ── لایبە"
            ),
            color=MAIN, ctx=ctx,
        )
        await ctx.send(embed=embed)

    @media.command(name="add", aliases=["upload", "save"])
    async def add(self, ctx, *, name: str = None):
        if not name:
            return await ctx.send(f"❌ ناوێک بنووسە. نموونە: `{PREFIX} media add zero-neon` و وێنەکە لەگەڵی بنێرە")
        att = await self._find_attachment(ctx)
        if att is None:
            return await ctx.send("❌ هیچ وێنەیەک نەدۆزرایەوە. وێنە یان GIF ێک لەگەڵ فەرمانەکە بنێرە، یان reply ی نامەیەک بکە کە وێنەی تێدایە")
        if att.size > M.MAX_BYTES:
            return await ctx.send(f"❌ وێنەکە زۆر گەورەیە (**{_mb(att.size)}**). زۆرترین: **{_mb(M.MAX_BYTES)}**")
        ext = _ext(att)
        if ext not in M.ALLOWED_EXT:
            return await ctx.send("❌ تەنها `gif` `png` `jpg` `webp` قبوڵ دەکرێن")
        try:
            content = await att.read()
        except discord.HTTPException:
            return await ctx.send("❌ نەتوانرا وێنەکە دابەزێنرێت، دووبارە هەوڵ بدەرەوە")
        key, replaced = M.add(name, content, ext)
        if key is None:
            reason = {"bad_name": f"ناوەکە دەبێت لە ١ تا {M.MAX_NAME} پیت بێت", "bad_type": "جۆری فایل نادروستە",
                      "too_big": "وێنەکە زۆر گەورەیە"}.get(replaced, "هەڵەیەک ڕوویدا")
            return await ctx.send(f"❌ {reason}")
        file, ref = M.as_discord_file(key)
        embed = make_embed(
            "✅  وێنەکە پارێزرا" if not replaced else "♻️  وێنەکە گۆڕدرا",
            f"**ناو:** `{key}`\n**قەبارە:** `{_mb(len(content))}`\n"
            f"بۆ بەکارهێنان: `{PREFIX} media set <بەش> {key}`",
            color=SUCCESS, ctx=ctx,
        )
        embed.set_image(url=ref)
        await ctx.send(embed=embed, file=file)

    @media.command(name="list", aliases=["ls", "all"])
    async def list_(self, ctx):
        items = M.names()
        if not items:
            return await ctx.send(f"📭 هیچ وێنەیەک نییە. بە `{PREFIX} media add <ناو>` زیادی بکە")
        slots = M.get_slots()
        used = {}
        for s, n in slots.items():
            used.setdefault(n, []).append(s)
        lines = []
        for key, filename, size in items:
            kind = os.path.splitext(filename)[1][1:].upper()
            tag = f" ── 📌 {', '.join(used[key])}" if key in used else ""
            lines.append(f"▫️ **{key}** ── `{kind}` · `{_mb(size)}`{tag}")
        text = "\n".join(lines)
        if len(text) > 3900:
            text = text[:3900] + "\n…"
        await ctx.send(embed=make_embed(f"🖼️  وێنەکان ({len(items)})", text, color=MAIN, ctx=ctx))

    @media.command(name="show", aliases=["view", "preview"])
    async def show(self, ctx, *, name: str = None):
        file, ref = M.as_discord_file(name)
        if file is None:
            return await ctx.send(f"❌ وێنەیەک بەم ناوە نییە. `{PREFIX} media list` ببینە")
        embed = make_embed(f"🖼️  {M.clean_name(name)}", color=MAIN, ctx=ctx)
        embed.set_image(url=ref)
        await ctx.send(embed=embed, file=file)

    @media.command(name="rename", aliases=["mv"])
    async def rename(self, ctx, old: str = None, new: str = None):
        if not old or not new:
            return await ctx.send(f"❌ نموونە: `{PREFIX} media rename \"ناوی کۆن\" \"ناوی نوێ\"`")
        res = M.rename(old, new)
        msg = {
            "ok": f"✅ ناوەکە گۆڕدرا: **{M.clean_name(old)}** ← **{M.clean_name(new)}**",
            "missing": "❌ وێنەیەک بەم ناوە نییە",
            "exists": "❌ ناوی نوێ پێشتر بەکارهێنراوە",
            "bad_name": f"❌ ناوەکە دەبێت لە ١ تا {M.MAX_NAME} پیت بێت",
        }[res]
        await ctx.send(msg)

    @media.command(name="remove", aliases=["delete", "del", "rm"])
    async def remove(self, ctx, *, name: str = None):
        freed = M.remove(name)
        if freed is None:
            return await ctx.send("❌ وێنەیەک بەم ناوە نییە")
        extra = f"\n⚠️ لەم بەشانە لابرا: {', '.join(f'`{s}`' for s in freed)}" if freed else ""
        await ctx.send(f"🗑️ **{M.clean_name(name)}** سڕدرایەوە{extra}")

    @media.command(name="slots", aliases=["places", "parts"])
    async def slots(self, ctx):
        cur = M.get_slots()
        lines = [
            f"📌 `{s}` ── {desc}\n　　┕ {('**' + cur[s] + '**') if s in cur else '*دیاری نەکراوە*'}"
            for s, desc in M.SLOTS.items()
        ]
        await ctx.send(embed=make_embed("📌  بەشەکانی بوت", "\n".join(lines), color=MAIN, ctx=ctx))

    @media.command(name="set", aliases=["use", "assign"])
    async def set_(self, ctx, slot: str = None, *, name: str = None):
        if not slot or not name:
            return await ctx.send(f"❌ نموونە: `{PREFIX} media set help zero-neon`. بەشەکان: `{PREFIX} media slots`")
        res = M.set_slot(slot.lower(), name)
        if res == "bad_slot":
            return await ctx.send(f"❌ ئەم بەشە نییە. بەشەکان: {', '.join(f'`{s}`' for s in M.SLOTS)}")
        if res == "missing":
            return await ctx.send(f"❌ وێنەیەک بەم ناوە نییە. `{PREFIX} media list` ببینە")
        await ctx.send(f"✅ **{M.clean_name(name)}** بوو بە وێنەی بەشی `{slot.lower()}`")

    @media.command(name="unset", aliases=["clear"])
    async def unset(self, ctx, slot: str = None):
        if not slot:
            return await ctx.send(f"❌ نموونە: `{PREFIX} media unset help`")
        ok = M.unset_slot(slot.lower())
        await ctx.send(f"✅ وێنەی بەشی `{slot.lower()}` لابرا" if ok else "❌ ئەم بەشە وێنەی دیاریکراوی نەبوو")


async def setup(bot):
    await bot.add_cog(MediaCog(bot))
