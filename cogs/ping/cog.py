# Nextcord:
import nextcord
from nextcord.ext import commands

# The class to create the cog:
class Ping(commands.Cog):
    
    # Create a command:
    @commands.command()
    async def ping(self, ctx):
        await ctx.reply("Pong!")

# Function to load cog
def setup(bot):
    # Add the cog
    bot.add_cog(Ping(bot))