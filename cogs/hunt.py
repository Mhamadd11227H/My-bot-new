"""
ZERO HUNT — بەشی Discord (فەرمان، embed، دوگمە). لۆجیک لە hunt_core.py ـە و داتا لە hunt_data.py.
"""
import asyncio
import math
import time

import discord
from discord.ext import commands, tasks

from database import get_user
from utils import make_embed, BOT_NAME, PREFIX, CURRENCY, CASH_EMOJI, MAIN, SUCCESS, ERROR, WARN
from . import hunt_core as C
from . import hunt_data as D

LINE = "━━━━━━━━━━━━━━━━━━━━"
GOLD = 0xFFC700


def esc(text):
    return discord.utils.escape_markdown(discord.utils.escape_mentions(str(text)))


def rar(a):
    return D.RARITIES[a["rarity"]]


def fmt_counts(counts, limit=25):
    items = sorted(counts.items(), key=lambda kv: (-D.RARITY_RANK[D.ANIMALS[kv[0]]["rarity"]], D.ANIMALS[kv[0]]["name"]))
    text = " ".join(f"{D.ANIMALS[a]['emoji']}×{n}" for a, n in items[:limit])
    if len(items) > limit:
        text += f" … +{len(items) - limit}"
    return text or "—"


def fmt_dur(seconds):
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def pet_name(animal, nickname):
    return f"{animal['emoji']} {esc(nickname) if nickname else animal['name']}"


def level_up_lines(ups):
    out = []
    for aid, lvl, reward in ups:
        a = D.ANIMALS[aid]
        out.append(f"⬆️ **{a['name']}** reached level **{lvl}**! (+{reward:,} {CURRENCY})")
    return out


def split_animal_rest(tokens):
    """['shadow','cat','Hello','there'] -> (Shadow Cat, 'Hello there'). درێژترین ناوی ئاژەڵ یەکەم دەپشکنرێت"""
    for i in range(len(tokens), 0, -1):
        a = C.find_animal(" ".join(tokens[:i]))
        if a:
            return a, " ".join(tokens[i:])
    return None, ""


# ═══════════════════════════════════════
# Embed ی hunt
# ═══════════════════════════════════════
def reset_in():
    """ماوەی ماوە تا ڕەستکردنەوەی ڕۆژانە (٠٠:٠٠ UTC)، بەشێوەی 7H 21M 46S"""
    left = int(86400 - (time.time() % 86400))
    hh, rem = divmod(left, 3600)
    mm, ss = divmod(rem, 60)
    return f"{hh}H {mm}M {ss}S"


def hunt_message(ctx, r):
    """نامەی hunt بە شێوازی OwO: کورت، ڕێک، و بێ embed"""
    uid = ctx.author.id
    name = esc(ctx.author.display_name)
    pad = "\u3000\u3000| "
    animals = sorted(r["animals"], key=lambda a: (D.RARITY_RANK[a["rarity"]], a["name"]))
    found = " ".join(a["emoji"] for a in animals)

    g = r["gem"]
    lines = []
    if g:
        lines.append(f"🌱 | **{name}**, hunt is empowered by {g['emoji']} `[{g['left']}/{g['max']}]` !")
        lines.append(f"{pad}You found: {found}")
    else:
        lines.append(f"🌱 | **{name}**, you found: {found}")

    # ئاژەڵی نوێ و کاریگەری rarity ی بەرزترین ئاژەڵ
    new_names = [f"{a['emoji']} {a['name']}" for a in animals if a["id"] in r["new"]]
    if new_names:
        lines.append(f"{pad}🆕 New: {', '.join(dict.fromkeys(new_names))}")
    effect = rar(animals[-1])["effect"]
    if effect:
        lines.append(f"{pad}**{effect}**")

    # XP ی team
    team = C.get_team(uid)
    if team and r["team_xp"] > 0:
        lines.append(f"{pad}{' '.join(t['animal']['emoji'] for t in team)} gained **{r['team_xp']:,}xp**!")
    lines += [f"{pad}{x}" for x in level_up_lines(r["level_ups"])]

    # gem شکا
    if g and g["expired"]:
        lines.append(f"💨 | Your {g['emoji']} **{g['name']}** has broken!")

    # event ە چالاکەکان
    if r["events"]:
        lines.append(f"{pad}" + " ".join(f"{D.EVENTS[k]['emoji']} **{D.EVENTS[k]['name']}**" for k in r["events"]))

    # lootbox: تەنها کاتێک دەرچوو
    if r["box"]:
        today = min(r["box"][0], D.DAILY_BOX_TARGET)
        lines.append(f"📦 | You found a **lootbox**! `[{today}/{D.DAILY_BOX_TARGET}]` RESETS IN: `{reset_in()}`")
        if r["box"][1]:
            lines.append(f"🏅 | Daily checklist complete! **+{r['box'][1]:,} {CURRENCY}**")
    return "\n".join(lines)


def hunt_embed(ctx, r):
    animals = r["animals"]
    top = max(animals, key=lambda a: D.RARITY_RANK[a["rarity"]])
    rd = rar(top)
    lines = [LINE, "🐾 **ZERO HUNTING**", LINE, ""]
    if len(animals) == 1:
        a = animals[0]
        tag = "  🆕" if a["id"] in r["new"] else ""
        lines += [
            "A wild animal appeared!", "",
            f"{a['emoji']} **{a['name'].upper()}**{tag}", "",
            f"Rarity: **{rd['emoji']} {rd['name'].upper()}**",
            f"XP Reward: **{a['xp']:,}**",
            f"Sell Value: **{a['sell']:,} {CURRENCY}**",
            f"Essence: **{a['essence']:,}**",
        ]
    else:
        lines.append(f"A wild pack appeared! (**{len(animals)}** animals)\n")
        for aid, n in sorted(r["counts"].items(), key=lambda kv: -D.RARITY_RANK[D.ANIMALS[kv[0]]["rarity"]]):
            a = D.ANIMALS[aid]
            tag = " 🆕" if aid in r["new"] else ""
            lines.append(f"{rar(a)['emoji']} {a['emoji']} **{a['name']}** ×{n}{tag}")
    if rd["effect"]:
        lines += ["", f"**{rd['effect']}**"]
    lines += ["", LINE, f"💰 Hunt Cost: **{r['cost']:,} {CURRENCY}**", f"✨ Team XP: **+{r['team_xp']:,}**"]
    if r["box"]:
        lines.append(f"🎁 **You found a Lootbox!** (`{PREFIX} lootbox open`)")
        if r["box"][1]:
            lines.append(f"🏅 Daily checklist complete! **+{r['box'][1]:,} {CURRENCY}**")
    lines.append(f"📦 Lootbox Progress: **{min(r['boxes_today'], D.DAILY_BOX_TARGET)}/{D.DAILY_BOX_TARGET}** today "
                 f"• next in **{D.LOOTBOX_EVERY - r['since']}** hunts")
    g = r["gem"]
    if g:
        if g["expired"]:
            lines.append(f"💨 Your {g['emoji']} **{g['name']}** has broken!")
        else:
            lines.append(f"{g['emoji']} {g['name']}: **{g['left']}** hunts left")
    for key in r["events"]:
        ev = D.EVENTS[key]
        lines.append(f"{ev['emoji']} **{ev['name']}** is active!")
    lines.append(LINE)
    lines += level_up_lines(r["level_ups"])
    embed = make_embed(None, "\n".join(lines), color=rd["color"], ctx=ctx)
    if len(animals) == 1 and top["image"]:
        embed.set_thumbnail(url=top["image"])
    return embed


