"""
Zero Card Battle — جەنگی کارتەکانی ئەنیمی (نۆرە بە نۆرە، RPG)

  z cardbattle @کەس <گرەو>   ← تەحەدای هاوڕێیەک بکە

ڕێڕەو: تەحەدا ← قبووڵکردن ← هەر دوو یاریزان کارتێک هەڵدەبژێرن ← جەنگ
دوگمەکان: هێرش ⚔️ | هێزی سیحراوی ✨ (٪٢٥ MISS) | بەرگیری 🛡️ (چاکبوونەوە + نیوە زیان) | تەسلیمبوون 🏳️

گرەو: لە دەستپێکی جەنگدا لە هەردوو یاریزان دەبڕدرێت (escrow) و براوە هەردووکی وەردەگرێت.
ئەگەر جەنگ بەبێ براوە تەواو بوو (کاتی تەواو بوو) گرەوەکە دەگەڕێتەوە بۆ هەردووکیان.
"""

import random

import discord
from discord.ext import commands

from database import get_balance, spend_coins, add_coins
from utils import PREFIX, ERROR, SUCCESS
from .cards import (
    fetch_card, fetch_cards, rarity_info, mk, money, level_bar, err_embed, DEFAULT_IMAGE,
)

# ═══════════════════════════════════════
# ڕێکخستنەکان
# ═══════════════════════════════════════
ATTACK_RATIO = 0.30        # هێرشی ئاسایی = ٪٣٠ ی هێزی کارت
MAGIC_RATIO = 0.50         # هێزی سیحراوی = ٪٥٠
MAGIC_MISS_CHANCE = 0.25   # ئەگەری MISS ی سیحر
DEFEND_HEAL = 0.15         # بەرگیری = ٪١٥ چاکبوونەوە
DEFEND_REDUCTION = 0.50    # بەرگیری = نیوە زیان
LOG_LINES = 3              # چەند دێڕی کۆتایی لە لۆگی جەنگ پیشان بدرێت
MAX_BET = 1_000_000_000

RED = 0xE74C3C
GOLD = 0xF1C40F
BLUE = 0x3498DB

# هەر یاریزانێک لە هەمان کاتدا تەنها یەک جەنگ/تەحەدای هەبێت
ACTIVE = set()


def release(*user_ids):
    for uid in user_ids:
        ACTIVE.discard(uid)


def card_img(card):
    return card.get("image_url") or DEFAULT_IMAGE


def hp_bar(hp, max_hp, size=10):
    ratio = max(0, hp) / max_hp if max_hp else 0
    filled = round(ratio * size)
    if hp > 0 and filled == 0:
        filled = 1
    colour = "🟩" if ratio > 0.5 else "🟨" if ratio > 0.25 else "🟥"
    return colour * filled + "⬛" * (size - filled)


