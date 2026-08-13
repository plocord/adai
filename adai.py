# adai.py



#-------------------------START--------------------------------
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import random
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp
from discord.ext import tasks
import itertools
import sqlite3
from datetime import datetime
from datetime import datetime, timezone, timedelta
import re

AZ_TZ = timezone(timedelta(hours=4))

load_dotenv()

db = sqlite3.connect("adai.db")
cursor = db.cursor()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True   # add this line
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
#---------------------------------------------------------


#-------------------------HELP---------------------------------
def build_help_embed():
    embed = discord.Embed(
        title="ADAi Commands",
        description="Here's everything I can do:",
        color=discord.Color.blurple()
    )
    embed.add_field(name="🎉 Fun", value=(
        "`!8ball <question>` — Ask the magic 8-ball\n"
        "`!rate <thing>` — Get a rating out of 10\n"
        "`!coffee` — Brew a virtual coffee\n"
        "`!choose <a, b, c>` — Let the bot decide\n"
        "`!coinflip` / `!cf` — Flip a coin \n"
        "`!quote` — Turn a message into a quote (reply to a message with this command) \n"

    ), inline=False)
    embed.add_field(name="🛡️ Moderation", value=(
        "`!clear <amount>` — Delete messages (requires Manage Messages)\n"
        "`!warn @user <reason>` — Warn a user (!warnhelp for more info, requires Kick Members)\n"
        "`!ban @user <reason>` — Ban a user (requires Ban Members)\n"

    ), inline=False)
    embed.add_field(name="⚙️ Utility", value=(
        "`!ping` — Check if I'm alive\n"
        "`!help` / `/help` — Show this menu \n"
        "`!pfp <user>` — Show a user's profile picture \n"
    ), inline=False)
    embed.set_footer(text="ADAi — ADA University Discord bot")
    return embed

@bot.command()
async def help(ctx):
    await ctx.send(embed=build_help_embed())

@bot.tree.command(name="help", description="Show what ADAi can do")
async def help_slash(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_help_embed())
#---------------------------------------------------------


#-------------------------PING--------------------------------
@bot.command()
async def ping(ctx):
    await ctx.send("Pongg!!")

NOT_IN_UNI_ROLE = "Outsider"
SCHOOL_ROLES = ["SITE", "SPIA", "Law", "SDA", "SAFS", "Business"]
#---------------------------------------------------------



#-------------------------BAN--------------------------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason=None):
    if member is None:
        await ctx.send("Usage: `!ban @user reason`")
        return
    
    if reason is None:
        reason = "No reason provided"
    
    try:
        await member.send(f"You've been banned from **{ctx.guild.name}**. Reason: {reason}")
    except discord.Forbidden:
        pass  # DMs disabled, ignore
    
    await member.ban(reason=reason)
    await ctx.send(f"🔨 **{member.display_name}** has been banned. Reason: {reason}")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need the **Ban Members** permission to use this command.")
    else:
        await ctx.send(f"⚠️ Something went wrong: `{error}`")
        print(f"Ban command error: {error}")


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, user_input=None):
    if user_input is None:
        await ctx.send("Usage: `!unban <user_id or username#0000>`")
        return
    
    banned_users = [entry async for entry in ctx.guild.bans()]
    
    target = None
    for ban_entry in banned_users:
        user = ban_entry.user
        if user_input.isdigit() and str(user.id) == user_input:
            target = user
            break
        elif str(user) == user_input:  # matches "username#0000" or "username"
            target = user
            break
    
    if target is None:
        await ctx.send("Couldn't find that user in the ban list.")
        return
    
    await ctx.guild.unban(target)
    await ctx.send(f"✅ **{target.name}** has been unbanned.")

@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need the **Ban Members** permission to use this command.")
    else:
        await ctx.send(f"⚠️ Something went wrong: `{error}`")
        print(f"Unban command error: {error}")
#---------------------------------------------------------



#-------------------------WARN---------------------------------


