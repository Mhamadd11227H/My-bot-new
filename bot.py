import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"بوت ئۆنلاین بوو: {bot.user}")

@bot.command(name="سلاو")
async def hello(ctx):
    await ctx.send(f"سلاو {ctx.author.mention}! 👋")

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel:
        await channel.send(f"بەخێربێیت {member.mention} بۆ سێرڤەرەکەمان! 🎉")

bot.run(os.environ["DISCORD_TOKEN"])
