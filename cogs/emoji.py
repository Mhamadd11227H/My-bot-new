"""
Emoji: گۆڕینی ئیمۆجییەکانی بوت بە وێنە و GIF (تەنها خاوەنی بوت)
نموونە:  z emoji set 🐾   (وێنەیەک لەگەڵی بنێرە)
"""
import asyncio
import io
import re
import uuid

import aiohttp
import discord
from discord.ext import commands

import emoji_swap as ES
import media_store as M
from utils import make_embed, PREFIX, MAIN, SUCCESS

TAG_RE = re.compile(r"<a?:\w+:\d+>")
EMOJI_MAX_BYTES = 256 * 1024   # سنووری Discord بۆ هەر ئیمۆجییەک
TYPE_TO_EXT = {"image/gif": ".gif", "image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


def _looks_like_emoji(s):
    return bool(s) and len(s) <= 64 and (TAG_RE.fullmatch(s) is not None or not s.isascii())


def _show(key):
    """ئیمۆجییەکە بێ ئەوەی بگۆڕدرێت پیشان دەدات (بۆ لیست)"""
    return key + ES.BYPASS


def _shrink_sync(data, ext):
    """وێنە بچووک دەکاتەوە ئەگەر لە ٢٥٦KB زیاتر بوو (پێویستی بە Pillow هەیە). None ئەگەر نەکرا"""
    try:
        from PIL import Image, ImageSequence
    except ImportError:
        return None
    try:
        for size in (128, 96, 64):
            im = Image.open(io.BytesIO(data))
            out = io.BytesIO()
            if getattr(im, "is_animated", False):
                frames, durations = [], []
                for fr in ImageSequence.Iterator(im):
                    f = fr.convert("RGBA")
                    f.thumbnail((size, size))
                    frames.append(f)
                    durations.append(fr.info.get("duration", 50))
                frames[0].save(out, format="GIF", save_all=True, append_images=frames[1:],
                               duration=durations, loop=0, disposal=2, optimize=True)
            else:
                f = im.convert("RGBA")
                f.thumbnail((size, size))
                f.save(out, format="PNG", optimize=True)
            if out.tell() <= EMOJI_MAX_BYTES:
                return out.getvalue()
    except Exception:
        return None
    return None


class EmojiCog(commands.Cog, name="Emoji"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        ES.install()

    async def cog_check(self, ctx):
        if not await ctx.bot.is_owner(ctx.author):
            raise commands.NotOwner()
        return True

    # ── وێنەکە لە کوێ دەدۆزرێتەوە ──
    async def _source_bytes(self, ctx, source):
        """دەگەڕێنێتەوە (bytes, ext) یان ("tag", tag) بۆ ئیمۆجی ی ئامادە، یان (None, هەڵە)"""
        # ١. وێنە/GIF ی لکێنراو، لە نامەکەی خۆت یان لەو نامەیەی reply ت لێکردووە
        msgs = [ctx.message]
        ref = ctx.message.reference
        if ref and ref.message_id:
            m = ref.resolved if isinstance(ref.resolved, discord.Message) else None
            if m is None:
                try:
                    m = await ctx.channel.fetch_message(ref.message_id)
                except discord.HTTPException:
                    m = None
            if m:
                msgs.append(m)
        for m in msgs:
            if m.attachments:
                att = m.attachments[0]
                import os
                ext = os.path.splitext(att.filename)[1].lower() or TYPE_TO_EXT.get((att.content_type or "").split(";")[0], "")
                if ext not in M.ALLOWED_EXT:
                    return None, "تەنها gif png jpg webp قبوڵ دەکرێن"
                return await att.read(), ext
            if m.stickers:
                st = m.stickers[0]
                if st.format == discord.StickerFormatType.lottie:
                    return None, "ئەم sticker ـە جۆری Lottie ـە و ناتوانرێت ببێت بە ئیمۆجی"
                ext = ".gif" if st.format == discord.StickerFormatType.gif else ".png"
                async with aiohttp.ClientSession() as s:
                    async with s.get(st.url) as r:
                        if r.status != 200:
                            return None, "نەتوانرا sticker ـەکە دابەزێنرێت"
                        return await r.read(), ext
        # ٢. ئیمۆجی ی custom ی ئامادە (لە سێرڤەرێک کە بوت تێیدایە)
        if source:
            tag = TAG_RE.search(source)
            if tag:
                return "tag", tag.group(0)
            # ٣. ناوی وێنەیەک لە z media
            found = M.find(source)
            if found:
                path, filename = found
                with open(path, "rb") as f:
                    return f.read(), "." + filename.rsplit(".", 1)[-1]
            return None, f"هیچ وێنەیەک بەم ناوە نییە: `{source}`"
        return None, "وێنەیەک نەدۆزرایەوە"

    async def _create_emoji(self, ctx, data):
        name = "ze_" + uuid.uuid4().hex[:8]
        if hasattr(self.bot, "create_application_emoji"):
            e = await self.bot.create_application_emoji(name=name, image=data)
            return e, "app"
        if ctx.guild is None:
            raise commands.CommandError("ئەم وەشانەی discord.py ناتوانێت ئیمۆجی ی بوت دروست بکات. لەناو سێرڤەردا بنووسە یان `pip install -U discord.py`")
        e = await ctx.guild.create_custom_emoji(name=name, image=data)
        return e, f"guild:{ctx.guild.id}"

    async def _delete_created(self, entry):
        """ئیمۆجی ی کۆنی دروستکراوی بوت دەسڕێتەوە بۆ ئەوەی شوێن نەگیرێت"""
        try:
            created, eid = entry.get("created"), entry.get("id")
            if not created or not eid:
                return
            if created == "app" and hasattr(self.bot, "fetch_application_emoji"):
                e = await self.bot.fetch_application_emoji(int(eid))
                await e.delete()
            elif created.startswith("guild:"):
                g = self.bot.get_guild(int(created.split(":")[1]))
                if g:
                    e = await g.fetch_emoji(int(eid))
                    await e.delete()
        except Exception:
            pass

    @commands.group(name="emoji", aliases=["emojis"], invoke_without_command=True)
    async def emoji(self, ctx):
        p = PREFIX
        await ctx.send(embed=make_embed(
            "🎨  گۆڕینی ئیمۆجییەکان",
            (
                "> هەر ئیمۆجییەک بە وێنە یان GIF ی خۆت بگۆڕە، لە **هەموو** شوێنێکی بوتەکەدا\n"
                "───────────────────────────\n"
                f"🔄 `{p} emoji set 🐾` + وێنە/GIF ی لکێنراو\n"
                f"🔄 `{p} emoji set 🐾` + reply ی نامەیەک کە وێنە یان sticker ی تێدایە\n"
                f"🔄 `{p} emoji set 🐾 <ناوی وێنە>` ── وێنەیەک لە `{p} media`\n"
                f"🔄 `{p} emoji set 🐾 <ئیمۆجی ی custom>` ── ئیمۆجییەکی ئامادە\n"
                f"📋 `{p} emoji list` ── هەموو گۆڕانکارییەکان\n"
                f"♻️ `{p} emoji reset 🐾` ── بیگەڕێنەرەوە بۆ ئیمۆجی ی ڕەسەن"
            ),
            color=MAIN, ctx=ctx,
        ))

    @emoji.command(name="set", aliases=["change", "replace"])
    async def set_(self, ctx, old: str = None, *, source: str = None):
        if not old or not _looks_like_emoji(old):
            return await ctx.send(f"❌ یەکەمجار ئیمۆجییەک بنووسە کە دەتەوێت بیگۆڕیت. نموونە: `{PREFIX} emoji set 🐾` و وێنەکە لەگەڵی بنێرە")
        data, ext = await self._source_bytes(ctx, source)
        if data is None:
            return await ctx.send(f"❌ {ext}\nوێنە یان GIF ێک لەگەڵ فەرمانەکە بنێرە، یان reply ی نامەیەک بکە کە وێنەی تێدایە")

        prev = ES.get(old)
        if data == "tag":                      # ئیمۆجی ی ئامادە، تەنها بەستنەوە
            m = re.fullmatch(r"<a?:\w+:(\d+)>", ext)
            ES.set_mapping(old, ext, emoji_id=m.group(1), created=None)
            if prev:
                await self._delete_created(prev)
            return await ctx.send(f"✅ {_show(old)} ← {ext}")

        if len(data) > EMOJI_MAX_BYTES:
            small = await asyncio.get_running_loop().run_in_executor(None, _shrink_sync, data, ext)
            if small is None:
                return await ctx.send(
                    f"❌ وێنەکە زۆر گەورەیە (**{len(data) // 1024}KB**) و Discord تەنها **٢٥٦KB** قبوڵ دەکات.\n"
                    "وێنەیەکی بچووکتر بەکاربهێنە، یان `pip install pillow` بکە بۆ ئەوەی بوت خۆی بچووکی بکاتەوە")
            data = small
        try:
            new, where = await self._create_emoji(ctx, data)
        except commands.CommandError as e:
            return await ctx.send(f"❌ {e}")
        except discord.HTTPException as e:
            return await ctx.send(f"❌ Discord ڕەتی کردەوە: `{e.text or e}`")
        ES.set_mapping(old, str(new), emoji_id=str(new.id), created=where)
        if prev:
            await self._delete_created(prev)
        await ctx.send(f"✅ {_show(old)} ← {new}\nئێستا لە هەموو شوێنێکی بوتەکەدا بەم شێوەیە دەردەکەوێت")

    @emoji.command(name="list", aliases=["ls", "all"])
    async def list_(self, ctx):
        items = ES.get_all()
        if not items:
            return await ctx.send(f"📭 هیچ ئیمۆجییەک نەگۆڕدراوە. بە `{PREFIX} emoji set 🐾` دەستپێبکە")
        text = "\n".join(f"{_show(k)} ➜ {v['tag']}" for k, v in items.items())
        if len(text) > 3900:
            text = text[:3900] + "\n…"
        await ctx.send(embed=make_embed(f"🎨  گۆڕانکارییەکان ({len(items)})", text, color=MAIN, ctx=ctx))

    @emoji.command(name="reset", aliases=["remove", "delete", "rm"])
    async def reset(self, ctx, old: str = None):
        if not old:
            return await ctx.send(f"❌ نموونە: `{PREFIX} emoji reset 🐾`")
        entry = ES.remove_mapping(old)
        if entry is None:
            return await ctx.send("❌ ئەم ئیمۆجییە نەگۆڕدرابوو")
        await self._delete_created(entry)
        await ctx.send(f"♻️ {_show(old)} گەڕایەوە بۆ ڕەسەن")


async def setup(bot):
    await bot.add_cog(EmojiCog(bot))