@bot.command()
async def warnhelp(ctx):
    embed = discord.Embed(
        title="Warning System Commands",
        description="All warning commands require the **Kick Members** permission.",
        color=discord.Color.orange()
    )
    embed.add_field(name="!warn @user <reason>", value="Warn a user", inline=False)
    embed.add_field(name="!warnings @user", value="Show a user's warning history", inline=False)
    embed.add_field(name="!removewarning @user <number>", value="Remove a specific warning by its number", inline=False)
    embed.add_field(name="!clearwarnings @user", value="Remove all warnings for a user", inline=False)
    
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member = None, *, reason=None):
    if member is None or reason is None:
        await ctx.send("Usage: `!warn @user reason`")
        return
    
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO warnings (user_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?)",
        (str(member.id), str(ctx.author.id), reason, str(datetime.now(AZ_TZ)))
    )
    db.commit()
    
    await ctx.send(f"⚠️ **{member.display_name}** has been warned. Reason: {reason}")
    try:
        await member.send(f"You've been warned in **{ctx.guild.name}**. Reason: {reason}")
    except discord.Forbidden:
        pass

@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need the **Kick Members** permission to use this command.")
    else:
        await ctx.send(f"⚠️ Something went wrong: `{error}`")
        print(f"Warn command error: {error}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def warnings(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    cursor = db.cursor()
    cursor.execute("SELECT reason, timestamp FROM warnings WHERE user_id = ?", (str(member.id),))
    rows = cursor.fetchall()
    
    if not rows:
        await ctx.send(f"{member.display_name} has no warnings.")
        return
    
    embed = discord.Embed(title=f"Warnings for {member.display_name}", color=discord.Color.orange())
    for i, (reason, timestamp) in enumerate(rows, start=1):
        embed.add_field(name=f"Warning #{i}", value=f"{reason}\n*{timestamp}*", inline=False)
    
    await ctx.send(embed=embed)
@warnings.error
async def warnings_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need the **Kick Members** permission to use this command.")
    else:
        await ctx.send(f"⚠️ Something went wrong: `{error}`")
        print(f"Warnings command error: {error}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def removewarning(ctx, member: discord.Member = None, index: int = None):
    if member is None or index is None:
        await ctx.send("Usage: `!removewarning @user <warning number>` — check numbers with `!warnings @user`")
        return
    
    cursor = db.cursor()
    cursor.execute("SELECT id FROM warnings WHERE user_id = ? ORDER BY id", (str(member.id),))
    rows = cursor.fetchall()
    
    if not rows or index < 1 or index > len(rows):
        await ctx.send(f"Invalid warning number. {member.display_name} has {len(rows)} warning(s).")
        return
    
    warning_id = rows[index - 1][0]
    cursor.execute("DELETE FROM warnings WHERE id = ?", (warning_id,))
    db.commit()
    
    await ctx.send(f"✅ Removed warning #{index} from **{member.display_name}**.")

@removewarning.error
async def removewarning_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need the **Kick Members** permission to use this command.")
    else:
        await ctx.send(f"⚠️ Something went wrong: `{error}`")
        print(f"Removewarning command error: {error}")


@bot.command()
@commands.has_permissions(kick_members=True)
async def clearwarnings(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Usage: `!clearwarnings @user`")
        return
    
    cursor = db.cursor()
    cursor.execute("DELETE FROM warnings WHERE user_id = ?", (str(member.id),))
    db.commit()
    
    await ctx.send(f"✅ Cleared all warnings for **{member.display_name}**.")

@clearwarnings.error
async def clearwarnings_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need the **Kick Members** permission to use this command.")
    else:
        await ctx.send(f"⚠️ Something went wrong: `{error}`")
        print(f"Clearwarnings command error: {error}")
#---------------------------------------------------------


#-------------------------MEMBER UPDATE-------------------------------
@bot.event
async def on_member_update(before, after):
    role_names = [r.name for r in after.roles]
    
    if NOT_IN_UNI_ROLE in role_names:
        roles_to_remove = [r for r in after.roles if r.name in SCHOOL_ROLES]
        if roles_to_remove:
            await after.remove_roles(*roles_to_remove)
            print(f"Removed {[r.name for r in roles_to_remove]} from {after.name}")
#---------------------------------------------------------


#-------------------------PROFILE PICTURE------------------------------
@bot.command()
async def pfp(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    
    avatar_url = member.display_avatar.replace(size=1024).url
    
    embed = discord.Embed(title=f"{member.display_name}'s profile picture")
    embed.set_image(url=avatar_url)
    
    await ctx.send(embed=embed)
#---------------------------------------------------------

#-------------------------QUOTE-----------------------------------

def parse_bold_tokens(text):
    """Split text into (word, is_bold) tokens based on **markdown**."""
    parts = re.split(r'(\*\*.*?\*\*)', text)
    tokens = []
    for part in parts:
        if not part:
            continue
        bold = part.startswith("**") and part.endswith("**")
        content = part[2:-2] if bold else part
        for word in content.split(" "):
            if word:
                tokens.append((word, bold))
    return tokens

def wrap_tokens(tokens, regular_font, bold_font, max_width, draw):
    """Wrap (word, is_bold) tokens into lines that fit max_width."""
    lines = []
    current_line = []
    current_width = 0
    space_width = draw.textlength(" ", font=regular_font)
    
    for word, bold in tokens:
        font = bold_font if bold else regular_font
        word_width = draw.textlength(word, font=font)
        added_width = word_width if not current_line else word_width + space_width
        
        if current_width + added_width <= max_width or not current_line:
            current_line.append((word, bold))
            current_width += added_width
        else:
            lines.append(current_line)
            current_line = [(word, bold)]
            current_width = word_width
    
    if current_line:
        lines.append(current_line)
    return lines

@bot.command()
async def quote(ctx):
    if ctx.message.reference is None:
        await ctx.send("Reply to a message with `!quote` to turn it into a quote!")
        return
    
    quoted_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    text = quoted_msg.content
    author = quoted_msg.author
    
    if not text:
        await ctx.send("That message has no text to quote!")
        return
    
    avatar_url = author.display_avatar.replace(size=512).url
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as resp:
            avatar_bytes = await resp.read()
    
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("L")
    avatar = avatar.resize((400, 400)).convert("RGB")
    
    fade_width = 150
    mask = Image.new("L", (400, 400), 255)
    mask_draw = ImageDraw.Draw(mask)
    for x in range(400 - fade_width, 400):
        opacity = int(255 * (1 - (x - (400 - fade_width)) / fade_width))
        mask_draw.line([(x, 0), (x, 400)], fill=opacity)
    
    black_bg = Image.new("RGB", (400, 400), color=(10, 10, 10))
    faded_avatar = Image.composite(avatar, black_bg, mask)
    
    regular_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    bold_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    italic_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", 20)
    
    dummy_canvas = Image.new("RGB", (900, 100))
    dummy_draw = ImageDraw.Draw(dummy_canvas)
    
    tokens = parse_bold_tokens(f'"{text}"')
    lines = wrap_tokens(tokens, regular_font, bold_font, 440, dummy_draw)
    
    line_height = 40
    text_block_height = len(lines) * line_height
    author_height = 50
    top_margin = 60
    bottom_margin = 40
    
    needed_height = top_margin + text_block_height + author_height + bottom_margin
    canvas_height = max(400, needed_height)
    
    canvas = Image.new("RGB", (900, canvas_height), color=(10, 10, 10))
    canvas.paste(faded_avatar, (0, 0))
    
    draw = ImageDraw.Draw(canvas)
    
    y = (canvas_height - text_block_height - author_height) // 2
    for line in lines:
        x = 450
        for word, bold in line:
            font = bold_font if bold else regular_font
            draw.text((x, y), word, fill="white", font=font)
            x += draw.textlength(word, font=font) + draw.textlength(" ", font=font)
        y += line_height
    
    draw.text((450, y + 20), f"— {author.display_name}", fill=(180, 180, 180), font=italic_font)
    
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    buffer.seek(0)
    
    await ctx.send(file=discord.File(buffer, filename="quote.png"))
#---------------------------------------------------------


#-------------------------8BALL--------------------------------
EIGHT_BALL_RESPONSES = [
    "It is certain.",
    "Without a doubt.",
    "Yes, definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very doubtful."
]

@bot.command(name="8ball")
async def eightball(ctx, *, question=None):
    if question is None:
        await ctx.send("You need to ask a question! e.g. `!8ball will i pass this exam`")
        return
    answer = random.choice(EIGHT_BALL_RESPONSES)
    await ctx.send(f"🎱 **{ctx.author.display_name} asked:** {question}\n**Answer:** {answer}")
#---------------------------------------------------------




#-----------------------RATE----------------------------------
@bot.command()
async def rate(ctx, *, thing=None):
    if thing is None:
        await ctx.send("Rate what? e.g. `!rate pineapple on pizza`")
        return
    score = random.randint(0, 10)
    await ctx.send(f"📊 **{ctx.author.display_name}** rated **{thing}**: **{score}/10**")
#---------------------------------------------------------





#-------------------------COINFLIP--------------------------------
@bot.command(aliases=["cf"])
async def coinflip(ctx):
    message = await ctx.send("<a:coinflip:1536412337987391529> Flipping the coin...")
    await asyncio.sleep(2)  # Simulate a delay for suspense
    result = random.choice(["Heads", "Tails"])
    await message.edit(content=f"🪙 **{ctx.author.display_name}** flipped a coin: **{result}**!")#---------------------------------------------------------

#-------------------------COFFEE-----------------------------------
COFFEE_RESPONSES = [
    "☕ Here's your coffee, freshly brewed!",
    "☕ One espresso shot, coming right up!",
    "☕ Brewing... done! Extra hot, just how you like it.",
    "☕ Here's a latte with a little heart drawn on top.",
    "☕ Watch out, this one's steaming hot!",
    "☕ Cold brew for you, since it's probably too hot outside anyway.",
    "☕ Here's your coffee. No sugar, just like your code reviews."
]

COFFEE_GIFS = [
    "https://c.tenor.com/Mm3NPYMZDw8AAAAd/tenor.gif",
    "https://c.tenor.com/MpCcg8u5LlAAAAAd/tenor.gif",
    "https://c.tenor.com/vD4J7J3JTnUAAAAd/tenor.gif",
    "https://c.tenor.com/FFAiNXfiZrQAAAAd/tenor.gif"


    # add a few more for variety if you want
]

@bot.command()
async def coffee(ctx):
    response = random.choice(COFFEE_RESPONSES)
    embed = discord.Embed(description=f"{response}\n*Served to {ctx.author.display_name}*")
    embed.set_image(url=random.choice(COFFEE_GIFS))
    await ctx.send(embed=embed)
#---------------------------------------------------------

#-------------------------CHOOSE--------------------------------
@bot.command()
async def choose(ctx, *, options=None):
    if options is None:
        await ctx.send("Give me some options! e.g. `!choose pizza, sushi, tacos`")
        return
    
    choices = [opt.strip() for opt in options.split(",") if opt.strip()]
    
    if len(choices) < 2:
        await ctx.send("I need at least 2 options separated by commas! e.g. `!choose pizza, sushi, tacos`")
        return
    
    pick = random.choice(choices)
    await ctx.send(f"🤔 **{ctx.author.display_name}** asked me to choose between: {', '.join(choices)}\n**I choose:** {pick}")
#---------------------------------------------------------

#-------------------------CLEAR--------------------------------
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = None):
    if amount is None:
        await ctx.send("Specify how many messages to clear! e.g. `!clear 10`")
        return
    
    if amount < 1 or amount > 100:
        await ctx.send("Please choose a number between 1 and 100.")
        return
    
    deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message itself
    confirmation = await ctx.send(f"🧹 Deleted {len(deleted) - 1} messages.")
    await confirmation.delete(delay=3)  # auto-delete the confirmation after 3 seconds

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need the **Manage Messages** permission to use this command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Please provide a valid number. e.g. `!clear 10`")
#---------------------------------------------------------


#GUILD_ID = discord.Object(id=1411110776827019337)

#-------------------------STATUS ROTATION-------------------------------
STATUSES = [
    "Registering for classes... !help",
    "Serving coffee... ☕ !help",
    "Flipping coins... 🪙 !help",
    "Preparing for exams... 📚 !help"
]
status_cycle = itertools.cycle(STATUSES)

@tasks.loop(seconds=11) 
async def rotate_status():
    next_status = next(status_cycle)
    await bot.change_presence(activity=discord.Game(name=next_status))
#---------------------------------------------------------


#-------------------------READY--------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s) globally")
    except Exception as e:
        print(f"Sync failed: {e}")
    rotate_status.start()
bot.run(os.getenv("DISCORD_TOKEN"))
#---------------------------------------------------------