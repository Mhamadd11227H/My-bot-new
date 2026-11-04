"""
👑 ZERO ROYAL BANK
دانان، دەرئینان، قازانجا ڕۆژانە، ئاستێن بانکێ (برۆنز ← شاهانە)، لیستا باشترینان و مێژوو
هەمی ب دوگمە و فۆرم (Modal). هەمان داتابەیسێ economy.db بکاردئینیت.

فەرمان:
  z bank                  ← داشبۆردا سەرەکی ب دوگمە
  z bank me [@کەس]       ← کارتا بانکێ
  z bank top              ← دەوڵەمەندترین
  z bank history          ← مێژوویا مامەلەیان
  z bank info             ← ڕێنمایی
  z dep <بڕ|all|half>     (یان z bank dep)
  z with <بڕ|all|half>    (یان z bank with)
"""

import time

import discord
from discord.ext import commands

from database import db, get_user, parse_bet
from utils import PREFIX, CURRENCY

# ═══════════════════════════════════════
# ڕێکخستن (لێرە دەستکاری بکە)
# ═══════════════════════════════════════
INTEREST_RATE = 0.10              # ٪١٠ قازانج
INTEREST_INTERVAL = 24 * 60 * 60  # هەر ٢٤ دەمژمێران جارەکێ (ب چرکە)
MAX_CATCHUP_DAYS = 365            # ئەگەر کەس درێژ نەهاتبیت، هەتا چەند ڕۆژان قازانج دهێتە هەژمارتن
BANK_CAP = 1_000_000_000          # زۆرترین بڕێ ل بانکێ (هەتا ڤێرێ قازانج دچیت). 0 = سنوور نینە
LEADERBOARD_SIZE = 10
HISTORY_SHOWN = 8

GOLD = 0xF1C40F
GREEN = 0x2ECC71
ORANGE = 0xE67E22
RED = 0xE74C3C

# ئاست: (کێمترین بڕ، ناڤ، ئیمۆجی، ڕەنگ)
TIERS = [
    (0,           "برۆنز",  "🥉", 0xCD7F32),
    (10_000,      "زیڤ",    "🥈", 0xC0C0C0),
    (100_000,     "زێڕ",    "🥇", 0xF1C40F),
    (1_000_000,   "ئەلماس", "💎", 0x5DADE2),
    (10_000_000,  "شاهانە", "👑", 0x9B59B6),
]


# ═══════════════════════════════════════
# LOGIC START : داتابەیس و مامەلە (بێ discord)
# ═══════════════════════════════════════
db.execute(
    "CREATE TABLE IF NOT EXISTS royal_bank ("
    "user_id INTEGER PRIMARY KEY, "
    "balance INTEGER NOT NULL DEFAULT 0, "
    "deposited INTEGER NOT NULL DEFAULT 0, "
    "profit INTEGER NOT NULL DEFAULT 0, "
    "opened_at REAL NOT NULL DEFAULT 0, "
    "last_interest REAL NOT NULL DEFAULT 0)"
)
db.execute(
    "CREATE TABLE IF NOT EXISTS royal_bank_log ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "user_id INTEGER NOT NULL, kind TEXT NOT NULL, "
    "amount INTEGER NOT NULL, ts REAL NOT NULL)"
)
db.commit()


def _cap():
    return BANK_CAP if BANK_CAP > 0 else 10 ** 15


def _log(uid, kind, amount):
    db.execute(
        "INSERT INTO royal_bank_log (user_id, kind, amount, ts) VALUES (?, ?, ?, ?)",
        (uid, kind, amount, time.time()),
    )


def _next_gain(balance):
    return max(0, min(int(balance * INTEREST_RATE), _cap() - balance))


