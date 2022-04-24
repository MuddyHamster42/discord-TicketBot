from config import config
from utils.load_cogs import load_cogs
import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config['bot']['prefix'], help_command=None, intents=intents)

# ======================================= #


@bot.event
async def on_ready():
    await bot.cogs['Tickets'].init_func()

    await bot.change_presence(status=discord.Status.online)
    print(f"[i] "+config["bot"]["name"]+" готов к работе!\n")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        s=round(error.retry_after, 1)
        await ctx.reply(content=f"Подождите **__{s}__**с. перед тем как использовать команду еще раз.")
    elif isinstance(error, commands.MissingPermissions): return
    elif ctx.author.guild_permissions.administrator:
        p=config['bot']['prefix']
        await ctx.send(embed = discord.Embed(description = f"Команда не распознана. Используйте **__{p}help__** или проверьте синтаксис.", color=config['color']['red']))
    if ctx.author.guild_permissions.administrator:
        print("[-] "+str(error))


# ======================================= #

load_cogs(bot)
bot.run(config['bot']['token'])