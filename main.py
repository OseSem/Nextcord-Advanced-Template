# Nextcord
import nextcord
from nextcord.ext import commands

# File imports
from botconfig import botconfig

# Standard libraries
import os

class Bot(commands.Bot):
    def __init__(self):
        self.config = botconfig
        self.clean_prefix = botconfig.config("prefix")

        super().__init__(
            command_prefix = botconfig.config("prefix"),
            description = botconfig.config("description"),
            owner_ids = botconfig.config("prefix")
        )
    # Run when the bot is ready.
    async def on_ready(self):
        print("Ready!")
    
    # Run when its connected to discord.
    async def on_connect(self):
        print("Running Setup...")
        self.remove_command("Help")
        for folder in os.listdir("cogs"):
            if os.path.exists(os.path.join("cogs", folder, "cog.py")):
                self.load_extension(f"cogs.{folder}.cog")
                print(f" Loaded cog {folder.title()}")
        status1 = self.config.config('prefix') + "help"
        status = f"{status1} | {len(self.guilds)} Guilds"
        await self.change_presence(status = nextcord.Status.idle, activity = nextcord.Game(status))
        print("Setup ran.")
        print("Logged in to discord!")
    
    def run(self):
        super().run(botconfig.token())

bot = Bot()

if __name__ == "__main__":
    bot.run()