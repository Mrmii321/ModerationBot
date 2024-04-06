import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

class Main:
    def __init__(self, ai_key):
        self.status = discord.Game(name="Type !hello")
        self.client = OpenAI(api_key=ai_key)

    async def get_flagged_categories(self, text):
        response = self.client.moderations.create(input=text)
        response_dict = response.model_dump()
        results = response_dict['results'][0]
        flagged_categories = {category: flagged for category, flagged in results['categories'].items() if flagged}
        return flagged_categories

def setup_bot():
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix='!', intents=intents)
    ai_key = os.getenv("OPENAI_API_KEY")

    main = Main(ai_key)

    @bot.event
    async def on_ready():
        """Logs in the bot."""
        print(f'Logged in as {bot.user.name}')
        await bot.change_presence(activity=main.status)

    @bot.event
    async def on_message(message):
        """Handles incoming messages."""
        if message.author == bot.user:
            return

        flagged_categories = await main.get_flagged_categories(text=message.content)  # Process the message
        print(flagged_categories)  # Assuming you want to print the flagged categories for debugging
        await bot.process_commands(message)  # Needed for command handling

    return bot

if __name__ == "__main__":
    bot_token = os.getenv("BOT_TOKEN")
    bot = setup_bot()
    bot.run(bot_token)
