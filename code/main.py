import discord
from discord.ext import commands
from openai import OpenAI
import json


# Buttons are broken for now.
"""
class DeleteButton(discord.ui.Button):
    def __init__(self, label, custom_id):
        super().__init__(label=label, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        delete_message()



class PardonButton(discord.ui.Button):
    def __init__(self, label, custom_id):
        super().__init__(label=label, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        await interaction.message.clear_reaction(emoji="⚠️")


class MyView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(DeleteButton(label="Delete message", custom_id="delete_message"))
        self.add_item(PardonButton(label="Pardon message", custom_id="pardon_message"))
"""


class Main:
    def __init__(self, ai_key, bot):
        self.status = discord.Game(name="Type !hello")
        self.client = OpenAI(api_key=ai_key)
        self.bot = bot

    async def get_flagged_categories(self, text):
        response = self.client.moderations.create(input=text)
        response_dict = response.model_dump()
        results = response_dict['results'][0]
        flagged_categories = {category: flagged for category, flagged in results['categories'].items() if flagged}
        return flagged_categories

    async def send_message(self, channel_id, *, message):
        channel = self.bot.get_channel(channel_id)
        embed = discord.Embed(description=message, color=discord.Color.red(), title="Harmful message")
        await channel.send(embed=embed)  # Send the embed


def setup_bot():
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix='!', intents=intents)
    ai_key = "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"

    main = Main(ai_key, bot)

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

        flagged_categories = await main.get_flagged_categories(text=message.content)
        if flagged_categories:
            await main.send_message(channel_id=1226672487966834778,
                                    message=f"Harmful message: {message.content}.\n"
                                            f"Category: {flagged_categories}.\n "
                                            f"Sent by: {message.author}.\n"
                                            f"Channel: {message.channel}.\n"
                                            f"Timespamp: {message.created_at}.")
            await message.add_reaction("⚠️")
        print(flagged_categories)
        await bot.process_commands(message)

        with open("nono_words.json", "r") as file:
            data = json.loads(file.read())
        for word in data:
            if word in (f"{message.content} "):
                await message.delete()
                await send_message(channel_id=999718985098600539,
                                   message=f"Harmful word: {word}.\n"
                                           f"Message: {message.content}.\n "
                                           f"Sent by: {message.author}.\n"
                                           f"Channel: {message.channel}.\n"
                                           f"Timespamp: {message.created_at}."
                                   )
                await message.channel.send(f"Please do not say vulgar things {message.author}")


    async def send_message(channel_id, message):
        channel = bot.get_channel(channel_id)
        embed = discord.Embed(description=message, color=discord.Color.red(), title="Harmful word in message")
        await channel.send(embed=embed)

    return bot


if __name__ == "__main__":
    bot = setup_bot()
    bot.run("OTc0NDc1MTYxOTI1NDU5OTk4.G6M3rx.sp4a_xyFDoJHws5hpGJ3w28pab9A-ETfNxOaRk")
