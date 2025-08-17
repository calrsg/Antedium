import discord
from discord.ext import commands
from discord import app_commands
import os

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(name="load", description="Load a cog.")
    async def load(self, ctx, extension):
        """
        Load a cog.

        Parameters
        ----------
        extension: str
            The name of the cog to load.
        """
        # awful fix for errors with unknown filenames
        load_success = False
        for filename in os.listdir("./cogs"):
            if f"{extension}.py" == filename:
                await self.bot.load_extension(f"cogs.{extension}")
                await ctx.send(f"**{extension}** loaded successfully")
                load_success = True
        if not load_success:
            await ctx.send(f"**{extension}** has *not* been loaded, please check cog name.")

    @commands.is_owner()
    @commands.command(name="unload", description="Unload a cog")
    async def unload(self, ctx, extension):
        """
        Unload a cog.

        Parameters
        ----------
        extension: str
            The name of the cog to unload.
        """
        # awful fix for errors with unknown filenames
        unload_success = False
        for filename in os.listdir("./cogs"):
            if f"{extension}.py" == filename:
                if filename == "admin.py":
                    await ctx.send(f"**admin** cannot be unloaded, only reloaded.")
                    return
                await self.bot.unload_extension(f"cogs.{extension}")
                await ctx.send(f"**{extension}** unloaded successfully")
                unload_success = True
        if not unload_success:
            await ctx.send(f"**{extension}** has *not* been unloaded, please check cog name.")

    @commands.is_owner()
    @commands.command(name="reload", description="Reload a cog.")
    async def reload(self, ctx, extension):
        """
        Reload a cog.

        Parameters
        ----------
        extension: str
            The name of the cog to reload.
        """
        # awful fix for errors with unknown filenames
        reload_success = False
        for filename in os.listdir("./cogs"):
            if f"{extension}.py" == filename:
                await self.bot.unload_extension(f"cogs.{extension}")
                await self.bot.load_extension(f"cogs.{extension}")
                await ctx.send(f"**{extension}** reloaded successfully")
                reload_success = True
        if not reload_success:
            await ctx.send(f"**{extension}** has *not* been reloaded, please check cog name.")

    @commands.is_owner()
    @commands.command(name="listcogs", description="List all cogs in the cogs folder.")
    async def listcogs(self, ctx):
        """
        List all cogs in the cogs folder.
        """
        cogs = []
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                cogs.append(filename)
        await ctx.send(f"Found the following cogs: {str(cogs)[1:-1]}")

    @commands.is_owner()
    @commands.command(name="countservers", description="Count the number of servers the bot is in.")
    async def countservers(self, ctx):
        """
        Count the number of servers the bot is in.
        """
        await ctx.send(f"Servers: {len(self.bot.guilds)}")

    @commands.is_owner()
    @commands.command(name="setstatus", description="Set the bot's status.")
    async def setstatus(self, ctx, *, status: str):
        """
        Set the bot's status.

        Parameters
        ----------
        status: str
            The new status for the bot, must be 128 characters or less.
        """
        # 128 current max length for status
        if len(status) > 128:
            await ctx.send("Status is too long, must be 128 characters or less.", ephemeral=True)
            return

        await self.bot.set_status(status)
        await ctx.send(f"Status set to '{status}'", ephemeral=True)

    @commands.is_owner()
    @commands.command(name="statuscount", description="Toggle the bot's status to display the total links fixed.")
    async def statuscount(self, ctx):
        """
        Toggle if the bot's status displays the total fixed links
        """
        self.bot.status_count = not self.bot.status_count
        await self.bot.set_status_count(self.bot.status_count)
        await ctx.send(f"{'Enabled' if self.bot.status_count else 'Disabled'}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))