def get_account(uid):
    """ئەکاونتا بانکێ دگەڕینیتەڤە (قازانجا ڕۆژان ژی دهێتە زێدەکرن). None ئەگەر نەبیت"""
    row = db.execute(
        "SELECT balance, deposited, profit, opened_at, last_interest FROM royal_bank WHERE user_id = ?",
        (uid,),
    ).fetchone()
    if row is None:
        return None
    balance, deposited, profit, opened, last = row
    gained = 0
    if balance > 0:
        full_days = int((time.time() - last) // INTEREST_INTERVAL)
        if full_days > 0:
            cap = _cap()
            for _ in range(min(full_days, MAX_CATCHUP_DAYS)):
                if balance >= cap:
                    break
                g = min(int(balance * INTEREST_RATE), cap - balance)
                balance += g
                gained += g
            last += full_days * INTEREST_INTERVAL
            profit += gained
            db.execute(
                "UPDATE royal_bank SET balance = ?, profit = ?, last_interest = ? WHERE user_id = ?",
                (balance, profit, last, uid),
            )
            if gained > 0:
                _log(uid, "interest", gained)
            db.commit()
    return {
        "balance": balance, "deposited": deposited, "profit": profit,
        "opened": opened, "last": last, "next": last + INTEREST_INTERVAL,
        "gained": gained,
    }


def bank_deposit(uid, amount):
    """دراڤ ژ کیسێ دکەتە بانکێ. یەک مامەلەیا ئەتۆمییە. (ok, err) err: bad / no_cash / cap"""
    if amount <= 0:
        return False, "bad"
    acct = get_account(uid)
    bal = acct["balance"] if acct else 0
    if bal + amount > _cap():
        return False, "cap"
    get_user(uid)
    try:
        cur = db.execute(
            "UPDATE users SET coins = coins - ? WHERE user_id = ? AND coins >= ?",
            (amount, uid, amount),
        )
        if cur.rowcount != 1:
            db.rollback()
            return False, "no_cash"
        now = time.time()
        if acct is None:
            db.execute(
                "INSERT INTO royal_bank (user_id, balance, deposited, profit, opened_at, last_interest) "
                "VALUES (?, ?, ?, 0, ?, ?)",
                (uid, amount, amount, now, now),
            )
        else:
            last = acct["last"] if bal > 0 else now   # قازانج ژ دەمێ دانانێ دەست پێ دکەت
            db.execute(
                "UPDATE royal_bank SET balance = balance + ?, deposited = deposited + ?, "
                "last_interest = ? WHERE user_id = ?",
                (amount, amount, last, uid),
            )
        _log(uid, "deposit", amount)
        db.commit()
    except BaseException:
        db.rollback()
        raise
    return True, None


def bank_withdraw(uid, amount):
    """دراڤ ژ بانکێ دبەتە کیسێ. یەک مامەلەیا ئەتۆمییە. (ok, err) err: bad / no_bank"""
    if amount <= 0:
        return False, "bad"
    get_account(uid)
    get_user(uid)
    try:
        cur = db.execute(
            "UPDATE royal_bank SET balance = balance - ? WHERE user_id = ? AND balance >= ?",
            (amount, uid, amount),
        )
        if cur.rowcount != 1:
            db.rollback()
            return False, "no_bank"
        db.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, uid))
        _log(uid, "withdraw", amount)
        db.commit()
    except BaseException:
        db.rollback()
        raise
    return True, None


def bank_history(uid, limit=HISTORY_SHOWN):
    return db.execute(
        "SELECT kind, amount, ts FROM royal_bank_log WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (uid, limit),
    ).fetchall()


def bank_top(limit=LEADERBOARD_SIZE):
    return db.execute(
        "SELECT user_id, balance FROM royal_bank WHERE balance > 0 ORDER BY balance DESC LIMIT ?",
        (limit,),
    ).fetchall()


def bank_rank(balance):
    return db.execute(
        "SELECT COUNT(*) + 1 FROM royal_bank WHERE balance > ?", (balance,)
    ).fetchone()[0]


