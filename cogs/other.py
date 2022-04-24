from config import config
import discord
from discord.ext import commands, tasks
from discord_components import DiscordComponents, Button, ButtonStyle
import sqlite3
import os
from time import time
import json


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ======================================= #

    @commands.command(aliases=['h'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def help(self, ctx):
        p=config['bot']['prefix']
        msg = (
            f"**{p}ticket_invite** `[N]` `[@users]` ({p}ti) - Приглашает в тикет `N` упомянутых участников."
            f"\n\n[adm] **{p}ticket_button** `[#channel]` ({p}tb) - Создать кнопку, с текстом из прошлого сообщения в чате, в канале #channel."
            f"\n\n[adm] **{p}ticket_text** ({p}tt) - Меняет стандартный текст в каждом тикете на текст из прошлого сообщения."
            f"\n\n[adm] **{p}ticket_cooldown** `[seconds]` ({p}tc) - Меняет куладун на создание новых тикетов."
            f"\n\n[adm] **{p}ticket_reset** `[everyone/@users]` ({p}tr) - Обнуляет кулдаун создания тектов для конкретных пользователей, или для всех (everyone)."
        )
        await ctx.send(embed = discord.Embed(title = "Список команд:", description = msg, color=config['color']['main']))


def setup(bot):
    bot.add_cog(Tickets(bot))
