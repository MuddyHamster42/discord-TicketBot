import os
import json
import sqlite3
from time import time

import discord
from discord.ext import commands, tasks
from discord_components import DiscordComponents, Button, ButtonStyle

from config import config
import localization as loc


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
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS logs(
                    channel_id INT PRIMARY KEY);
            """)
            note = self.conn.execute("SELECT * FROM tickets_number").fetchone()
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

        if text == f'✉️ {loc.createTicket}':
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
                        if passed > 3600: passed = str(passed//3600)+f" {loc.hour}"
                        elif passed > 60: passed = str(passed//60)+f" {loc.minute}"
                        else: passed = str(passed)+f" {loc.second}"

                        await member.send(embed=discord.Embed(
                            title=loc.ticketCooldownTitle,
                            description=loc.ticketCooldownDescription.replace("($t)", passed),
                            color=config['color']['main']))
                        return

            self.conn.execute(f"UPDATE ticket_limit SET last_opened_at = {t} WHERE user_id = {member_id}")
            self.conn.commit()
            note = self.conn.execute("SELECT * FROM tickets_number ORDER BY ticket_id DESC").fetchone()
            num=note[0]+1
            self.conn.execute(f"UPDATE tickets_number SET ticket_id = {num} WHERE ticket_id = {note[0]}")
            self.conn.commit()

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=True),
                self.bot.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                member: discord.PermissionOverwrite(read_messages=True)
            }
            ch = await category.create_text_channel(f'{loc.ticket} №{num}', overwrites=overwrites)
            
            self.conn.execute("INSERT INTO tickets VALUES(?, ?, ?, ?, ?)", (num, member_id, ch.id, "None", 0))
            self.conn.commit()

            msg = await ch.send(
            embed = discord.Embed(
                title=loc.newTicketIsNowOpen.replace("($tnum)", str(num)),
                description=self.settings['tickets_text'],
                color=config['color']['main']),
                    components = [[
                        Button(style=ButtonStyle.blue, label=f'🔒 {loc.closeTicket}'),
                        Button(style=ButtonStyle.blue, label=f'🔓 {loc.openTicket}', disabled=True),
                        Button(style=ButtonStyle.red, label=f'⚠️ {loc.deleteTicket}')
                    ]])

            await msg.pin()
            msg = await ch.history(limit=1).flatten()
            await msg[0].delete()

        elif text == f'🔒 {loc.closeTicket}':
            note = self.conn.execute(f"SELECT * FROM tickets WHERE ch_id = {channel.id}").fetchone()
            closed = note[4]
            if closed: return
            overwrites = channel.overwrites_for(guild.default_role)
            overwrites.send_messages = False
            await channel.set_permissions(guild.default_role, overwrite=overwrites)

            embed=discord.Embed(
                title=loc.ticketIsNowClosedTitle,
                description=loc.ticketIsNowClosedDescription,
                color=config['color']['red'])
            embed.set_author(name=member, icon_url=member.avatar_url)
            await channel.send(embed=embed)

            self.conn.execute(f"UPDATE tickets SET closed = 1 WHERE ch_id = {channel.id}")
            self.conn.commit()

            await res.message.edit(
            embed = discord.Embed(
                title=loc.newTicketIsNowClosed.replace("($tnum)", str(note[0])),
                description=self.settings['tickets_text'],
                color=config['color']['main']),
                    components = [[
                        Button(style=ButtonStyle.blue, label=f'🔒 {loc.closeTicket}', disabled=True),
                        Button(style=ButtonStyle.blue, label=f'🔓 {loc.openTicket}', disabled=False),
                        Button(style=ButtonStyle.red, label=f'⚠️ {loc.deleteTicket}')
                    ]])

            note = self.conn.execute("SELECT * FROM logs").fetchone()
            tnum = self.conn.execute("SELECT * FROM tickets_number").fetchone()
            if note is not None:
                try:
                    log_ch = self.bot.get_channel(note[0])

                    embed = discord.Embed(
                        title=loc.newTicketIsNowClosed.replace("($tnum)", str(tnum[0])),
                        color=config['color']['main'])
                    embed.set_author(name=member, icon_url=member.avatar_url)

                    await log_ch.send(embed=embed)
                    
                except Exception as e:
                    print("[x] Logs error (ticket close):", e)

        elif text == f'🔓 {loc.openTicket}':
            if not member.guild_permissions.administrator: return
            note = self.conn.execute(f"SELECT * FROM tickets WHERE ch_id = {channel.id}").fetchone()
            closed = note[4]
            if not closed: return

            overwrites = channel.overwrites_for(guild.default_role)
            overwrites.send_messages = True
            await channel.set_permissions(guild.default_role, overwrite=overwrites)

            embed=discord.Embed(
                title=loc.ticketIsNowOpen,
                color=config['color']['lime'])
            embed.set_author(name=member, icon_url=member.avatar_url)
            await channel.send(embed=embed)
            self.conn.execute(f"UPDATE tickets SET closed = 0 WHERE ch_id = {channel.id}")
            self.conn.commit()

            await res.message.edit(
            embed = discord.Embed(
                title=loc.newTicketIsNowOpen.replace("($tnum)", str(note[0])),
                description=self.settings['tickets_text'],
                color=config['color']['main']),
                    components = [[
                        Button(style=ButtonStyle.blue, label=f'🔒 {loc.closeTicket}', disabled=False),
                        Button(style=ButtonStyle.blue, label=f'🔓 {loc.openTicket}', disabled=True),
                        Button(style=ButtonStyle.red, label=f'⚠️ {loc.deleteTicket}')
                    ]])

        elif text == f'⚠️ {loc.deleteTicket}':
            if not member.guild_permissions.administrator: return
            await channel.delete()
            self.conn.execute(f"DELETE FROM tickets WHERE ch_id = {channel.id}")
            self.conn.commit()

            note = self.conn.execute("SELECT * FROM logs").fetchone()
            tnum = self.conn.execute("SELECT * FROM tickets_number").fetchone()
            if note is not None:
                try:
                    log_ch = self.bot.get_channel(note[0])

                    embed = discord.Embed(
                        title=loc.ticketIsNowDeleted.replace("($tnum)", str(tnum[0])),
                        color=config['color']['red'])
                    embed.set_author(name=member, icon_url=member.avatar_url)

                    await log_ch.send(embed=embed)
                    
                except Exception as e:
                    print("[x] Logs error (ticket delete):", e)

        elif text == loc.joinTheTicket:
            t_num = res.component.custom_id
            note = self.conn.execute(f"SELECT * FROM tickets WHERE ticket_id = {t_num}").fetchone()
            
            if note is None:
                await member.send(embed=discord.Embed(
                    title=loc.oops,
                    description=loc.ticketNoLongerExist,
                    color=config['color']['red']))
                return
            
            if str(member.id) in note[3].split():
                await member.send(embed=discord.Embed(
                    title=loc.alreadyJoined,
                    color=config['color']['red']))
                return
            
            if note[4] == 1:
                await member.send(embed=discord.Embed(
                    title=loc.ticketIsClosedTitle,
                    description=loc.ticketIsClosedDescription,
                    color=config['color']['red']))
                return
            
            t_channel = self.bot.get_channel(note[2])
            overwrites = t_channel.overwrites_for(member)
            overwrites.read_messages = True
            await t_channel.set_permissions(member, overwrite=overwrites)
            await member.send(embed=discord.Embed(
                title=loc.ticketIsNowAvailable.replace("($tnum)", {note[0]}),
                color=config['color']['gray']))

            embed=discord.Embed(
                description=loc.userHasJoined,
                color=config['color']['lime'])
            embed.set_author(
                name=member,
                icon_url=member.avatar_url)
            await t_channel.send(embed=embed)

            if note[3] == "None": users = str(member.id)
            else: users = note[3]+" "+str(member.id)
            self.conn.execute(f"DELETE FROM tickets WHERE ch_id = {note[2]}")
            self.conn.execute(f"INSERT INTO tickets VALUES(?, ?, ?, ?, ?)", (note[0], note[1], note[2], users, note[4]))
            self.conn.commit()
        
        elif text == loc.refuse:
            t_num = int(str(res.component.custom_id)[:-1])
            note = self.conn.execute(f"SELECT * FROM tickets WHERE ticket_id = {t_num}").fetchone()
            if note is None: pass
            else:
                t_channel = self.bot.get_channel(note[2])
                embed=discord.Embed(description=loc.userRefusedToJoin, color=config['color']['gray'])
                embed.set_author(name=member, icon_url=member.avatar_url)
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
            
        await ctx.send(embed = discord.Embed(
            title=loc.textHasBeenChanged,
            color=config['color']['lime']))

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
                Button(style=ButtonStyle.blue, label=f'✉️ {loc.createTicket}')
            ]])

    @commands.command(aliases=['ti'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ticket_invite(self, ctx):
        num = ctx.message.content.split()
        num = num[1]
        note = self.conn.execute(f"SELECT * FROM tickets WHERE ticket_id = {num}").fetchone()
        if note is None or (note[1] != ctx.author.id and not ctx.author.guild_permissions.administrator):
            await ctx.send(embed=discord.Embed(
                title=loc.somethingsWrong,
                description=loc.incorrectTicketNumber,
                color=config['color']['red']))
            return

        for member in ctx.message.mentions:
            try:
                embed=discord.Embed(
                    title=loc.uInvitedToTicketTitle.replace("($tnum)", note[0]),
                    description=loc.uInvitedToTicketDescription,
                    color=config['color']['main'])
                embed.set_author(name=ctx.author, icon_url=str(ctx.author.avatar_url))

                await member.send(embed=embed,
                    components = [[
                        Button(style=ButtonStyle.blue, label=loc.joinTheTicket, custom_id=note[0]),
                        Button(style=ButtonStyle.red, label=loc.refuse, custom_id=int(str(note[0])+"0"))
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

        await ctx.send(embed = discord.Embed(
            title=loc.cooldownChanged,
            color=config['color']['lime']))

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
        await ctx.send(embed=discord.Embed(
            title=loc.cooldownReset,
            color=config['color']['lime']))

    @commands.command(aliases=['slc'])
    @commands.cooldown(1, 6, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def set_logs_channel(self, ctx):
        channel = ctx.message.content.split()[1]
        channel = channel.replace("<", "")
        channel = channel.replace("#", "")
        channel = channel.replace(">", "")

        if channel == "None":
            self.conn.execute("DELETE FROM logs")
            self.conn.commit()
            await ctx.send(embed = discord.Embed(
                title=loc.setLogsNone,
                color=config['color']['lime']))
            return

        try: ch_obj = self.bot.get_channel(int(channel))
        except: ch_obj = None
        if ch_obj is None:
            await ctx.send(embed = discord.Embed(
                title=loc.setLogsWrongChannel,
                color=config['color']['red']))
            return

        note = self.conn.execute("SELECT * FROM logs").fetchone()
        if note is None:
            self.conn.execute("INSERT INTO logs VALUES(?)", (ch_obj.id,))
        else:
            self.conn.execute(f"UPDATE logs SET channel_id = {ch_obj.id}")
        self.conn.commit()
        note = self.conn.execute("SELECT * FROM logs").fetchone()

        await ctx.send(embed = discord.Embed(
            title=loc.setLogsSuccess,
            color=config['color']['lime']))


def setup(bot):
    bot.add_cog(Tickets(bot))