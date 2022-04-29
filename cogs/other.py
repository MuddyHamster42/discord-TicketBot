import localization as loc
import discord

from config import config
from discord.ext import commands


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ======================================= #

    @commands.command(aliases=['h'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def help(self, ctx):
        p=config['bot']['prefix']

        common_commands=(
            f"**{p}ticket_invite** [t] [*@user] ({p}ti)"
            f"\n```\n{loc.h_ticketInvite}```"
            
            f"\n**{p}help** ({p}h)"
            f"\n```\n{loc.h_help}```"
            )
            
        embed = discord.Embed(
            description=common_commands,
            color=config['color']['main'])

        await ctx.send(loc.h_helpTitle, embed=embed)

    @commands.command(aliases=['ha'])
    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def help_adm(self, ctx):
        p=config['bot']['prefix']

        admin_commands=(
            f"**{p}ticket_button** [#channel] (%tb)"
            f"\n```\n{loc.h_ticketButton}```"
            
            f"\n**{p}ticket_text** (%tt)"
            f"\n```\n{loc.h_ticketText}```"
            
            f"\n**{p}ticket_cooldown** [seconds] (%tc)"
            f"\n```\n{loc.h_ticketCooldown}```"

            f"\n**{p}ticket_reset** [*@user] (%tr)"
            f"\n```\n{loc.h_ticketReset}```"

            f"\n**{p}set_logs_channel** [#channel/None] (%slc)"
            f"\n```\n{loc.h_setLogsChannel}```"

            f"\n**{p}help_adm** (%ha)"
            f"\n```\n{loc.h_helpAdm}```")

        embed = discord.Embed(
            description=admin_commands,
            color=config['color']['main'])

        await ctx.send(loc.h_helpAdminTitle, embed=embed)


def setup(bot):
    bot.add_cog(Tickets(bot))