def tier_of(balance):
    cur, nxt = TIERS[0], None
    for i, t in enumerate(TIERS):
        if balance >= t[0]:
            cur = t
            nxt = TIERS[i + 1] if i + 1 < len(TIERS) else None
    return cur, nxt
# ═══════════════════════════════════════
# LOGIC END
# ═══════════════════════════════════════


# ═══════════════════════════════════════
# دیزاین: هاریکار
# ═══════════════════════════════════════
def _fmt(n):
    return f"{n:,}"


def _bar(frac, size=12):
    frac = max(0.0, min(1.0, frac))
    filled = int(round(frac * size))
    return "▰" * filled + "▱" * (size - filled)


def _pct():
    return f"{INTEREST_RATE * 100:g}%"


def _name(bot, guild, uid):
    m = guild.get_member(uid) if guild else None
    if m:
        return discord.utils.escape_markdown(m.display_name)
    u = bot.get_user(uid)
    return discord.utils.escape_markdown(u.display_name) if u else f"#{str(uid)[-4:]}"


def _bet_err(err, name, kind, balance, max_amt):
    where = "کیسێ تە" if kind == "dep" else "بانکێ"
    return {
        "invalid": f"❌ | **{name}**، ژمارەکێ بنڤیسە، یان `all` / `half`! نموونە: `{PREFIX} {kind} 5000`",
        "no_cash": f"⚠️ | **{name}**، {where} ڤاڵایە!",
        "too_low": f"❌ | **{name}**، کێمترین بڕ `1 {CURRENCY}` یە!",
        "too_high": f"⚠️ | **{name}**، زۆرترین بڕ `{_fmt(max_amt)} {CURRENCY}` یە!",
        "insufficient": f"⚠️ | **{name}**، تەنێ `{_fmt(balance)} {CURRENCY}` ل {where} هەیە!",
    }.get(err, "❌ هەلەیەک چێبوو")


def card_embed(member, show_wallet=True):
    """کارتا بانکێ یا جوان"""
    acct = get_account(member.id)
    name = discord.utils.escape_markdown(member.display_name)

    # هەژمار نینە
    if acct is None:
        e = discord.Embed(
            title="🏦  ZERO ROYAL BANK",
            description=(
                f"**{name}**، هەژمارا بانکێ نینە هێشتا.\n\n"
                f"> 📈 هەر **٢٤ دەمژمێران** جارەکێ **{_pct()}** قازانج ل سەر {CURRENCY}ێن تە دهێتە زێدەکرن\n"
                f"> 🛡️ {CURRENCY}ێن تە ل بانکێ د ئاسایشدا نە\n"
                f"> 🏆 ئاستێ بانکێ بلند دبیت: 🥉 ← 🥈 ← 🥇 ← 💎 ← 👑\n\n"
                f"دوگمەیا **📥 دانان** بکە دا دەست پێ بکەی، یان بنڤیسە `{PREFIX} dep <بڕ>`"
            ),
            color=GOLD,
        )
        e.set_thumbnail(url=member.display_avatar.url)
        e.set_footer(text=f"Zero Royal Bank • قازانجا ڕۆژانە {_pct()}")
        return e

    bal = acct["balance"]
    (t_min, t_name, t_emoji, t_color), nxt = tier_of(bal)
    if nxt:
        frac = (bal - t_min) / (nxt[0] - t_min)
        prog = (
            f"{_bar(frac)} `{int(frac * 100)}%`\n"
            f"> بۆ ئاستێ {nxt[2]} **{nxt[1]}** پێدڤی ب `{_fmt(nxt[0] - bal)}` یێن دی یە"
        )
    else:
        prog = f"{_bar(1)} `MAX`\n> تە گەهشتیە بلندترین ئاستی 👑"

    desc = f"### {t_emoji}  ئاستێ {t_name}\n{prog}"
    if acct["gained"] > 0:
        desc += f"\n\n🎉 **+{_fmt(acct['gained'])} {CURRENCY}** قازانج هاتە زێدەکرن!"

    e = discord.Embed(title=f"🏦  هەژمارا بانکێ ─ {name}", description=desc, color=t_color)
    if show_wallet:
        wallet = get_user(member.id)[0]
        e.add_field(name="💼 کیسە", value=f"```{_fmt(wallet)}```", inline=True)
    e.add_field(name="🏦 بانک", value=f"```{_fmt(bal)}```", inline=True)
    e.add_field(name="📈 قازانج", value=f"```+{_fmt(acct['profit'])}```", inline=True)
    e.add_field(
        name="⏳ قازانجا دیتر",
        value=f"<t:{int(acct['next'])}:R>\n`+{_fmt(_next_gain(bal))}` {CURRENCY}",
        inline=True,
    )
    if show_wallet:
        e.add_field(name="💎 کۆی هەمی", value=f"`{_fmt(wallet + bal)}`", inline=True)
    e.add_field(name="📅 ڤەکرنا هەژمارێ", value=f"<t:{int(acct['opened'])}:D>", inline=True)
    e.set_thumbnail(url=member.display_avatar.url)
    e.set_footer(text=f"Zero Royal Bank • قازانجا ڕۆژانە {_pct()}")
    return e