# ═══════════════════════════════════════
# دوگمە: دڵنیابوونەوە
# ═══════════════════════════════════════
class ConfirmView(discord.ui.View):
    """action() دەبێت sync بێت و str یان discord.Embed بگەڕێنێتەوە"""
    def __init__(self, uid, action, timeout=30):
        super().__init__(timeout=timeout)
        self.uid, self.action, self.done, self.message = uid, action, False, None

    async def interaction_check(self, interaction):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ This button is not for you.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", emoji="✅", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.done:
            return
        self.done = True
        self.stop()
        try:
            result = self.action()
        except Exception as e:  # هەڵە = ڕۆڵبەک، هیچ شتێک نەگۆڕاوە
            print(f"ConfirmView هەڵە: {e}")
            result = "⚠️ Something changed, nothing was done. Try again."
        if isinstance(result, discord.Embed):
            await interaction.response.edit_message(content=None, embed=result, view=None)
        else:
            await interaction.response.edit_message(content=result, embed=None, view=None)

    @discord.ui.button(label="Cancel", emoji="✖️", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.done:
            return
        self.done = True
        self.stop()
        await interaction.response.edit_message(content="❌ Cancelled.", embed=None, view=None)

    async def on_timeout(self):
        if self.done or not self.message:
            return
        self.done = True
        try:
            await self.message.edit(content="⏱️ Timed out, cancelled.", view=None)
        except discord.HTTPException:
            pass


# ═══════════════════════════════════════
# Zoo (پەڕەپەڕە)
# ═══════════════════════════════════════
class FilterSelect(discord.ui.Select):
    def __init__(self, parent):
        self.parent = parent
        opts = [discord.SelectOption(label="All rarities", value="all", emoji="🐾")]
        for key, r in D.RARITIES.items():
            opts.append(discord.SelectOption(label=r["name"], value=key, emoji=r["emoji"]))
        super().__init__(placeholder="Filter by rarity…", options=opts)

    async def callback(self, interaction: discord.Interaction):
        v = self.values[0]
        self.parent.rarity = None if v == "all" else v
        self.parent.page = 0
        await interaction.response.edit_message(content="✅ Filter applied.", view=None)
        if self.parent.message:
            await self.parent.message.edit(embed=self.parent.embed(), view=self.parent)


class FilterView(discord.ui.View):
    def __init__(self, parent):
        super().__init__(timeout=60)
        self.add_item(FilterSelect(parent))


class ZooSearchModal(discord.ui.Modal, title="🔎 Search your zoo"):
    query = discord.ui.TextInput(label="Animal name", required=False, max_length=30, placeholder="wolf")

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    async def on_submit(self, interaction: discord.Interaction):
        self.parent.search = self.query.value.strip() or None
        self.parent.page = 0
        await interaction.response.edit_message(embed=self.parent.embed(), view=self.parent)


class ZooView(discord.ui.View):
    def __init__(self, ctx, rarity=None, search=None):
        super().__init__(timeout=180)
        self.ctx, self.uid = ctx, ctx.author.id
        self.rarity, self.search, self.page, self.message = rarity, search, 0, None
        self._sync()

    def _rows(self):
        return C.zoo_rows(self.uid, self.rarity, self.search)

    def _pages(self):
        return max(1, math.ceil(len(self._rows()) / D.PAGE_SIZE))

    def _sync(self):
        pages = self._pages()
        self.page = max(0, min(self.page, pages - 1))
        self.prev.disabled = self.page <= 0
        self.next.disabled = self.page >= pages - 1

    def embed(self):
        self._sync()
        rows, s = self._rows(), C.zoo_summary(self.uid)
        pages = self._pages()
        pct = s["discovered"] / s["species"] * 100 if s["species"] else 0
        breakdown = " ".join(f"{D.RARITIES[r]['emoji']} {n:,}" for r, n in
                             sorted(s["by_rarity"].items(), key=lambda kv: D.RARITY_RANK[kv[0]]))
        title = f"🐾 {esc(self.ctx.author.display_name)}'s Zoo"
        if self.rarity:
            title += f" • {D.RARITIES[self.rarity]['name']}"
        if self.search:
            title += f" • 🔎 {esc(self.search)}"
        head = (f"🐾 **{s['total']:,}** animals • 📖 **{s['discovered']}/{s['species']}** species (**{pct:.1f}%**)\n"
                f"🏆 Zoo Points: **{s['points']:,}**\n{breakdown or '*No animals yet.*'}")
        chunk = rows[self.page * D.PAGE_SIZE:(self.page + 1) * D.PAGE_SIZE]
        body = "\n".join(f"{rar(a)['emoji']} {a['emoji']} **{a['name']}** ×{q:,}{' 🔒' if l else ''}"
                         for a, q, l in chunk) or "*Nothing here. Use* `" + PREFIX + " hunt`"
        embed = make_embed(title, f"{head}\n\n{body}", color=GOLD, ctx=self.ctx)
        if self.page == 0 and not self.rarity and not self.search:
            if s["recent"]:
                embed.add_field(name="🕒 Recently caught", value=" ".join(a["emoji"] for a in s["recent"]), inline=True)
            if s["favorites"]:
                embed.add_field(name="⭐ Favorites", value=" ".join(a["emoji"] for a in s["favorites"][:20]), inline=True)
        embed.set_footer(text=f"Page {self.page + 1}/{pages} • {BOT_NAME}", icon_url=self.ctx.author.display_avatar.url)
        return embed

    async def interaction_check(self, interaction):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ This is not your zoo.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Previous", emoji="◀️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="Next", emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label="Filter", emoji="🎚️", style=discord.ButtonStyle.primary)
    async def filter(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Choose a rarity:", view=FilterView(self), ephemeral=True)

    @discord.ui.button(label="Search", emoji="🔎", style=discord.ButtonStyle.primary)
    async def search_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ZooSearchModal(self))

    @discord.ui.button(label="Close", emoji="✖️", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        try:
            await interaction.message.delete()
        except discord.HTTPException:
            await interaction.response.edit_message(view=None)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


# ═══════════════════════════════════════
# Leaderboard
# ═══════════════════════════════════════
class LbSelect(discord.ui.Select):
    def __init__(self, bot, current):
        self.bot = bot
        opts = [discord.SelectOption(label=t.split(" ", 1)[1], value=k, emoji=t.split(" ", 1)[0], default=(k == current))
                for k, (t, _) in C.LEADERBOARDS.items()]
        super().__init__(placeholder="Choose a leaderboard…", options=opts)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=lb_embed(self.bot, self.values[0]),
                                                view=LbView(self.bot, interaction.user.id, self.values[0]))


