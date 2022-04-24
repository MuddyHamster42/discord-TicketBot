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
        self.cogs_folder = os.path.dirname(__file__)
        self.main_folder = os.path.dirname(self.cogs_folder)

        DiscordComponents(self.bot)
        self.button_detect.start()

    # ======================================= #

    async def init_func(self):
        self.conn = sqlite3.connect(f'{self.main_folder}/data.db')
        self.cur = self.conn.cursor()
        with self.conn:
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS tickets(
                    ticket_id INT PRIMARY KEY,
                    owner_id INT,
                    ch_id INT,
                    users TEXT,
                    closed INT);
            """)
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS tickets_number(
                    ticket_id INT PRIMARY KEY);
            """)
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS ticket_limit(
                    user_id INT PRIMARY KEY,
                    last_opened_at INT);
            """)
            note = self.conn.execute("SELECT * FROM tickets_number ORDER BY ticket_id DESC").fetchone()
            if note is None:
                self.conn.execute("INSERT INTO tickets_number VALUES(?)", (0,))
                self.conn.commit()
        self.conn.commit()

        file = os.path.join(self.main_folder, "settings.json")
        with open(file, "r", encoding='utf8') as read_file:
            self.settings = json.load(read_file)

    @tasks.loop(seconds=1)
    async def button_detect(self):
        res = await self.bot.wait_for('button_click')
        try: await res.respond()
        except: pass
        
        try: guild = res.author.guild
        except: pass
        channel = res.channel
        try: category = channel.category
        except: pass
        member_id = res.author.id
        member = res.author
        text = res.component.label

        if text == '✉️ Создать тикет':
            note = self.conn.execute(f"SELECT * FROM ticket_limit WHERE user_id = {member_id}").fetchone()
            t = int(time())
            if note is None:
                self.conn.execute("INSERT INTO ticket_limit VALUES(?, ?)", (member_id, t))
                self.conn.commit()
            elif note is not None:
                if not member.guild_permissions.administrator:
                    passed = int(time())-int(note[1])
                    if passed < self.settings['ticket_limit']:
                        passed = self.settings['ticket_limit'] - passed
                        if passed > 3600: passed = str(passed//3600)+" ч."
                        elif passed > 60: passed = str(passed//60)+" мин."
                        else: passed = str(passed)+" сек."
                        await member.send(embed = discord.Embed(title="Вы создаете тикеты слишком часто!", description=f"Подождите {passed} или напишите администратору.", color=config['color']['main']))
                        return
            self.conn.execute(f"UPDATE ticket_limit SET last_opened_at = {t} WHERE user_id = {member_id}")
            self.conn.commit()
            note = self.conn.execute("SELECT * FROM tickets_number ORDER BY ticket_id DESC").fetchone()
            num=note[0]+1
            self.conn.execute(f"UPDATE tickets_number SET ticket_id = {num} WHERE ticket_id = {note[0]}")
            self.conn.commit()

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                member: discord.PermissionOverwrite(read_messages=True)
            }
            ch = await category.create_text_channel(f'Тикет №{num}', overwrites=overwrites)
            self.conn.execute("INSERT INTO tickets VALUES(?, ?, ?, ?, ?)", (num, member_id, ch.id, "None", 0))
            self.conn.commit()

            msg = await ch.send(
            embed = discord.Embed(title=f"Тикет №{num} открыт.", description=self.settings['tickets_text'], color=config['color']['main']),
            components = [[
                Button(style=ButtonStyle.blue, label='🔒 Закрыть тикет'),
                Button(style=ButtonStyle.blue, label='🔓 Открыть тикет'),
                Button(style=ButtonStyle.red, label='⚠️ Удалить тикет')
            ]])
            await msg.pin()
            msg = await ch.history(limit=1).flatten()
            await msg[0].delete()

        elif text == '🔒 Закрыть тикет':
            closed = self.conn.execute(f"SELECT closed FROM tickets WHERE ch_id = {channel.id}").fetchone()
            if closed[0]: return
            overwrites = channel.overwrites_for(guild.default_role)
            overwrites.send_messages = False
            await channel.set_permissions(guild.default_role, overwrite=overwrites)

            embed=discord.Embed(title=f"Тикет закрыт.", description="Он все еще доступен для просмотра, но без возможности отправки сообщений.\nАдминистрация может удалить тикет в закрепленном сообщении.", color=config['color']['red'])
            embed.set_author(name=member, icon_url=str(member.avatar_url))
            await channel.send(embed=embed)
            self.conn.execute(f"UPDATE tickets SET closed = 1 WHERE ch_id = {channel.id}")
            self.conn.commit()

        elif text == '🔓 Открыть тикет':
            if not member.guild_permissions.administrator: return
            closed = self.conn.execute(f"SELECT closed FROM tickets WHERE ch_id = {channel.id}").fetchone()
            if not closed[0]: return

            overwrites = channel.overwrites_for(guild.default_role)
            overwrites.send_messages = True
            await channel.set_permissions(guild.default_role, overwrite=overwrites)

            embed=discord.Embed(title=f"Тикет снова открыт.", color=config['color']['lime'])
            embed.set_author(name=member, icon_url=str(member.avatar_url))
            await channel.send(embed=embed)
            self.conn.execute(f"UPDATE tickets SET closed = 0 WHERE ch_id = {channel.id}")
            self.conn.commit()

        elif text == '⚠️ Удалить тикет':
            if not member.guild_permissions.administrator: return
            await channel.delete()
            self.conn.execute(f"DELETE FROM tickets WHERE ch_id = {channel.id}")
            self.conn.commit()

        elif text == 'Присоединиться':
            t_num = res.component.custom_id
            note = self.conn.execute(f"SELECT * FROM tickets WHERE ticket_id = {t_num}").fetchone()
            if note is None:
                await member.send(embed=discord.Embed(title="Упс...", description="Похоже, что этот тикет больше не существует.", color=config['color']['red']))
                return
            if str(member.id) in note[3].split():
                await member.send(embed=discord.Embed(title="Вы уже присоединились.", color=config['color']['red']))
                return
            if note[4] == 1:
                await member.send(embed=discord.Embed(title="Этот тикет закрыт.", description="Чтобы присоединиться - попросите администрацию его открыть.", color=config['color']['red']))
                return
            t_channel = self.bot.get_channel(note[2])
            overwrites = t_channel.overwrites_for(member)
            overwrites.read_messages = True
            await t_channel.set_permissions(member, overwrite=overwrites)
            await member.send(embed=discord.Embed(title=f"Теперь вам доступен канал тикета №{note[0]}.", color=config['color']['gray']))

            if note[3] == "None": users = str(member.id)
            else: users = note[3]+" "+str(member.id)
            self.conn.execute(f"DELETE FROM tickets WHERE ch_id = {note[2]}")
            self.conn.execute(f"INSERT INTO tickets VALUES(?, ?, ?, ?, ?)", (note[0], note[1], note[2], users, note[4]))
            self.conn.commit()
        
        elif text == 'Отказаться':
            t_num = int(str(res.component.custom_id)[:-1])
            note = self.conn.execute(f"SELECT * FROM tickets WHERE ticket_id = {t_num}").fetchone()
            if note is None: pass
            else:
                t_channel = self.bot.get_channel(note[2])
                embed=discord.Embed(description=f"Пользователь отказался присоединяться к тикету.", color=config['color']['gray'])
                embed.set_author(name=member, icon_url=str(member.avatar_url))
                await t_channel.send(embed=embed)
            await res.message.delete()


    # ======================================= #

    @commands.command(aliases=['tt'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def ticket_text(self, ctx):
        message = await ctx.channel.history(limit=2).flatten()
        message = message[1].content
        self.settings['tickets_text'] = message
        file = os.path.join(self.main_folder, "settings.json")
        with open(file, 'w', encoding='utf8') as write_file:
            json.dump(self.settings, write_file)
        await ctx.send(embed = discord.Embed(title="Текст успешно изменен.", color=config['color']['lime']))

    @commands.command(aliases=['tb'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def ticket_button(self, ctx):
        args = ctx.message.content.split()
        args.pop(0)
        channel=args[0]
        channel=channel.replace("<","")
        channel=channel.replace("#","")
        channel=channel.replace(">","")
        channel = self.bot.get_channel(int(channel))
        message = await ctx.channel.history(limit=2).flatten()
        message = message[1].content
        color = config['color']['main']
        await channel.send(
            embed = discord.Embed(description=message, color=color),
            components = [[
                Button(style=ButtonStyle.blue, label='✉️ Создать тикет')
            ]])

    @commands.command(aliases=['ti'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ticket_invite(self, ctx):
        num = ctx.message.content.split()
        num = num[1]
        note = self.conn.execute(f"SELECT * FROM tickets WHERE ticket_id = {num}").fetchone()
        if note is None or (note[1] != ctx.author.id and not ctx.author.guild_permissions.administrator):
            await ctx.send(embed=discord.Embed(title="Что-то не так....", description="Вы ввели неправильный номер тикета или этот тикет открыт не вами.\nПример исползования команды: `%ti 34 @user1 @user2`", color=config['color']['red']))
            return

        for member in ctx.message.mentions:
            try:
                embed=discord.Embed(title=f"Вы были приглашены в тикет №{note[0]}", description="Если вы хотите к нему присоединиться - нажмите на соответсвующую кнопку под этим сообщением:", color=config['color']['main'])
                embed.set_author(name=ctx.author, icon_url=str(ctx.author.avatar_url))
                await member.send(embed=embed,
                components = [[
                    Button(style=ButtonStyle.blue, label='Присоединиться', custom_id=note[0]),
                    Button(style=ButtonStyle.red, label='Отказаться', custom_id=int(str(note[0])+"0"))
                ]])
            except: pass
        
    @commands.command(aliases=['tc'])
    @commands.cooldown(1, 6, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def ticket_cooldown(self, ctx):
        arg = ctx.message.content.split()
        arg = int(arg[1])
        self.settings['ticket_limit'] = arg
        file = os.path.join(self.main_folder, "settings.json")
        with open(file, 'w', encoding='utf8') as write_file:
            json.dump(self.settings, write_file)
        await ctx.send(embed = discord.Embed(title="Кулдаун успешно изменен.", color=config['color']['lime']))

    @commands.command(aliases=['tr'])
    @commands.cooldown(1, 6, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def ticket_reset(self, ctx):
        arg = ctx.message.content.split()
        arg = arg[1]
        if arg == "everyone":
            self.conn.execute("DELETE FROM ticket_limit")
            self.conn.commit()
        else:
            for member in ctx.message.mentions:
                self.conn.execute(f"DELETE FROM ticket_limit WHERE user_id = {member.id}")
            self.conn.commit()
        await ctx.send(embed=discord.Embed(title="Куладун успешно сброшен", color=config['color']['lime']))


def setup(bot):
    bot.add_cog(Tickets(bot))