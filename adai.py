# adai.py
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True   # add this line
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

NOT_IN_UNI_ROLE = "Outsider"
SCHOOL_ROLES = ["SITE", "SPIA", "Law", "SDA", "SAFS", "Business"]

@bot.event
async def on_member_update(before, after):
    role_names = [r.name for r in after.roles]
    
    if NOT_IN_UNI_ROLE in role_names:
        roles_to_remove = [r for r in after.roles if r.name in SCHOOL_ROLES]
        if roles_to_remove:
            await after.remove_roles(*roles_to_remove)
            print(f"Removed {[r.name for r in roles_to_remove]} from {after.name}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))