def top_embed(bot, guild, user):
    rows = bank_top()
    medals = ["🥇", "🥈", "🥉"]
    if rows:
        lines = []
        for i, (uid, zeros) in enumerate(rows):
            medal = medals[i] if i < 3 else f"`{i + 1}.`"
            lines.append(
                f"{medal} **{_name(bot, guild, uid)}** ─ `{_fmt(zeros)}` {tier_of(zeros)[0][2]}"
            )
        body = "\n".join(lines)
    else:
        body = "✨ *هێشتا کەسێ دراڤ نەکریە بانکێ!*"
    acct = get_account(user.id)
    if acct and acct["balance"] > 0:
        body += f"\n\n━━━━━━━━━━━━━━━\n📍 **پلەیا تە:** `#{bank_rank(acct['balance'])}` ─ `{_fmt(acct['balance'])}`"
    e = discord.Embed(title="🏆  دەوڵەمەندترین ل بانکێ", description=body, color=GOLD)
    e.set_footer(text="Zero Royal Bank")
    return e


def history_embed(user):
    rows = bank_history(user.id)
    icons = {"deposit": ("📥", "دانان", "+"), "withdraw": ("📤", "دەرئینان", "-"), "interest": ("📈", "قازانج", "+")}
    if rows:
        lines = []
        for kind, amount, ts in rows:
            icon, label, sign = icons.get(kind, ("▫️", kind, ""))
            lines.append(f"{icon} **{label}** ─ `{sign}{_fmt(amount)}` ─ <t:{int(ts)}:R>")
        body = "\n".join(lines)
    else:
        body = "✨ *هێشتا چ مامەلە نینن.*"
    e = discord.Embed(title="📜  مێژوویا بانکێ", description=body, color=GOLD)
    e.set_footer(text=f"دوماهیک {HISTORY_SHOWN} مامەلە • Zero Royal Bank")
    return e


def info_embed():
    tiers = "\n".join(
        f"{t[2]} **{t[1]}** ─ ژ `{_fmt(t[0])}` ڤە" for t in TIERS
    )
    e = discord.Embed(
        title="ℹ️  ڕێنمایا بانکا شاهانە",
        description=(
            f"📈 **قازانج:** هەر **٢٤ دەمژمێران** جارەکێ **{_pct()}** ل سەر بانکا تە زێدە دبیت (ل سەر قازانجا پێشی ژی).\n"
            f"🛡️ **ئاسایش:** {CURRENCY}ێن د بانکێ دا نابنە شەرت و نامینیتە د یاریاندا.\n"
            f"🏔️ **سنوور:** هەتا `{_fmt(_cap())}` ل بانکێ دمینیت.\n\n"
            f"**🏆 ئاستێن بانکێ**\n{tiers}\n\n"
            f"**📋 فەرمان**\n"
            f"`{PREFIX} bank` ─ داشبۆردا سەرەکی\n"
            f"`{PREFIX} dep <بڕ|all|half>` ─ دانان\n"
            f"`{PREFIX} with <بڕ|all|half>` ─ دەرئینان\n"
            f"`{PREFIX} bank me [@کەس]` ─ کارتا بانکێ\n"
            f"`{PREFIX} bank top` ─ باشترینان\n"
            f"`{PREFIX} bank history` ─ مێژوو"
        ),
        color=GOLD,
    )
    e.set_footer(text="Zero Royal Bank")
    return e


