import os

import discord
from dotenv import load_dotenv
from discord.ext import commands

import localization as loc
from config import config
from utils.load_cogs import load_cogs


load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config['bot']['prefix'], help_command=None, intents=intents)


@bot.event
async def on_ready():
    await bot.cogs['Tickets'].init_func()
    
    p=config['bot']['prefix']
    name=config["bot"]["name"]

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(loc.gameActivity.replace("($p)", p)))
    print(f"[i] {name} {loc.onReady}\n")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        s=round(error.retry_after, 1)
        await ctx.reply(
            content=loc.commandOnCooldown.replace("($s)", str(s)))
    
    elif ctx.author.guild_permissions.administrator:
        p=config['bot']['prefix']
        await ctx.send(embed = discord.Embed(
            description=loc.commandNotFound.replace("($p)", p),
            color=config['color']['red']))
    
    elif isinstance(error, commands.MissingPermissions): pass


load_cogs(bot)
bot.run(TOKEN)