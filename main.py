import discord
from discord.ext import commands
import os
import json

class Core(commands.Bot):

    intents = discord.Intents.default()

    # Required intents
    intents.message_content = True  # Needed to read message content for link detection
    intents.guilds = True  # Needed for server stats and guild info
    intents.members = False
    
    # Disabled to avoid performance degredation in large servers
    intents.presences = False 
    intents.typing = False
    intents.voice_states = False
    intents.webhooks = False
    intents.integrations = False
    intents.invites = False 

    member_cache_flags = discord.MemberCacheFlags.from_intents(intents)

    def __init__(self):
        self.discord_bot_token = ""
        self.discord_command_prefixes = ""
        self.current_status = ""
        self.status_count = False
        self.log_timer = 10
        self.load_config()
        allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=True)

        owners = [73389450113069056]
        super().__init__(command_prefix=self.discord_command_prefixes, case_insensitive=True,
                         intents=self.intents, owner_ids=set(owners), allowed_mentions=allowed_mentions, 
                         member_cache_flags=self.member_cache_flags, max_messages=1000)

    def load_config(self):
        try:
            with open("config.json") as file:
                contents = json.loads(file.read())

                dev = contents['discord']['dev']
                if dev:
                    self.discord_bot_token = contents['discord']['dev_bot_token']
                else:
                    self.discord_bot_token = contents['discord']['bot_token']
                self.discord_command_prefixes = contents['discord']['command_prefixes']
                self.current_status = contents['discord']['status']
                self.status_count = contents['discord']['status_count']
                self.log_timer = contents['discord']['log_timer']
                file.close()
                print("config loaded successfully.")

        except FileNotFoundError:
            with open("config.json", "w") as file:
                default_config = {
                    "discord": {
                        "dev_bot_token": "",
                        "bot_token": "",
                        "command_prefixes": ["!"],
                        "dev": True,
                        "status": "",
                        "status_count": False,
                        "log_timer": 60
                    }
                }
                json.dump(default_config, file, indent=4)
            print("config.json not found. A default config file has been created. Please fill in the bot_token field.")
            exit(1)

    async def on_ready(self):
        print("Bot initialised.")
        await self.startup()

    async def startup(self):
        print("Attempting to load cogs...")
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                # loads filename, removes last 3 characters (because load works with filename itself, not extension)
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"{filename} successfully loaded.")

        print("All cogs parsed.")

        await self.tree.sync()
        
        if not self.status_count:
            await self.change_presence(activity=discord.Game(name=self.current_status))
        print("Bot is ready.")

    async def set_status(self, status: str):
        self.current_status = status

        with open("config.json", "r") as file:
            contents = json.load(file)

        contents['discord']['status'] = status

        with open("config.json", "w") as file:
            json.dump(contents, file, indent=4)

        await self.change_presence(activity=discord.Game(name=self.current_status))

    async def set_status_count(self, status_count: bool):
        self.status_count = status_count

        with open("config.json", "r") as file:
            contents = json.load(file)

        contents['discord']['status_count'] = status_count

        with open("config.json", "w") as file:
            json.dump(contents, file, indent=4)

    def run(self):
        super().run(self.discord_bot_token)

if __name__ == "__main__":
    core = Core()
    core.run()