# ═══════════════════════════════════════
# دوگمەیێن پشتڕاستکرنێ
# ═══════════════════════════════════════
class ConfirmView(discord.ui.View):
    def __init__(self, user, kind, amount, parent=None):
        super().__init__(timeout=45)
        self.user, self.kind, self.amount, self.parent = user, kind, amount, parent
        self.message = None

    async def interaction_check(self, inter):
        if inter.user.id != self.user.id:
            await inter.response.send_message("❌ ئەڤ دوگمەیە بۆ تە نینە!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(
                    embed=discord.Embed(title="⌛ کات ب سەر چوو", description="مامەلە هاتە هەڵوەشاندن.", color=RED),
                    view=None,
                )
            except discord.HTTPException:
                pass

    @discord.ui.button(label="پشتڕاستکرن", emoji="✅", style=discord.ButtonStyle.success)
    async def confirm(self, inter, button):
        uid = self.user.id
        if self.kind == "dep":
            ok, err = bank_deposit(uid, self.amount)
        else:
            ok, err = bank_withdraw(uid, self.amount)

        if not ok:
            reason = {
                "no_cash": "کیسێ تە ڤاڵایە یان بڕ نەماوە.",
                "no_bank": "ئەو بڕە ل بانکێ نەماوە.",
                "cap": f"بانک دگەهیتە سنوورێ خوە (`{_fmt(_cap())}`).",
            }.get(err, "هەلەیەک چێبوو.")
            e = discord.Embed(title="❌  مامەلە سەرنەکەفت", description=reason, color=RED)
            await inter.response.edit_message(embed=e, view=None)
            self.stop()
            return

        wallet = get_user(uid)[0]
        bank_now = get_account(uid)["balance"]
        if self.kind == "dep":
            w_before, b_before = wallet + self.amount, bank_now - self.amount
            title, color = "📥  دانان ب سەرکەفتی بوو", GREEN
            line = f"✨ **{_fmt(self.amount)} {CURRENCY}** هاتە دانان ل بانکێ"
        else:
            w_before, b_before = wallet - self.amount, bank_now + self.amount
            title, color = "📤  دەرئینان ب سەرکەفتی بوو", ORANGE
            line = f"✨ **{_fmt(self.amount)} {CURRENCY}** ژ بانکێ هاتە دەرئینان"

        e = discord.Embed(
            title=title,
            description=(
                f"{line}\n\n"
                f"💼 **کیسە:** `{_fmt(w_before)}` ➜ `{_fmt(wallet)}`\n"
                f"🏦 **بانک:** `{_fmt(b_before)}` ➜ `{_fmt(bank_now)}`"
            ),
            color=color,
        )
        e.set_footer(text="✅ پشتڕاستکرا • Zero Royal Bank")
        await inter.response.edit_message(embed=e, view=None)
        self.stop()
        if self.parent:
            await self.parent.refresh_message()

    @discord.ui.button(label="هەڵوەشاندن", emoji="✖️", style=discord.ButtonStyle.danger)
    async def cancel(self, inter, button):
        e = discord.Embed(
            title="🚫  هاتە هەڵوەشاندن",
            description="چ گوهۆڕین ل {} ێن تە نەهاتنە کرن.".format(CURRENCY),
            color=RED,
        )
        await inter.response.edit_message(embed=e, view=None)
        self.stop()


