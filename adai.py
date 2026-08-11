# adai.py



#---------------------------------------------------------
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import random
import asyncio

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True   # add this line
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
#---------------------------------------------------------

#-------------------------PING--------------------------------
@bot.command()
async def ping(ctx):
    await ctx.send("Pongg!!")

NOT_IN_UNI_ROLE = "Outsider"
SCHOOL_ROLES = ["SITE", "SPIA", "Law", "SDA", "SAFS", "Business"]
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
        "`!coinflip` / `!cf` — Flip a coin"
    ), inline=False)
    embed.add_field(name="🛡️ Moderation", value=(
        "`!clear <amount>` — Delete messages (requires Manage Messages)"
    ), inline=False)
    embed.add_field(name="⚙️ Utility", value=(
        "`!ping` — Check if I'm alive\n"
        "`!help` / `/help` — Show this menu"
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




#-------------------------QUOTE-----------------------------------
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
    
    await ctx.send(f'"{text}"\n— {author.display_name}')
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


#-------------------------READY--------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s) globally")
    except Exception as e:
        print(f"Sync failed: {e}")
bot.run(os.getenv("DISCORD_TOKEN"))
#---------------------------------------------------------