# ═══════════════════════════════════════
# ١. تەحەدا
# ═══════════════════════════════════════
class ChallengeView(discord.ui.View):
    def __init__(self, challenger, opponent, bet):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.bet = bet
        self.message = None

    async def on_timeout(self):
        release(self.challenger.id, self.opponent.id)
        if self.message:
            try:
                await self.message.edit(embed=mk("⌛  تەحەداکە بەسەرچوو", f"{self.opponent.mention} وەڵامی نەدایەوە.", RED), view=None)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="قبووڵکردن", emoji="✅", style=discord.ButtonStyle.success)
    async def accept(self, interaction, button):
        if interaction.user.id != self.opponent.id:
            return await interaction.response.send_message("❌ تەنها ئەو کەسەی تەحەداکراوە دەتوانێت قبووڵی بکات!", ephemeral=True)
        if not fetch_cards(self.challenger.id):
            release(self.challenger.id, self.opponent.id)
            self.stop()
            return await interaction.response.edit_message(embed=mk("❌ جەنگ هەڵوەشایەوە", f"{self.challenger.mention} هیچ کارتێکی نییە!", ERROR), view=None)
        if not fetch_cards(self.opponent.id):
            release(self.challenger.id, self.opponent.id)
            self.stop()
            return await interaction.response.edit_message(embed=mk("❌ جەنگ هەڵوەشایەوە", f"{self.opponent.mention} هیچ کارتێکی نییە!", ERROR), view=None)
        self.stop()
        view = PickView(self.challenger, self.opponent, self.bet, stage=1)
        await interaction.response.edit_message(embed=view.embed(), view=view)
        view.message = interaction.message

    @discord.ui.button(label="ڕەتکردنەوە", emoji="❌", style=discord.ButtonStyle.danger)
    async def decline(self, interaction, button):
        if interaction.user.id not in (self.opponent.id, self.challenger.id):
            return await interaction.response.send_message("❌ ئەم دوگمەیە بۆ تۆ نییە!", ephemeral=True)
        release(self.challenger.id, self.opponent.id)
        self.stop()
        who = "ڕەتیکردەوە" if interaction.user.id == self.opponent.id else "تەحەداکەی هەڵوەشاندەوە"
        await interaction.response.edit_message(embed=mk("🛑  جەنگ هەڵوەشایەوە", f"{interaction.user.mention} {who}.", RED), view=None)


