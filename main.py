import discord
from discord.ext import commands
import os
import json

class Core(commands.Bot):

    intents = discord.Intents.default()

    intents.message_content = True
    intents.members = False
    intents.presences = False

    member_cache_flags = discord.MemberCacheFlags.none()

    def __init__(self):
        self.discord_bot_token = ""
        self.discord_command_prefixes = ["!"]
        self.load_config()
        allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=True)

        owners = [73389450113069056]
        super().__init__(command_prefix=self.discord_command_prefixes, case_insensitive=True,
                         intents=self.intents, owner_ids=set(owners), allowed_mentions=allowed_mentions, 
                         member_cache_flags=self.member_cache_flags, chunk_guilds_at_startup=False, max_messages=1000)

    def load_config(self):
        with open("config.json") as file:
            contents = json.loads(file.read())
            dev = contents['dev']
            if dev:
                self.discord_bot_token = contents['discord']['dev_bot_token']
            else:
                self.discord_bot_token = contents['discord']['bot_token']
            self.discord_command_prefixes = contents['discord']['command_prefixes']
            file.close()

    async def on_ready(self):
        print("Bot initialised.")
        await self.startup()
        await self.change_presence(activity=discord.Game(name=f"Tidying up 🧹"))

    async def startup(self):
        print("Attempting to load cogs...")
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                # loads filename, removes last 3 characters (because load works with filename itself, not extension)
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"{filename} successfully loaded.")

        print("All cogs parsed.")
        await self.tree.sync()

    def run(self):
        super().run(self.discord_bot_token)


if __name__ == "__main__":
    core = Core()
    core.run()


