import discord
from discord import app_commands
from discord.ext import commands

from linkhandlers.healthreport import (DOWN, KNOWN_OUTAGE, PARTIAL, UNCHECKED, WORKING,
                                       load_report, provider_status, results_dir)
from linkhandlers.rewrite import default_handlers

MARKS = {WORKING: "✅", DOWN: "❌", PARTIAL: "⚠️", KNOWN_OUTAGE: "⚠️", UNCHECKED: "❔"}


class Providers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="providers", description="Check which embed providers are working.")
    async def providers(self, interaction: discord.Interaction):
        """
        Show each platform's current embed provider and whether the latest
        provider health checks found it working.
        """
        report = load_report(results_dir())
        if report is None:
            lines = ["**Embed providers**, not checked yet"]
        else:
            stale = " (stale)" if report.stale() else ""
            lines = [f"**Embed providers**, last checked <t:{int(report.checked_at.timestamp())}:R>{stale}"]
        for handler in default_handlers():
            status = provider_status(handler, report)
            note = f", {status.note}" if status.note else ""
            lines.append(f"{MARKS[status.state]} **{status.handler}** `{status.provider}`: {status.state}{note}")
        await interaction.response.send_message("\n".join(lines))


async def setup(bot):
    await bot.add_cog(Providers(bot))
