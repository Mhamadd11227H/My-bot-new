"""
Emoji Swap: گۆڕینی هەموو ئیمۆجییەکانی بوت بە وێنە یان GIF ی خۆت
هەر ئیمۆجییەک (وەک 🐾 یان 💰) بە یەک فەرمان لە هەموو شوێنێکی بوتەکەدا دەگۆڕدرێت،
بێ ئەوەی کۆدی هیچ فایلێک دەستکاری بکەیت. خاوەن بە  z emoji set  بەڕێوەی دەبات.

چۆن کار دەکات: هەموو نامە، embed و دوگمەیەک کە بوت دەینێرێت، پێش ناردن دەپشکنرێت
و ئیمۆجییە دیاریکراوەکان دەگۆڕدرێن بە custom emoji ی Discord (وێنەی ئاسایی یان GIF).
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
MAP_FILE = os.path.join(BASE, "emoji_map.json")

FE0F = "\ufe0f"      # نیشانەی شێوازی ئیمۆجی (⚙️ = ⚙ + FE0F)
BYPASS = "\u2063"    # نیشانەی نەگۆڕین: ئیمۆجییەک کە ئەمەی دوای بێت ناگۆڕدرێت (بۆ z emoji list)

_map = {}            # ئیمۆجی ی ڕێکخراو -> {"tag": "<a:ناو:ئایدی>", "id": ..., "created": ...}
_regex = None


def norm(s):
    return s.replace(FE0F, "")


def _rebuild():
    global _regex
    parts = []
    for key in sorted(_map, key=len, reverse=True):
        if key.startswith("<"):
            parts.append(re.escape(key))
        else:
            parts.append("".join(re.escape(ch) + FE0F + "?" for ch in key))
    _regex = re.compile("(?:" + "|".join(parts) + ")(?!" + BYPASS + ")") if parts else None


def load():
    global _map
    try:
        with open(MAP_FILE, encoding="utf-8") as f:
            data = json.load(f)
        _map = {norm(k): v for k, v in data.items() if isinstance(v, dict) and v.get("tag")}
    except (FileNotFoundError, ValueError):
        _map = {}
    _rebuild()


def _save():
    tmp = MAP_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_map, f, ensure_ascii=False, indent=2)
    os.replace(tmp, MAP_FILE)
    _rebuild()


def get_all():
    return dict(_map)


def get(key):
    return _map.get(norm(key))


def set_mapping(key, tag, emoji_id=None, created=None):
    """created: "app" / "guild:<ئایدی>" ئەگەر بوت خۆی دروستی کرد (بۆ سڕینەوەی دواتر)، وگرنە None"""
    old = _map.get(norm(key))
    _map[norm(key)] = {"tag": tag, "id": emoji_id, "created": created}
    _save()
    return old


def remove_mapping(key):
    old = _map.pop(norm(key), None)
    if old is not None:
        _save()
    return old


# ═══════════════════════════════════════
# گۆڕینی دەق و embed
# ═══════════════════════════════════════
def swap(text, limit=None):
    """ئیمۆجییەکان لە دەقدا دەگۆڕێت. ئەگەر دەرەنجامەکە لە limit درێژتر بوو، دەقی ڕەسەن دەگەڕێنێتەوە"""
    if not text or not isinstance(text, str):
        return text
    clean = text.replace(BYPASS, "")
    if _regex is None:
        return clean
    out = _regex.sub(lambda m: _map[norm(m.group(0))]["tag"], text).replace(BYPASS, "")
    if limit and len(out) > limit:
        return clean
    return out


def swap_embed(e):
    """سەردێڕ، وەسف و خانەکانی embed دەگۆڕێت (footer و author نا، چونکە Discord لەوێ custom emoji پیشان نادات)"""
    try:
        if e.title:
            e.title = swap(e.title, 256)
        if e.description:
            e.description = swap(e.description, 4096)
        for f in getattr(e, "_fields", None) or []:
            f["name"] = swap(f.get("name"), 256)
            f["value"] = swap(f.get("value"), 1024)
    except Exception:
        pass
    return e


def swap_component_emoji(emoji):
    """ئیمۆجی ی دوگمە و لیست (select) دەگۆڕێت"""
    if isinstance(emoji, str):
        ent = _map.get(norm(emoji))
        if ent:
            return ent["tag"]
    return emoji


# ═══════════════════════════════════════
# دامەزراندن: discord.py دەستکاری دەکات بۆ ئەوەی هەموو نامەکان بپشکنرێن
# ═══════════════════════════════════════
_installed = False


def install():
    global _installed
    if _installed:
        return True
    import discord
    load()

    def wrap_send(cls, name):
        orig = getattr(cls, name, None)
        if orig is None:
            return
        async def wrapper(self, *args, **kw):
            try:
                if args and isinstance(args[0], str):
                    args = (swap(args[0], 2000),) + tuple(args[1:])
                if isinstance(kw.get("content"), str):
                    kw["content"] = swap(kw["content"], 2000)
                if isinstance(kw.get("embed"), discord.Embed):
                    swap_embed(kw["embed"])
                for em in kw.get("embeds") or ():
                    if isinstance(em, discord.Embed):
                        swap_embed(em)
            except Exception:
                pass
            return await orig(self, *args, **kw)
        wrapper.__name__ = getattr(orig, "__name__", name)
        wrapper.__doc__ = getattr(orig, "__doc__", None)
        setattr(cls, name, wrapper)

    for cls_name, meth in (
        ("abc.Messageable", "send"),
        ("Message", "edit"),
        ("InteractionResponse", "send_message"),
        ("InteractionResponse", "edit_message"),
        ("Interaction", "edit_original_response"),
        ("Webhook", "send"),
        ("WebhookMessage", "edit"),
        ("InteractionMessage", "edit"),
    ):
        try:
            cls = discord
            for part in cls_name.split("."):
                cls = getattr(cls, part)
            wrap_send(cls, meth)
        except Exception as e:
            print(f"emoji_swap: نەتوانرا {cls_name}.{meth} بپارێزرێت ({e})")

    # ئیمۆجی ی دوگمە و لیستی هەڵبژاردن
    def wrap_init(cls):
        orig = cls.__init__
        def init(self, *args, **kw):
            if "emoji" in kw:
                kw["emoji"] = swap_component_emoji(kw["emoji"])
            orig(self, *args, **kw)
        cls.__init__ = init

    for cls in (discord.SelectOption, discord.ui.Button):
        try:
            wrap_init(cls)
        except Exception as e:
            print(f"emoji_swap: نەتوانرا {cls.__name__} بپارێزرێت ({e})")

    # reaction ەکان
    try:
        orig_react = discord.Message.add_reaction
        async def add_reaction(self, emoji):
            return await orig_react(self, swap_component_emoji(emoji))
        discord.Message.add_reaction = add_reaction
    except Exception:
        pass

    _installed = True
    return True