# ═══════════════════════════════════════
# فۆرما بڕی (Modal)
# ═══════════════════════════════════════
class AmountModal(discord.ui.Modal):
    def __init__(self, parent, kind):
        super().__init__(title=("📥 دانانا " if kind == "dep" else "📤 دەرئینانا ") + CURRENCY)
        self.parent, self.kind = parent, kind
        self.amount = discord.ui.TextInput(
            label="بڕ", placeholder="5000   /   all   /   half", max_length=20,
        )
        self.add_item(self.amount)

    async def on_submit(self, inter):
        async def send(content=None, embed=None, view=None):
            await inter.response.send_message(content=content, embed=embed, view=view, ephemeral=True)
            return await inter.original_response()

        await self.parent.cog.start_flow(inter.user, self.kind, self.amount.value, send, parent=self.parent)


# ═══════════════════════════════════════
# داشبۆردا سەرەکی (دوگمە)
# ═══════════════════════════════════════
class BankView(discord.ui.View):
    def __init__(self, cog, author):
        super().__init__(timeout=180)
        self.cog, self.author = cog, author
        self.message = None

    async def interaction_check(self, inter):
        if inter.user.id != self.author.id:
            await inter.response.send_message(
                f"❌ ئەڤ داشبۆردە بۆ **{discord.utils.escape_markdown(self.author.display_name)}** یە. "
                f"بنڤیسە `{PREFIX} bank` دا یا خوە ڤەکەی!",
                ephemeral=True,
            )
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

    async def refresh_message(self):
        if self.message:
            try:
                await self.message.edit(embed=card_embed(self.author), view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="دانان", emoji="📥", style=discord.ButtonStyle.success, row=0)
    async def dep_btn(self, inter, button):
        await inter.response.send_modal(AmountModal(self, "dep"))

    @discord.ui.button(label="دەرئینان", emoji="📤", style=discord.ButtonStyle.primary, row=0)
    async def with_btn(self, inter, button):
        await inter.response.send_modal(AmountModal(self, "with"))

    @discord.ui.button(label="نویکرن", emoji="🔄", style=discord.ButtonStyle.secondary, row=0)
    async def refresh_btn(self, inter, button):
        await inter.response.edit_message(embed=card_embed(self.author), view=self)

    @discord.ui.button(label="باشترین", emoji="🏆", style=discord.ButtonStyle.secondary, row=1)
    async def top_btn(self, inter, button):
        await inter.response.send_message(
            embed=top_embed(self.cog.bot, inter.guild, inter.user), ephemeral=True)

    @discord.ui.button(label="مێژوو", emoji="📜", style=discord.ButtonStyle.secondary, row=1)
    async def hist_btn(self, inter, button):
        await inter.response.send_message(embed=history_embed(inter.user), ephemeral=True)

    @discord.ui.button(label="ڕێنمایی", emoji="ℹ️", style=discord.ButtonStyle.secondary, row=1)
    async def info_btn(self, inter, button):
        await inter.response.send_message(embed=info_embed(), ephemeral=True)