class LbView(discord.ui.View):
    def __init__(self, bot, uid, current):
        super().__init__(timeout=120)
        self.uid = uid
        self.add_item(LbSelect(bot, current))

    async def interaction_check(self, interaction):
        if interaction.user.id != self.uid:
            await interaction.response.send_message("❌ Run the command yourself to switch boards.", ephemeral=True)
            return False
        return True


def lb_embed(bot, key):
    title, rows = C.leaderboard(key)
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, (uid, val) in enumerate(rows):
        u = bot.get_user(uid)
        name = esc(u.display_name if u else f"User {uid}")
        lines.append(f"{medals[i] if i < 3 else f'`#{i + 1}`'} **{name}** — `{int(val):,}`")
    return make_embed(title, "\n".join(lines) or "*Nobody here yet.*", color=GOLD)


# ═══════════════════════════════════════
# Cog
# ═══════════════════════════════════════
class Hunt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self._ticks = 0
        self.huntbot_loop.start()

    async def cog_unload(self):
        self.huntbot_loop.cancel()

    # ── Huntbot ی ئۆفلاین: هەر خولەکێک تەواوبووەکان کۆ دەکاتەوە و DM دەنێرێت ──
    @tasks.loop(seconds=60)
    async def huntbot_loop(self):
        self._ticks += 1
        if self._ticks % 360 == 1:  # هەر ٦ کاتژمێر مێژووی کۆن پاک دەکرێتەوە
            C.prune_history()
        for uid in C.hb_pending_users():
            try:
                res = C.hb_claim(uid)
                if not res:
                    continue
                user = self.bot.get_user(uid) or await self.bot.fetch_user(uid)
                await user.send(embed=self.claim_embed(res, None))
            except (discord.Forbidden, discord.HTTPException):
                pass
            except Exception as e:
                print(f"huntbot loop هەڵە: {e}")

    @huntbot_loop.before_loop
    async def _before(self):
        await self.bot.wait_until_ready()

    # ── lootbox ی ڕۆژانە دوای !daily (بێ دەستکاریکردنی economy.py) ──
    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.command is None or ctx.command.name != "daily":
            return
        _, last, _ = get_user(ctx.author.id)
        if time.time() - last > 20:  # daily نەدرا (cooldown بوو)
            return
        res = C.grant_daily_box(ctx.author.id, last)
        if res:
            today, bonus = res
            text = (f"🎁 | **{esc(ctx.author.display_name)}**, you also got a **Lootbox**! "
                    f"(`{PREFIX} lootbox open`) • Checklist **{min(today, D.DAILY_BOX_TARGET)}/{D.DAILY_BOX_TARGET}**")
            if bonus:
                text += f"\n🏅 Daily checklist complete! **+{bonus:,} {CURRENCY}**"
            await ctx.send(text)

    # ═══════════ HUNT ═══════════
    @commands.command(name="hunt", aliases=["h", "catch"])
    async def hunt(self, ctx):
        name = esc(ctx.author.display_name)
        r = C.perform_hunt(ctx.author.id)
        if r.get("error") == "cooldown":
            await ctx.send(f"⏱️ | **{name}**, slow down! Wait **{r['wait']:.1f}s**.", delete_after=4)
        elif r.get("error") == "no_cash":
            await ctx.send(f"⚠️ | **{name}**, you need **{r['cost']} {CURRENCY}** to hunt! "
                           f"(You have `{r['balance']:,}`) Use `{PREFIX} daily`.")
        else:
            await ctx.send(hunt_message(ctx, r))

    # ═══════════ ZOO ═══════════
    @commands.command(name="zoo", aliases=["animals"])
    async def zoo(self, ctx, *args):
        C.ensure_user(ctx.author.id)
        rarity = search = None
        display = False
        tokens = list(args)
        if tokens and tokens[0].lower() in ("display", "d"):
            display = True
        elif tokens and tokens[0].lower() in ("search", "s", "find") and len(tokens) > 1:
            search = " ".join(tokens[1:])
        elif tokens:
            rarity = C.find_rarity(tokens[0])
            if rarity is None:
                search = " ".join(tokens)
        if display:
            rows = C.zoo_rows(ctx.author.id)
            lines = []
            for key in reversed(D.RARITY_ORDER):
                mine = [(a, q) for a, q, _ in rows if a["rarity"] == key]
                if mine:
                    lines.append(f"{D.RARITIES[key]['emoji']} **{D.RARITIES[key]['name']}**\n" +
                                 " ".join(f"{a['emoji']}×{q}" for a, q in mine))
            text = "\n\n".join(lines) or "*No animals yet.*"
            await ctx.send(embed=make_embed(f"🐾 {esc(ctx.author.display_name)}'s Zoo Display", text[:4000], color=GOLD, ctx=ctx))
            return
        view = ZooView(ctx, rarity, search)
        view.message = await ctx.send(embed=view.embed(), view=view)

    # ═══════════ INVENTORY ═══════════
    @commands.command(name="inventory", aliases=["bag", "backpack", "items"])
    async def inventory(self, ctx):
        uid = ctx.author.id
        coins, _, _ = get_user(uid)
        boxes, items, gems = C.get_boxes(uid), C.get_items(uid), C.get_gems(uid)
        embed = make_embed(f"🎒 {esc(ctx.author.display_name)}'s Inventory", color=GOLD, ctx=ctx)
        embed.add_field(name="💰 Balance", value=f"{CASH_EMOJI} **{coins:,}** {CURRENCY}\n💠 **{C.get_essence(uid):,}** essence")
        embed.add_field(name="📦 Lootboxes",
                        value="\n".join(f"{D.BOXES[t]['emoji']} {D.BOXES[t]['name']} ×{q}" for t, q in boxes.items()) or "—")
        embed.add_field(name="💎 Gems", value="\n".join(
            f"{g[5]} `{g[0]}` {g[4]} • {g[2]} left{' ✅' if g[3] else ''}" for g in gems[:8]) or "—", inline=False)
        embed.add_field(name="🧪 Items", value="\n".join(
            f"{D.ITEMS[k]['emoji']} {D.ITEMS[k]['name']} ×{q}" for k, q in items.items()) or "—", inline=False)
        buffs = C.get_buffs(uid)
        if buffs:
            embed.add_field(name="⏳ Active buffs", value="\n".join(
                f"{C.buff_label(k)} ({C.buff_strength_text(k, s)}) — <t:{int(e)}:R>" for k, (s, e) in buffs.items()), inline=False)
        embed.set_footer(text=f"{PREFIX} use <id/name> • {PREFIX} lootbox open • {BOT_NAME}")
        await ctx.send(embed=embed)

    @commands.command(name="buffs")
    async def buffs(self, ctx):
        buffs = C.get_buffs(ctx.author.id)
        text = "\n".join(f"{C.buff_label(k)} **{C.buff_strength_text(k, s)}** — ends <t:{int(e)}:R>"
                         for k, (s, e) in buffs.items()) or "No active buffs. Find potions in lootboxes!"
        await ctx.send(embed=make_embed("⏳ Active Buffs", text, color=MAIN, ctx=ctx))

    # ═══════════ SELL / SACRIFICE ═══════════
    def _parse_spec(self, args):
        """دەگەڕێنێتەوە (spec, هەڵە)"""
        tokens = list(args)
        if not tokens:
            return None, "usage"
        qty = None
        if len(tokens) > 1:
            last = tokens[-1].lower()
            if last.isdigit():
                qty = int(last)
                tokens = tokens[:-1]
            elif last == "all":
                tokens = tokens[:-1]
        if qty is not None and qty < 1:
            return None, "qty"
        text = " ".join(tokens)
        if text.lower() == "all":
            return dict(kind="all", qty=None), None
        key = C.find_rarity(text)
        if key:
            return dict(kind="rarity", value=key, qty=None), None
        a = C.find_animal(text)
        if a:
            return dict(kind="animal", value=a["id"], qty=qty), None
        return None, "unknown"

    async def _trade(self, ctx, args, mode):
        name = esc(ctx.author.display_name)
        verb, usage = ("sell", f"`{PREFIX} sell wolf 3` • `{PREFIX} sell common` • `{PREFIX} sell all`") if mode == "sell" \
            else ("sacrifice", f"`{PREFIX} sacrifice wolf 3` • `{PREFIX} sacrifice common` • `{PREFIX} sacrifice all`")
        spec, err = self._parse_spec(args)
        if err == "usage":
            return await ctx.send(f"❌ | **{name}**, usage: {usage}")
        if err == "qty":
            return await ctx.send(f"❌ | **{name}**, the quantity must be at least 1.")
        if err == "unknown":
            return await ctx.send(f"❌ | **{name}**, I don't know that animal or rarity.")
        C.ensure_user(ctx.author.id)
        plan = C.build_plan(ctx.author.id, spec, mode)
        if plan["count"] <= 0:
            extra = f" ({plan['protected']} protected 🔒/team)" if plan["protected"] else ""
            return await ctx.send(f"⚠️ | **{name}**, nothing to {verb}!{extra}")

        unit = CURRENCY if mode == "sell" else "essence"
        icon = CASH_EMOJI if mode == "sell" else "💠"

        def run():
            res = C.execute_plan(ctx.author.id, spec, mode)
            if res is None:
                return f"⚠️ | **{name}**, nothing to {verb}."
            counts = {aid: n for aid, n, _ in res["items"]}
            word = "sold" if mode == "sell" else "sacrificed"
            return (f"{icon} | **{name}** {word} **{res['count']:,}** animals for **{res['total']:,} {unit}**!\n"
                    f"{fmt_counts(counts)}")

        if C.plan_needs_confirm(plan):
            skip = f"\n🔒 **{plan['protected']}** protected animals will be kept." if plan["protected"] else ""
            view = ConfirmView(ctx.author.id, run)
            view.message = await ctx.send(
                f"⚠️ | **{name}**, {verb} **{plan['count']:,}** animals for **{plan['total']:,} {unit}**?\n"
                f"{fmt_counts({a: n for a, n, _ in plan['items']})}{skip}", view=view)
        else:
            await ctx.send(run())

    @commands.command(name="sell")
    async def sell(self, ctx, *args):
        await self._trade(ctx, args, "sell")

    @commands.command(name="sacrifice", aliases=["sac", "sc"])
    async def sacrifice(self, ctx, *args):
        await self._trade(ctx, args, "sacrifice")

    @commands.command(name="essence", aliases=["ess"])
    async def essence(self, ctx):
        e = C.get_essence(ctx.author.id)
        await ctx.send(f"💠 | **{esc(ctx.author.display_name)}**, you have **{e:,}** essence! "
                       f"Upgrade your Huntbot with `{PREFIX} huntbot upgrade`.")

    @commands.command(name="lock", aliases=["favorite", "fav"])
    async def lock(self, ctx, *, animal: str = ""):
        a = C.find_animal(animal)
        name = esc(ctx.author.display_name)
        if not a:
            return await ctx.send(f"❌ | **{name}**, usage: `{PREFIX} lock wolf`")
        ok = C.set_lock(ctx.author.id, a, True)
        await ctx.send(f"🔒 | **{name}**, {a['emoji']} **{a['name']}** is protected from selling/sacrifice!" if ok
                       else f"⚠️ | **{name}**, you haven't discovered {a['emoji']} **{a['name']}** yet.")

    @commands.command(name="unlock", aliases=["unfav"])
    async def unlock(self, ctx, *, animal: str = ""):
        a = C.find_animal(animal)
        name = esc(ctx.author.display_name)
        if not a:
            return await ctx.send(f"❌ | **{name}**, usage: `{PREFIX} unlock wolf`")
        ok = C.set_lock(ctx.author.id, a, False)
        await ctx.send(f"🔓 | **{name}**, {a['emoji']} **{a['name']}** is unlocked." if ok
                       else f"⚠️ | **{name}**, you haven't discovered {a['emoji']} **{a['name']}** yet.")

    # ═══════════ OWODEX ═══════════
    @commands.command(name="owodex", aliases=["dex", "zerodex"])
    async def owodex(self, ctx, *, animal: str = ""):
        uid = ctx.author.id
        C.ensure_user(uid)
        if not animal.strip():
            lines = []
            for key, r in D.RARITIES.items():
                total = [a for a in D.ANIMALS.values() if a["rarity"] == key]
                found = sum(1 for a in total if (C.animal_record(uid, a["id"]) or (0, 0))[1] > 0)
                if key in D.SECRET_RARITIES and found == 0:
                    lines.append(f"{r['emoji']} **{r['name']}** — `?/?`")
                else:
                    lines.append(f"{r['emoji']} **{r['name']}** — `{found}/{len(total)}`")
            embed = make_embed("📖 ZeroDex", "\n".join(lines) + f"\n\nLook up an animal: `{PREFIX} owodex wolf`",
                               color=GOLD, ctx=ctx)
            return await ctx.send(embed=embed)

        a = C.find_animal(animal)
        rec = C.animal_record(uid, a["id"]) if a else None
        discovered = bool(rec and rec[1] > 0)
        if a is None or (a["rarity"] in D.SECRET_RARITIES and not discovered):
            return await ctx.send(f"❌ | **{esc(ctx.author.display_name)}**, no data found for that animal.")
        r = rar(a)
        embed = make_embed(f"{a['emoji']} {a['name']}", a["description"], color=r["color"], ctx=ctx)
        embed.add_field(name="Rarity", value=f"{r['emoji']} {r['name']}")
        embed.add_field(name="Category", value=a["category"].title())
        embed.add_field(name="Availability", value=r["avail"] + (f" ({D.EVENTS[a['event']]['name']})" if a["event"] else ""))
        if discovered:
            chance = D.animal_chance_percent(a)
            embed.add_field(name="Sell Value", value=f"{a['sell']:,} {CURRENCY}")
            embed.add_field(name="Essence", value=f"{a['essence']:,}")
            embed.add_field(name="XP", value=f"{a['xp']:,}")
            embed.add_field(name="Zoo Points", value=f"{a['zoo']:,}")
            embed.add_field(name="Drop Chance", value=f"{chance:.4f}%" if chance else "Not in normal hunts")
            embed.add_field(name="📊 Your stats", value=(
                f"Owned: **{rec[0]}** • Caught: **{rec[1]}**\n"
                f"First caught: <t:{int(rec[6])}:D>\n"
                f"Pet level: **{rec[4]}**"), inline=False)
            if a["image"]:
                embed.set_image(url=a["image"])
        else:
            embed.add_field(name="❓ Undiscovered", value="Catch it to reveal its stats!", inline=False)
        await ctx.send(embed=embed)

    # ═══════════ GEMS ═══════════
    @commands.command(name="gems", aliases=["gem"])
    async def gems(self, ctx):
        gems = C.get_gems(ctx.author.id)
        if not gems:
            return await ctx.send(f"💎 | **{esc(ctx.author.display_name)}**, you have no gems. Open lootboxes to find them! "
                                  f"(`{PREFIX} lootbox`)")
        lines = [f"{g[5]} **{g[4]}** • ID `{g[0]}` • +{g[6]} animals • **{g[2]}/{g[7]}** hunts left "
                 f"{'✅ **ACTIVE**' if g[3] else ''}" for g in gems[:20]]
        embed = make_embed("💎 Hunting Gems", "\n".join(lines) + f"\n\nActivate with `{PREFIX} use <id>`", color=0x00E5FF, ctx=ctx)
        await ctx.send(embed=embed)

    @commands.command(name="geminfo")
    async def geminfo(self, ctx, gem_id: int):
        g = C.gem_info(ctx.author.id, gem_id)
        if not g:
            return await ctx.send(f"❌ | **{esc(ctx.author.display_name)}**, you don't own a gem with that ID.")
        bar = C.bar(g[2], g[7])
        embed = make_embed(f"{g[5]} {g[4]}", color=0x00E5FF, ctx=ctx)
        embed.add_field(name="ID", value=f"`{g[0]}`")
        embed.add_field(name="Effect", value=f"+{g[6]} animals per hunt")
        embed.add_field(name="Status", value="✅ Active" if g[3] else "💤 Inactive")
        embed.add_field(name="Durability", value=f"`{bar}` {g[2]}/{g[7]}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="use")
    async def use(self, ctx, *, target: str = ""):
        name = esc(ctx.author.display_name)
        target = target.strip()
        if not target:
            return await ctx.send(f"❌ | **{name}**, usage: `{PREFIX} use <gem id>` or `{PREFIX} use luck potion`")
        if target.isdigit():
            res = C.toggle_gem(ctx.author.id, int(target))
            if res is None:
                return await ctx.send(f"❌ | **{name}**, you don't own a gem with that ID.")
            state, g = res
            if state == "on":
                return await ctx.send(f"{g[5]} | **{name}**, **{g[4]}** is now active! (+{g[6]} animals per hunt, **{g[2]}** hunts left)")
            return await ctx.send(f"💤 | **{name}**, **{g[4]}** was deactivated.")
        key = C.find_item(target)
        if not key:
            return await ctx.send(f"❌ | **{name}**, I don't know that item.")
        res = C.use_item(ctx.author.id, key)
        if res is None:
            return await ctx.send(f"⚠️ | **{name}**, you don't have a **{D.ITEMS[key]['name']}**.")
        it, s, e = res
        await ctx.send(f"{it['emoji']} | **{name}** used **{it['name']}**! "
                       f"{C.buff_label(it['kind'])} **{C.buff_strength_text(it['kind'], s)}** until <t:{int(e)}:R>")

    # ═══════════ LOOTBOX ═══════════
    @commands.command(name="lootbox", aliases=["box", "boxes", "lbox"])
    async def lootbox(self, ctx, action: str = "", *args):
        uid, name = ctx.author.id, esc(ctx.author.display_name)
        C.ensure_user(uid)
        boxes = C.get_boxes(uid)
        action = action.lower()
        if action in ("history", "log"):
            rows = C.box_history(uid, 10)
            text = "\n".join(f"{D.BOXES[t]['emoji']} {rw} — <t:{int(ts)}:R>" for t, rw, ts in rows) or "No history yet."
            return await ctx.send(embed=make_embed("📜 Lootbox History", text, color=GOLD, ctx=ctx))
        if action not in ("open", "o"):
            lines = [f"{D.BOXES[t]['emoji']} **{D.BOXES[t]['name']}** ×{q}" for t, q in boxes.items()] or ["You have no lootboxes."]
            today = min(C.box_progress(uid), D.DAILY_BOX_TARGET)
            lines.append(f"\n🏅 Daily checklist: **{today}/{D.DAILY_BOX_TARGET}** lootboxes "
                         f"(+{D.CHECKLIST_REWARD:,} {CURRENCY} when done)")
            lines.append(f"Earn them every **{D.LOOTBOX_EVERY}** hunts and from `{PREFIX} daily`.")
            lines.append(f"Open: `{PREFIX} lootbox open` • History: `{PREFIX} lootbox history`")
            return await ctx.send(embed=make_embed("📦 Lootboxes", "\n".join(lines), color=GOLD, ctx=ctx))
        if not boxes:
            return await ctx.send(f"⚠️ | **{name}**, you have no lootboxes!")
        # کام box؟ چەند؟
        tier, count = None, 1
        for tok in args:
            t = tok.lower()
            if t in D.BOXES:
                tier = t
            elif t == "all":
                count = 10_000
            elif t.isdigit():
                count = max(1, int(t))
        if tier is None:
            tier = next((t for t in D.BOXES if boxes.get(t)), None)
        have = boxes.get(tier, 0)
        if have <= 0:
            return await ctx.send(f"⚠️ | **{name}**, you don't have that lootbox!")
        count = min(count, have, 25)
        cfg = D.BOXES[tier]
        label = cfg["name"] if count == 1 else f"{count}x {cfg['name']}"
        msg = await ctx.send(f"{cfg['emoji']} | **{name}** opens **{label}**...")
        res = C.open_boxes(uid, tier, count)
        if res is None:
            return await msg.edit(content=f"⚠️ | **{name}**, you don't have enough lootboxes!")
        await asyncio.sleep(1.5)
        embed = make_embed(f"{cfg['emoji']} {cfg['name']} opened!", "\n".join(f"• {r['text']}" for r in res),
                           color=cfg["color"], ctx=ctx)
        gem_ids = [r["gem_uid"] for r in res if r["type"] == "gem"]
        if gem_ids:
            embed.set_footer(text=f"{PREFIX} use <gem id> to activate • {BOT_NAME}", icon_url=ctx.author.display_avatar.url)
        await msg.edit(content=None, embed=embed)

    # ═══════════ TEAM / PETS ═══════════
    @commands.group(name="team", aliases=["pets", "pet"], invoke_without_command=True)
    async def team(self, ctx):
        C.ensure_user(ctx.author.id)
        team = C.get_team(ctx.author.id)
        embed = make_embed(f"🐾 {esc(ctx.author.display_name)}'s Team", color=GOLD, ctx=ctx)
        if not team:
            embed.description = (f"Your team is empty! Add up to **{D.MAX_TEAM}** animals:\n`{PREFIX} team add wolf`\n"
                                 "Team pets earn XP from every hunt.")
        for t in team:
            cur, need = C.level_progress(t["xp"], t["level"])
            maxed = t["level"] >= D.MAX_PET_LEVEL
            embed.add_field(
                name=f"#{t['slot']} {pet_name(t['animal'], t['nickname'])} • Lv. {t['level']}{' (MAX)' if maxed else ''}",
                value=f"`{C.bar(cur, need)}` {cur:,}/{need:,} XP\nTotal XP: **{t['xp']:,}** • Owned: **{t['qty']}** • Caught: **{t['caught']}**",
                inline=False)
        await ctx.send(embed=embed)

    @team.command(name="add")
    async def team_add(self, ctx, *, animal: str = ""):
        a, name = C.find_animal(animal), esc(ctx.author.display_name)
        if not a:
            return await ctx.send(f"❌ | **{name}**, usage: `{PREFIX} team add wolf`")
        res = C.team_add(ctx.author.id, a)
        msg = {"ok": f"✅ | **{name}**, {a['emoji']} **{a['name']}** joined your team!",
               "not_owned": f"⚠️ | **{name}**, you don't own {a['emoji']} **{a['name']}**.",
               "already": f"⚠️ | **{name}**, it's already on your team.",
               "full": f"⚠️ | **{name}**, your team is full ({D.MAX_TEAM}). Remove one first."}[res]
        await ctx.send(msg)

    @team.command(name="remove", aliases=["rm", "delete"])
    async def team_remove(self, ctx, *, animal: str = ""):
        a, name = C.find_animal(animal), esc(ctx.author.display_name)
        if not a:
            return await ctx.send(f"❌ | **{name}**, usage: `{PREFIX} team remove wolf`")
        ok = C.team_remove(ctx.author.id, a)
        await ctx.send(f"✅ | **{name}**, {a['emoji']} **{a['name']}** left your team." if ok
                       else f"⚠️ | **{name}**, it isn't on your team.")

    @commands.command(name="rename")
    async def rename(self, ctx, *args):
        name = esc(ctx.author.display_name)
        a, rest = split_animal_rest(list(args))
        if not a:
            return await ctx.send(f"❌ | **{name}**, usage: `{PREFIX} rename wolf Shadow` (or `reset`)")
        rest = " ".join(rest.split())
        if rest.lower() == "reset":
            nick = None
        else:
            if not rest or len(rest) > 20 or "\n" in rest:
                return await ctx.send(f"❌ | **{name}**, the nickname must be 1-20 characters.")
            nick = rest
        ok = C.set_nickname(ctx.author.id, a, nick)
        if not ok:
            return await ctx.send(f"⚠️ | **{name}**, you haven't discovered {a['emoji']} **{a['name']}** yet.")
        await ctx.send(f"✏️ | **{name}**, {a['emoji']} **{a['name']}** is now called **{esc(nick) if nick else a['name']}**!")

    # ═══════════ HUNTBOT ═══════════
    def claim_embed(self, res, ctx):
        by_r = {}
        for aid, n in res["counts"].items():
            r = D.ANIMALS[aid]["rarity"]
            by_r[r] = by_r.get(r, 0) + n
        breakdown = " ".join(f"{D.RARITIES[r]['emoji']} {n:,}" for r, n in
                             sorted(by_r.items(), key=lambda kv: -D.RARITY_RANK[kv[0]]))
        embed = make_embed("🤖 Huntbot returned!", color=0x7289DA, ctx=ctx)
        embed.add_field(name="🐾 Animals", value=f"**{res['animals']:,}**\n{breakdown}", inline=False)
        top = sorted(res["counts"].items(), key=lambda kv: -D.RARITY_RANK[D.ANIMALS[kv[0]]["rarity"]])
        embed.add_field(name="🔝 Best finds", value=fmt_counts(dict(top[:10])), inline=False)
        embed.add_field(name="💠 Essence", value=f"+{res['essence']:,}")
        embed.add_field(name="✨ Team XP", value=f"+{res['xp']:,}")
        if res["new"]:
            embed.add_field(name="🆕 New species", value=" ".join(D.ANIMALS[a]["emoji"] for a in res["new"]), inline=False)
        ups = level_up_lines(res["level_ups"])
        if ups:
            embed.add_field(name="Level up!", value="\n".join(ups), inline=False)
        return embed

    def hb_overview(self, ctx, row):
        uid = ctx.author.id
        lv = C.hb_levels(uid)
        st = C.hb_stats(lv)
        embed = make_embed("🤖 Huntbot", color=0x7289DA, ctx=ctx)
        now = time.time()
        if row[8] == 0:
            left = row[1] - now
            embed.description = (f"⚙️ **Running** — returns <t:{int(row[1])}:R>\n"
                                 f"`{C.bar(now - row[0], row[1] - row[0], 12)}` {fmt_dur(left)} left\n"
                                 f"Expected: **{row[3]:,}** animals • **{row[4]:,}** essence • **{row[5]:,}** XP")
        else:
            embed.description = (f"💤 **Idle.** Start a run: `{PREFIX} huntbot start [hours]`\n"
                                 f"Max run: **{st['max_hours']:g}h** • Animals/h: **{st['animals_per_hour']:.1f}** • "
                                 f"Cost/animal: **{st['cost_per_animal']} {CURRENCY}**")
        lines = []
        for key, s in D.HB_STATS.items():
            l = lv[key]
            nxt = f"{C.hb_upgrade_cost(key, l):,} 💠" if l < D.HB_MAX_LEVEL else "MAX"
            lines.append(f"{s['emoji']} **{s['name']}** Lv.{l} `{C.bar(l, D.HB_MAX_LEVEL, 8)}` • next: {nxt}")
        embed.add_field(name="Upgrades", value="\n".join(lines), inline=False)
        embed.add_field(name="💠 Essence", value=f"{C.get_essence(uid):,}")
        embed.add_field(name="✨ XP/h", value=f"{st['xp_per_hour']:.0f}")
        embed.add_field(name="📡 Bot chance", value=f"{st['bot_chance'] * 100:.2f}%")
        embed.set_footer(text=f"{PREFIX} huntbot upgrade <stat> • {BOT_NAME}", icon_url=ctx.author.display_avatar.url)
        return embed

    @commands.group(name="huntbot", aliases=["hb", "autohunt"], invoke_without_command=True)
    async def huntbot(self, ctx):
        row = C.hb_row(ctx.author.id)
        if row[8] == 0 and row[1] <= time.time():
            res = C.hb_claim(ctx.author.id)
            if res:
                return await ctx.send(embed=self.claim_embed(res, ctx))
            row = C.hb_row(ctx.author.id)
        await ctx.send(embed=self.hb_overview(ctx, row))

    @huntbot.command(name="claim", aliases=["collect"])
    async def hb_claim_cmd(self, ctx):
        res = C.hb_claim(ctx.author.id)
        if res:
            return await ctx.send(embed=self.claim_embed(res, ctx))
        await ctx.send(f"⚠️ | **{esc(ctx.author.display_name)}**, your Huntbot has nothing to collect yet.")

    @huntbot.command(name="start", aliases=["go", "send"])
    async def hb_start_cmd(self, ctx, hours: str = "max"):
        uid, name = ctx.author.id, esc(ctx.author.display_name)
        C.ensure_user(uid)
        row = C.hb_row(uid)
        if row[8] == 0:
            return await ctx.send(f"⚠️ | **{name}**, your Huntbot is already out! (<t:{int(row[1])}:R>)")
        st = C.hb_stats(C.hb_levels(uid))
        try:
            h = st["max_hours"] if hours.lower() == "max" else float(hours)
        except ValueError:
            return await ctx.send(f"❌ | **{name}**, usage: `{PREFIX} huntbot start 2` (hours) or `max`")
        h = min(h, st["max_hours"])
        if h < D.HB_MIN_HOURS:
            return await ctx.send(f"❌ | **{name}**, minimum run is **{D.HB_MIN_HOURS:g}h**.")
        animals = max(1, int(st["animals_per_hour"] * h))
        cost = animals * st["cost_per_animal"]

        def run():
            r = C.hb_start(uid, h)
            if r.get("error") == "busy":
                return f"⚠️ | **{name}**, your Huntbot is already out!"
            if r.get("error") == "no_cash":
                return f"⚠️ | **{name}**, you need **{r['cost']:,} {CURRENCY}**! (You have `{r['balance']:,}`)"
            if r.get("error"):
                return "⚠️ Could not start."
            return (f"🤖 | **{name}**, your Huntbot left for **{r['hours']:g}h**! Back <t:{int(r['end'])}:R>\n"
                    f"Paid **{r['cost']:,} {CURRENCY}**. You'll get a DM when it returns (works while offline).")

        view = ConfirmView(uid, run)
        view.message = await ctx.send(
            f"🤖 | **{name}**, send your Huntbot for **{h:g}h**? Cost: **{cost:,} {CURRENCY}** "
            f"(~{animals:,} animals, {int(st['essence_per_hour'] * h):,} essence)", view=view)

    @huntbot.command(name="upgrade", aliases=["up", "upgrades"])
    async def hb_upgrade_cmd(self, ctx, stat: str = ""):
        uid, name = ctx.author.id, esc(ctx.author.display_name)
        key = stat.lower()
        if key not in D.HB_STATS:
            lv = C.hb_levels(uid)
            lines = [f"{s['emoji']} `{PREFIX} huntbot upgrade {k}` — {s['desc']} (Lv.{lv[k]}, next "
                     f"{C.hb_upgrade_cost(k, lv[k]):,} 💠)" for k, s in D.HB_STATS.items()]
            return await ctx.send(embed=make_embed("🔧 Huntbot Upgrades", "\n".join(lines) +
                                                   f"\n\n💠 You have **{C.get_essence(uid):,}** essence.", color=0x7289DA, ctx=ctx))
        lvl = C.hb_levels(uid)[key]
        if lvl >= D.HB_MAX_LEVEL:
            return await ctx.send(f"✅ | **{name}**, **{D.HB_STATS[key]['name']}** is already at max level!")
        cost = C.hb_upgrade_cost(key, lvl)

        def run():
            r = C.hb_upgrade(uid, key, lvl)
            if r.get("ok"):
                return f"{D.HB_STATS[key]['emoji']} | **{name}**, **{D.HB_STATS[key]['name']}** is now level **{r['level']}**! (-{r['cost']:,} 💠)"
            if r.get("error") == "no_essence":
                return f"⚠️ | **{name}**, you need **{r['cost']:,} 💠 essence**. (Sacrifice animals: `{PREFIX} sacrifice`)"
            return "⚠️ Something changed, try again."

        view = ConfirmView(uid, run)
        view.message = await ctx.send(
            f"{D.HB_STATS[key]['emoji']} | **{name}**, upgrade **{D.HB_STATS[key]['name']}** "
            f"Lv.{lvl} → Lv.{lvl + 1} for **{cost:,} 💠 essence**? (You have {C.get_essence(uid):,})", view=view)

    # ═══════════ STATS / LEADERBOARD / EVENTS ═══════════
    @commands.command(name="huntstats", aliases=["hs", "hstats"])
    async def huntstats(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        s = C.hunt_stats(member.id)
        embed = make_embed(f"📊 {esc(member.display_name)}'s Hunt Stats", color=GOLD, ctx=ctx)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🎯 Hunts", value=f"{s['hunts']:,}")
        embed.add_field(name="🐾 Animals", value=f"{s['animals']:,}")
        embed.add_field(name="🏔️ Biggest session", value=f"{s['biggest']:,}")
        embed.add_field(name="💸 Spent", value=f"{s['spent']:,}")
        embed.add_field(name="💰 Earned (selling)", value=f"{s['earned']:,}")
        embed.add_field(name="💠 Essence earned", value=f"{s['essence']:,}")
        embed.add_field(name="⚪ Common", value=f"{s['common']:,}")
        embed.add_field(name="🔵 Rare", value=f"{s['rare']:,}")
        embed.add_field(name="🟡 Legendary", value=f"{s['legendary']:,}")
        embed.add_field(name="🌟 Highest rarity", value=(f"{D.RARITIES[s['highest']]['emoji']} {D.RARITIES[s['highest']]['name']}" if s["highest"] else "—"))
        embed.add_field(name="📦 Lootboxes", value=f"{s['boxes']:,}")
        embed.add_field(name="💎 Gems found", value=f"{s['gems']:,}")
        embed.add_field(name="⏱️ Hunt time", value=fmt_dur(s["hunt_time"]))
        buffs = ", ".join(f"{C.buff_label(k)}" for k in s["buffs"]) or "None"
        embed.add_field(name="⏳ Active buffs", value=buffs)
        await ctx.send(embed=embed)

    @commands.command(name="huntleaderboard", aliases=["huntlb", "hlb", "hunttop"])
    async def huntleaderboard(self, ctx, key: str = "zoo"):
        key = key.lower() if key.lower() in C.LEADERBOARDS else "zoo"
        await ctx.send(embed=lb_embed(self.bot, key), view=LbView(self.bot, ctx.author.id, key))

    @commands.command(name="events", aliases=["event"])
    async def events(self, ctx):
        evs = C.active_events()
        lines = []
        for key, start, end in evs:
            ev = D.EVENTS[key]
            animals = " ".join(D.ANIMALS[a]["emoji"] for a in D.EVENT_ANIMALS.get(key, []))
            lines.append(f"{ev['emoji']} **{ev['name']}** — ends <t:{int(end)}:R>\n{ev['desc']} {animals}")
        await ctx.send(embed=make_embed("🎉 Hunting Events", "\n\n".join(lines) or "No active events right now.",
                                        color=GOLD, ctx=ctx))

    # ═══════════ ئەدمین (تەنها خاوەن، هیچ وەڵامێک بۆ کەسی تر) ═══════════
    @commands.command(name="hevent", hidden=True)
    @commands.is_owner()
    async def hevent(self, ctx, action: str, key: str, hours: float = 24):
        if key not in D.EVENTS:
            return await ctx.send(f"❌ keys: {', '.join(D.EVENTS)}", delete_after=8)
        if action == "start":
            C.admin_event(key, max(0.01, hours))
            await ctx.send(f"✅ {D.EVENTS[key]['name']} started for {hours:g}h.", delete_after=8)
        else:
            C.admin_event_stop(key)
            await ctx.send(f"✅ {D.EVENTS[key]['name']} stopped.", delete_after=8)

    @commands.command(name="hgive", hidden=True)
    @commands.is_owner()
    async def hgive(self, ctx, kind: str, member: discord.Member, what: str = "", amount: int = 1):
        amount = max(1, min(amount, 10_000))
        if kind == "box" and what in D.BOXES:
            C.admin_give_box(member.id, what, amount)
        elif kind == "item" and what in D.ITEMS:
            C.admin_give_item(member.id, what, amount)
        elif kind == "gem" and what in D.GEMS:
            C.admin_give_gem(member.id, what)
        elif kind == "animal" and (a := C.find_animal(what)):
            C.admin_give_animal(member.id, a["id"], amount)
        else:
            return await ctx.send("❌ hgive box|item|gem|animal @user <name> [amount]", delete_after=8)
        await ctx.send("✅ done.", delete_after=5)

    @commands.command(name="hgem", hidden=True)
    @commands.is_owner()
    async def hgem(self, ctx, tier: str, animals: int, durability: int):
        if tier not in D.GEMS or animals < 1 or durability < 1:
            return await ctx.send(f"❌ tiers: {', '.join(D.GEMS)}", delete_after=8)
        C.admin_set_gem(tier, animals, durability)
        await ctx.send(f"✅ {tier} gem: +{animals} animals, {durability} hunts.", delete_after=8)


async def setup(bot):
    await bot.add_cog(Hunt(bot))