# ═══════════════════════════════════════
# ٢. هەڵبژاردنی کارت (یاریزانی ١ پاشان یاریزانی ٢)
# ═══════════════════════════════════════
class PickView(discord.ui.View):
    def __init__(self, p1, p2, bet, stage, p1_card=None):
        super().__init__(timeout=90)
        self.p1, self.p2, self.bet, self.stage, self.p1_card = p1, p2, bet, stage, p1_card
        self.picker = p1 if stage == 1 else p2
        self.message = None
        cards = fetch_cards(self.picker.id)
        options = [
            discord.SelectOption(label=f"{c['character_name']} (Lvl {c['level']})"[:100], value=str(c["card_id"]),
                                 emoji=rarity_info(c["rarity"])["emoji"], description=f"PL: {c['power']:,} | {c['rarity']}")
            for c in cards[:25]
        ]
        sel = discord.ui.Select(placeholder=f"🎴 {self.picker.display_name}: کارتەکەت هەڵبژێرە...", options=options)
        sel.callback = self.on_select
        self.add_item(sel)

    def embed(self):
        if self.stage == 1:
            e = mk("🎴  هەڵبژاردنی کارتی یەکەم", f"✅ {self.p2.mention} تەحەداکەی قبووڵکرد!\n\n👉 {self.p1.mention}، کارتەکەت هەڵبژێرە:", GOLD)
        else:
            e = mk("🎴  هەڵبژاردنی کارتی دووەم", f"✅ {self.p1.mention} کارتی **{self.p1_card['character_name']}** هەڵبژارد!\n\n👉 {self.p2.mention}، ئێستا نۆرەی تۆیە:", GOLD)
            e.set_thumbnail(url=card_img(self.p1_card))
        if self.bet:
            e.add_field(name="💰 گرەو", value=money(self.bet), inline=True)
        return e

    async def interaction_check(self, interaction):
        if interaction.user.id != self.picker.id:
            await interaction.response.send_message("❌ ئێستا نۆرەی تۆ نییە!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        release(self.p1.id, self.p2.id)
        if self.message:
            try:
                await self.message.edit(embed=mk("⌛  کات تەواو بوو", "کارت هەڵنەبژێردرا، جەنگ هەڵوەشایەوە.", RED), view=None)
            except discord.HTTPException:
                pass

    async def on_select(self, interaction):
        card = fetch_card(int(self.children[0].values[0]))
        if not card or card["user_id"] != self.picker.id:
            return await interaction.response.send_message(embed=err_embed("missing"), ephemeral=True)

        if self.stage == 1:
            self.stop()
            nxt = PickView(self.p1, self.p2, self.bet, stage=2, p1_card=card)
            await interaction.response.edit_message(embed=nxt.embed(), view=nxt)
            nxt.message = interaction.message
            return

        # قۆناغی ٢: گرەو دەبڕدرێت و جەنگ دەست پێدەکات
        self.stop()
        if self.bet:
            if not spend_coins(self.p1.id, self.bet):
                release(self.p1.id, self.p2.id)
                return await interaction.response.edit_message(
                    embed=mk("❌ جەنگ هەڵوەشایەوە", f"{self.p1.mention} دراوی پێویستی نەماوە بۆ گرەو!", ERROR), view=None)
            if not spend_coins(self.p2.id, self.bet):
                add_coins(self.p1.id, self.bet)
                release(self.p1.id, self.p2.id)
                return await interaction.response.edit_message(
                    embed=mk("❌ جەنگ هەڵوەشایەوە", f"{self.p2.mention} دراوی پێویستی نەماوە بۆ گرەو!", ERROR), view=None)

        battle = BattleView(self.p1, self.p2, self.p1_card, card, self.bet)
        await interaction.response.edit_message(embed=battle.render(first=True), view=battle)
        battle.message = interaction.message


# ═══════════════════════════════════════
# ٣. جەنگ
# ═══════════════════════════════════════
class BattleView(discord.ui.View):
    def __init__(self, p1, p2, c1, c2, bet):
        super().__init__(timeout=180)
        self.p1, self.p2, self.bet = p1, p2, bet
        self.cards = {p1.id: c1, p2.id: c2}
        self.max_hp = {p1.id: c1["power"], p2.id: c2["power"]}
        self.hp = dict(self.max_hp)
        self.defending = {p1.id: False, p2.id: False}
        self.turn = p1
        self.round = 1
        self.log = []
        self.last_actor = p1
        self.ended = False
        self.message = None

    # ── یاریدەدەرەکان ──
    def other(self, user):
        return self.p2 if user.id == self.p1.id else self.p1

    def push(self, text):
        self.log.append(text)
        self.log = self.log[-LOG_LINES:]

    def render(self, first=False):
        actor = self.last_actor
        target = self.other(actor)
        e = mk(f"⚔️  {self.p1.display_name}  VS  {self.p2.display_name}", None, RED)
        log = "\n".join(f"▫️ {line}" for line in self.log) if self.log else "▫️ جەنگ دەستی پێکرد! سەرکەوتوو بە!"
        e.description = f"{log}\n\n👉 **نۆرەی:** {self.turn.mention}"
        for p in (self.p1, self.p2):
            c = self.cards[p.id]
            r = rarity_info(c["rarity"])
            shield = "  🛡️" if self.defending[p.id] else ""
            e.add_field(
                name=f"{r['emoji']} {p.display_name}{shield}",
                value=(f"**{c['character_name']}**  ·  `{level_bar(c['level'])}`\n"
                       f"❤️ `{max(0, self.hp[p.id]):,} / {self.max_hp[p.id]:,}`\n{hp_bar(self.hp[p.id], self.max_hp[p.id])}"),
                inline=True,
            )
        if self.bet:
            e.add_field(name="💰 خەڵات", value=money(self.bet * 2), inline=False)
        # وێنەی ئەو کەسەی کردارەکەی کرد + وێنەی بەرامبەر وەک thumbnail
        e.set_image(url=card_img(self.cards[actor.id]))
        e.set_thumbnail(url=card_img(self.cards[target.id]))
        e.set_footer(text=f"Round {self.round} • Zero Bot")
        return e

    async def interaction_check(self, interaction):
        if interaction.user.id not in (self.p1.id, self.p2.id):
            await interaction.response.send_message("❌ ئەم جەنگە بۆ تۆ نییە!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.ended:
            return
        self.ended = True
        if self.bet:
            add_coins(self.p1.id, self.bet)
            add_coins(self.p2.id, self.bet)
        release(self.p1.id, self.p2.id)
        if self.message:
            try:
                e = mk("⌛  کات تەواو بوو", "هیچ کردارێک نەکرا. جەنگ بەبێ براوە تەواو بوو" + (" و گرەوەکان گەڕانەوە." if self.bet else "."), RED)
                await self.message.edit(embed=e, view=None)
            except discord.HTTPException:
                pass

    async def _finish(self, interaction, winner, reason):
        self.ended = True
        loser = self.other(winner)
        if self.bet:
            add_coins(winner.id, self.bet * 2)
        release(self.p1.id, self.p2.id)
        self.stop()
        wc = self.cards[winner.id]
        r = rarity_info(wc["rarity"])
        e = mk("🏆  کۆتایی جەنگ!", None, GOLD)
        e.description = (f"🎉 **{winner.mention} براوە بوو!**\n{reason}\n\n"
                         f"👑 **کارتی براوە:** {r['emoji']} `{wc['character_name']}` (Lvl {wc['level']})")
        e.add_field(name="💰 خەڵات", value=f"**+{money(self.bet)}**" if self.bet else "جەنگی دۆستانە", inline=True)
        e.add_field(name="💀 دۆڕاو", value=loser.mention, inline=True)
        e.set_image(url=card_img(wc))
        await interaction.response.edit_message(embed=e, view=None)

    async def _after_action(self, interaction, actor):
        target = self.other(actor)
        if self.hp[target.id] <= 0:
            return await self._finish(interaction, actor, f"✨ **{self.cards[target.id]['character_name']}** تێکشکا!")
        self.last_actor = actor
        self.turn = target
        if target.id == self.p1.id:
            self.round += 1
        await interaction.response.edit_message(embed=self.render(), view=self)

    def _apply_damage(self, actor, dmg):
        """زیان دەدات، بەرگیری لەبەرچاو دەگرێت. دەگەڕێنێتەوە (زیانی کۆتایی، دەقی بەرگیری)"""
        target = self.other(actor)
        note = ""
        if self.defending[target.id]:
            dmg = int(dmg * (1 - DEFEND_REDUCTION))
            self.defending[target.id] = False
            note = " 🛡️ *(بەرگیری: زیان نیوە بوو)*"
        self.hp[target.id] -= dmg
        return dmg, note

    async def _guard_turn(self, interaction):
        if interaction.user.id != self.turn.id:
            await interaction.response.send_message("❌ نۆرەی تۆ نییە!", ephemeral=True)
            return False
        return True

    # ── دوگمەکان ──
    @discord.ui.button(label="هێرش", emoji="⚔️", style=discord.ButtonStyle.danger)
    async def attack_btn(self, interaction, button):
        if not await self._guard_turn(interaction):
            return
        actor = self.turn
        card = self.cards[actor.id]
        base = int(card["power"] * ATTACK_RATIO)
        dmg, note = self._apply_damage(actor, random.randint(int(base * 0.85), int(base * 1.15)))
        self.push(f"⚔️ {actor.mention} بە **{card['character_name']}** هێرشی کرد: **-{dmg:,}**{note}")
        await self._after_action(interaction, actor)

    @discord.ui.button(label="هێزی سیحراوی", emoji="✨", style=discord.ButtonStyle.primary)
    async def magic_btn(self, interaction, button):
        if not await self._guard_turn(interaction):
            return
        actor = self.turn
        card = self.cards[actor.id]
        if random.random() < MAGIC_MISS_CHANCE:
            self.push(f"💨 {actor.mention} هەوڵی سیحری دا بە **{card['character_name']}**، بەڵام **MISS** بوو!")
            return await self._after_action(interaction, actor)
        base = int(card["power"] * MAGIC_RATIO)
        dmg, note = self._apply_damage(actor, random.randint(int(base * 0.90), int(base * 1.20)))
        self.push(f"✨ **MAGIC!** {actor.mention} بە **{card['character_name']}** سیحرێکی کوشندەی کرد: **-{dmg:,}**{note}")
        await self._after_action(interaction, actor)

    @discord.ui.button(label="بەرگیری", emoji="🛡️", style=discord.ButtonStyle.secondary)
    async def defend_btn(self, interaction, button):
        if not await self._guard_turn(interaction):
            return
        actor = self.turn
        card = self.cards[actor.id]
        self.defending[actor.id] = True
        heal = int(card["power"] * DEFEND_HEAL)
        before = self.hp[actor.id]
        self.hp[actor.id] = min(self.max_hp[actor.id], before + heal)
        gained = self.hp[actor.id] - before
        self.push(f"🛡️ {actor.mention} بەرگری کرد و **+{gained:,} HP** چاک بووەوە!")
        await self._after_action(interaction, actor)

    @discord.ui.button(label="تەسلیم", emoji="🏳️", style=discord.ButtonStyle.secondary)
    async def surrender_btn(self, interaction, button):
        winner = self.other(interaction.user)
        await self._finish(interaction, winner, f"🏳️ {interaction.user.mention} تەسلیم بوو!")


# ═══════════════════════════════════════
# فەرمان
# ═══════════════════════════════════════
class CardBattle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cardbattle", aliases=["cbattle", "شەڕەکارت"])
    async def card_battle_cmd(self, ctx, opponent: discord.Member = None, bet: int = 0):
        """تەحەدای هاوڕێیەک بکە بۆ جەنگی کارتەکان"""
        if opponent is None:
            return await ctx.send(f"❌ بەکارهێنان: `{PREFIX} cardbattle @کەس <گرەو>`")
        if opponent.bot or opponent.id == ctx.author.id:
            return await ctx.send("❌ ناتوانیت لەگەڵ خۆت یان بۆتەکان جەنگ بکەیت!")
        if bet < 0 or bet > MAX_BET:
            return await ctx.send(f"❌ گرەو دەبێت لەنێوان **0** و **{MAX_BET:,}** بێت!")
        if ctx.author.id in ACTIVE or opponent.id in ACTIVE:
            return await ctx.send("⏳ یەکێک لە ئێوە لە جەنگێکی تردایە. چاوەڕێ بکە.")
        if not fetch_cards(ctx.author.id):
            return await ctx.send(f"❌ تۆ هیچ کارتێکت نییە! `{PREFIX} cards`")
        if not fetch_cards(opponent.id):
            return await ctx.send(f"❌ {opponent.mention} هیچ کارتێکی نییە!")
        if get_balance(ctx.author.id) < bet:
            return await ctx.send(f"❌ دراوی پێویستت نییە بۆ گرەوی {money(bet)}!")
        if get_balance(opponent.id) < bet:
            return await ctx.send(f"❌ {opponent.mention} دراوی پێویستی نییە بۆ گرەوی {money(bet)}!")

        ACTIVE.update((ctx.author.id, opponent.id))
        e = mk("⚔️  تەحەدای جەنگی کارت", None, 0x9B59B6)
        e.description = (f"🎮 {ctx.author.mention} تەحەدای {opponent.mention} دەکات!\n\n"
                         f"👉 {opponent.mention}، قبووڵی دەکەیت؟ (٦٠ چرکە)")
        e.add_field(name="💰 گرەوی هەرکەسێک", value=money(bet) if bet else "بێ گرەو", inline=True)
        if bet:
            e.add_field(name="🏆 خەڵاتی براوە", value=money(bet * 2), inline=True)
        view = ChallengeView(ctx.author, opponent, bet)
        view.message = await ctx.send(content=opponent.mention, embed=e, view=view)


async def setup(bot):
    await bot.add_cog(CardBattle(bot))
