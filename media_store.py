"""
Media Store: گەنجینەی وێنە و GIF ی بوتەکە
فایلەکان لەناو فۆڵدەری media/ ی بوتەکە پارێزراون (نەک لینکی Discord)، بۆیە هەرگیز ناکوژێنەوە.
بەکارهێنان لە هەر cog ێکی تر:

    from media_store import as_discord_file, slot_file

    # بە ناو:
    file, ref = as_discord_file("ناوی-gif")      # file بۆ ctx.send(file=file)، ref بۆ embed.set_image(url=ref)

    # بە شوێن (slot) ــەوە، کە خاوەن بە  z media set  دیاری دەکات:
    found = slot_file("help")                      # (path, filename) یان None
"""
import json
import os
import uuid

BASE = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE, "media")
INDEX_FILE = os.path.join(MEDIA_DIR, "index.json")

ALLOWED_EXT = (".gif", ".png", ".jpg", ".jpeg", ".webp")
MAX_BYTES = 10 * 1024 * 1024   # زۆرترین قەبارە: ١٠ مێگابایت
MAX_NAME = 32

# شوێنەکانی بوتەکە کە دەتوانرێت وێنەیان بۆ دابنرێت. شوێنی نوێ؟ لێرە زیادی بکە
# (و لە کۆدی ئەو بەشەدا slot_file("ناو") بەکاربهێنە)
SLOTS = {
    "help": "وێنە/GIF ی خوارەوەی هەموو لاپەڕەکانی help",
}


def clean_name(name):
    """ناو ڕێکدەخات: بۆشایی زیادە لادەبات، پیتی بچووک. None ئەگەر نادروست بوو"""
    if not name:
        return None
    name = " ".join(str(name).split()).casefold()
    if not name or len(name) > MAX_NAME:
        return None
    return name


def _load():
    try:
        with open(INDEX_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, ValueError):
        data = {}
    data.setdefault("files", {})
    data.setdefault("slots", {})
    return data


def _save(data):
    os.makedirs(MEDIA_DIR, exist_ok=True)
    tmp = INDEX_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, INDEX_FILE)  # نووسینی ئەتۆمی، فایلەکە هەرگیز نیوەچڵ نامێنێت


def add(name, content, ext):
    """
    وێنە/GIF زیاد دەکات. ئەگەر ناوەکە هەبوو، فایلەکەی کۆن دەگۆڕێت.
    دەگەڕێنێتەوە (ناوی ڕێکخراو، replaced)  یان  (None, هۆکار)
    """
    key = clean_name(name)
    if key is None:
        return None, "bad_name"
    ext = (ext or "").lower()
    if ext not in ALLOWED_EXT:
        return None, "bad_type"
    if len(content) > MAX_BYTES:
        return None, "too_big"
    os.makedirs(MEDIA_DIR, exist_ok=True)
    filename = uuid.uuid4().hex[:12] + ext
    with open(os.path.join(MEDIA_DIR, filename), "wb") as f:
        f.write(content)
    data = _load()
    old = data["files"].get(key)
    data["files"][key] = {"file": filename}
    _save(data)
    if old:
        try:
            os.remove(os.path.join(MEDIA_DIR, old["file"]))
        except OSError:
            pass
    return key, bool(old)


def find(name):
    """(path, filename) یان None"""
    key = clean_name(name)
    if key is None:
        return None
    entry = _load()["files"].get(key)
    if not entry:
        return None
    path = os.path.join(MEDIA_DIR, entry["file"])
    return (path, entry["file"]) if os.path.isfile(path) else None


def names():
    """لیستی [(ناو, ناوی فایل, قەبارە بە بایت)]"""
    out = []
    for key, entry in sorted(_load()["files"].items()):
        path = os.path.join(MEDIA_DIR, entry["file"])
        size = os.path.getsize(path) if os.path.isfile(path) else 0
        out.append((key, entry["file"], size))
    return out


def remove(name):
    """دەگەڕێنێتەوە لیستی ئەو شوێنانەی ئەم وێنەیەیان تێدا بوو، یان None ئەگەر نەبوو"""
    key = clean_name(name)
    data = _load()
    entry = data["files"].pop(key, None) if key else None
    if entry is None:
        return None
    freed = [s for s, n in data["slots"].items() if n == key]
    for s in freed:
        del data["slots"][s]
    _save(data)
    try:
        os.remove(os.path.join(MEDIA_DIR, entry["file"]))
    except OSError:
        pass
    return freed


def rename(old, new):
    """"ok" / "missing" / "exists" / "bad_name" """
    a, b = clean_name(old), clean_name(new)
    if b is None:
        return "bad_name"
    data = _load()
    if a not in data["files"]:
        return "missing"
    if b in data["files"]:
        return "exists"
    data["files"][b] = data["files"].pop(a)
    for s, n in data["slots"].items():
        if n == a:
            data["slots"][s] = b
    _save(data)
    return "ok"


# ── شوێنەکانی بوتەکە (slot) ──
def get_slots():
    return dict(_load()["slots"])


def set_slot(slot, name):
    """"ok" / "bad_slot" / "missing" """
    key = clean_name(name)
    if slot not in SLOTS:
        return "bad_slot"
    data = _load()
    if key not in data["files"]:
        return "missing"
    data["slots"][slot] = key
    _save(data)
    return "ok"


def unset_slot(slot):
    data = _load()
    existed = data["slots"].pop(slot, None) is not None
    if existed:
        _save(data)
    return existed


def slot_file(slot):
    """(path, filename) ی وێنەی ئەو شوێنە، یان None ئەگەر دیاری نەکرابوو"""
    name = _load()["slots"].get(slot)
    return find(name) if name else None


def as_discord_file(name):
    """(discord.File, "attachment://..") یان (None, None)"""
    import discord
    found = find(name)
    if not found:
        return None, None
    path, filename = found
    return discord.File(path, filename=filename), f"attachment://{filename}"