# ═══════════════════════════════════════
# Cog
# ═══════════════════════════════════════
class Bank(commands.Cog, name="Bank"):
    def __init__(self, bot):
        self.bot = bot

    async def start_flow(self, user, kind, text, send, parent=None):
        """بڕی دانان/دەرئینانێ دپشکنیت و پەیامێ پشتڕاستکرنێ دنێریت"""
        name = discord.utils.escape_markdown(user.display_name)
        wallet = get_user(user.id)[0]
        acct = get_account(user.id)
        bank_bal = acct["balance"] if acct else 0

        if kind == "dep":
            room = _cap() - bank_bal
            if room <= 0:
                return await send(content=f"🏦 | **{name}**، بانکا تە گەهشتیە سنوورێ خوە (`{_fmt(_cap())}`)!")
            balance, max_amt = wallet, min(wallet, room)
        else:
            balance, max_amt = bank_bal, bank_bal

        amount, err = parse_bet(text, balance, 1, max(max_amt, 1))
        if err:
            return await send(content=_bet_err(err, name, kind, balance, max_amt))

        if kind == "dep":
            title = "🤔  پشتڕاستکرنا دانانێ"
            ask = f"تو دڤێت **{_fmt(amount)} {CURRENCY}** بخەیە بانکێ؟"
            w_after, b_after = wallet - amount, bank_bal + amount
            color = GREEN
        else:
            title = "🤔  پشتڕاستکرنا دەرئینانێ"
            ask = f"تو دڤێت **{_fmt(amount)} {CURRENCY}** ژ بانکێ دەرئینی؟"
            w_after, b_after = wallet + amount, bank_bal - amount
            color = ORANGE

        e = discord.Embed(
            title=title,
            description=(
                f"❓ **{name}**، {ask}\n\n"
                f"💼 **کیسە:** `{_fmt(wallet)}` ➜ `{_fmt(w_after)}`\n"
                f"🏦 **بانک:** `{_fmt(bank_bal)}` ➜ `{_fmt(b_after)}`\n\n"
                f"⏳ *٤٥ چرکەیان هەیە*"
            ),
            color=color,
        )
        e.set_footer(text="Zero Royal Bank")
        view = ConfirmView(user, kind, amount, parent)
        view.message = await send(embed=e, view=view)

    # ── z bank ──
    @commands.group(name="bank", aliases=["بانک"], invoke_without_command=True)
    async def bank_group(self, ctx):
        view = BankView(self, ctx.author)
        view.message = await ctx.send(embed=card_embed(ctx.author), view=view)

    @bank_group.command(name="me", aliases=["card", "acc"])
    async def bank_me(self, ctx, member: discord.Member = None):
        if member is None or member.id == ctx.author.id:
            view = BankView(self, ctx.author)
            view.message = await ctx.send(embed=card_embed(ctx.author), view=view)
        else:
            await ctx.send(embed=card_embed(member, show_wallet=False))

    @bank_group.command(name="top", aliases=["lb", "leaderboard"])
    async def bank_top_cmd(self, ctx):
        await ctx.send(embed=top_embed(self.bot, ctx.guild, ctx.author))

    @bank_group.command(name="history", aliases=["log"])
    async def bank_history_cmd(self, ctx):
        await ctx.send(embed=history_embed(ctx.author))

    @bank_group.command(name="info", aliases=["help"])
    async def bank_info_cmd(self, ctx):
        await ctx.send(embed=info_embed())

    @bank_group.command(name="dep", aliases=["deposit"])
    async def bank_dep(self, ctx, amount: str = None):
        await self._cmd_flow(ctx, "dep", amount)

    @bank_group.command(name="with", aliases=["withdraw"])
    async def bank_with(self, ctx, amount: str = None):
        await self._cmd_flow(ctx, "with", amount)

    # ── z dep / z with ──
    @commands.command(name="dep", aliases=["deposit", "دانان"])
    async def dep(self, ctx, amount: str = None):
        await self._cmd_flow(ctx, "dep", amount)

    @commands.command(name="with", aliases=["withdraw", "دەرئینان"])
    async def with_cmd(self, ctx, amount: str = None):
        await self._cmd_flow(ctx, "with", amount)

    async def _cmd_flow(self, ctx, kind, amount):
        if not amount:
            name = discord.utils.escape_markdown(ctx.author.display_name)
            return await ctx.send(
                f"⚠️ | **{name}**، بڕەکێ دیاری بکە! نموونە: `{PREFIX} {kind} 5000` یان `{PREFIX} {kind} all`"
            )
        await self.start_flow(ctx.author, kind, amount, ctx.send)


async def setup(bot):
    await bot.add_cog(Bank(bot))
