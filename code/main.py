import json
import logging
import time
import discord
from discord.ext import commands, tasks
from openai import OpenAI
from spreadsheeter import spreadsheeter
from database import database
from sensitiveVariables import sensitiveVariables


sensitivevariables = sensitiveVariables.SensitiveVariables()
spreadsheeter = spreadsheeter.Spreadsheeter()
database = database.MariaDB()
staff_roles = sensitivevariables.staff_roles


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.StreamHandler()
])
logger = logging.getLogger(__name__)
# Setting the logger


class Main:
    def __init__(self, ai_key, bot_class_var):
        self.status = discord.Activity(type=discord.ActivityType.watching, name="for =help", start=0)
        # start=0 is the timestamp for when activity starts
        self.client = OpenAI(api_key=ai_key)
        self.bot = bot_class_var

    async def get_flagged_categories(self, text):
        response = self.client.moderations.create(input=text)
        response_dict = response.model_dump()
        results = response_dict['results'][0]
        flagged_categories = {category: flagged for category, flagged in results['categories'].items() if flagged}
        logging.info(f"Checked text {text}")
        return flagged_categories

    async def send_message(self, channel_id, *, message):
        channel = self.bot.get_channel(channel_id)
        embed = discord.Embed(description=message, color=discord.Color.red(), title="Harmful message")
        await channel.send(embed=embed)  # Send the embed
        logging.info(f"Created Embed for harmful message {message}")

    async def send_message_dm(self, *, message, author):
        embed = discord.Embed(description=message, color=discord.Color.red(), title="Vulgar message")
        await author.send(embed=embed)  # Send the embed
        logging.info(f"Created Embed for harmful message {message}")


def setup_bot():
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix='==', intents=intents)
    bypass_roles = ["Owner", "Admin", "General Manager", "Community manager", "Staff manager",
                    "Events Manager", "Consultant", "Senior Moderator"]
    debug_role = ["bot debug perms"]
    start_time = int(time.time())

    main = Main(sensitivevariables.OPENAI_key, bot)



    @bot.event
    async def on_ready():
        """Logs in the bot."""
        tybalt_logs = bot.get_channel(982548416376750100)
        logging.info(f"Logged in as {bot.user.name}")
        await bot.change_presence(activity=main.status)
        message = (
            f"AutoMod started up at <t:{start_time}>"
        )
        embed = discord.Embed(description=message, color=discord.Color.green(), title="**AutoMod Online**")
        await tybalt_logs.send(embed=embed)
        check_for_spammers.start()
        logging.info("Started spammer check")



    @bot.event
    async def on_message(message):
        """Handles incoming messages."""
        if message.author.bot:
            return
        user_roles = [role.name for role in message.author.roles]

        if not any(role in user_roles for role in bypass_roles) or any(role in user_roles for role in debug_role):
            if message.author == bot.user:
                return

            """Part for AI mod"""

            flagged_categories = await main.get_flagged_categories(text=message.content)
            if flagged_categories:
                await main.send_message(channel_id=1226672487966834778,
                                        message=f"Harmful message: {message.content}.\n"
                                                f"Category: {flagged_categories}.\n "
                                                f"Sent by: {message.author}.\n"
                                                f"Channel: {message.channel}.\n"
                                                f"Timespamp: {message.created_at}.")
                logging.info(f"User {message.author} has been privately messaged about their vulgar message")
                await message.add_reaction("⚠️")
                key = list(flagged_categories.keys())[0]
                database.log_ai(message=message.content,
                                author=message.author,
                                channel=message.channel,
                                time_sent=message.created_at,
                                flags=key.strip("''"))

            """Part for bad words list"""

            with open("nono_words.json", "r") as file:
                data = json.loads(file.read())
            words = message.content.split()
            for word in data:
                if word in words:
                    logging.info(f"Bad word ({word}) detected")
                    await send_message(channel_id=999718985098600539,
                                       message=f"Harmful word: {word}.\n"
                                               f"Message: {message.content}.\n "
                                               f"Sent by: {message.author}.\n"
                                               f"Channel: {message.channel}.\n"
                                               f"Timespamp: {message.created_at}."
                                       )
                    await message.channel.send(f"Please do not say vulgar things {message.author.mention}")
                    database.log_filter(message=message.content,
                                        author=message.author,
                                        channel=message.channel,
                                        time_sent=message.created_at,
                                        harmful_word=word)
                    await message.delete()

        else:
            logging.info(f"Message sent by {message.author} was ignored through senior staff status")
            await bot.process_commands(message)


    @tasks.loop(hours=1)
    async def check_for_spammers(manual):
        if manual:
            logging.info("Started spammer check manually")
        else:
            logging.info("Started spammer check automatically")
        guild_id = bot.get_guild(272148882048155649)
        channel = bot.get_channel(1239179624689434716)
        members = guild_id.members
        for member in members:

            if member.public_flags.spammer:
                message = (
                    f"User {member.mention} has been flagged as suspicious."
                )
                embed = discord.Embed(description=message, color=discord.Color.red(), title="**Suspicious Account**")

                await channel.send(embed=embed)
                logging.info(f"User {member.name} has been flagged as potential spammer.")


    async def send_message(channel_id, message):
        channel = bot.get_channel(channel_id)
        embed = discord.Embed(description=message, color=discord.Color.red(), title="Harmful word in message")
        await channel.send(embed=embed)


    @bot.event
    async def on_member_update(before, after):
        if before.roles != after.roles:
            old_roles = set(before.roles)
            new_roles = set(after.roles)

            added_roles = new_roles - old_roles
            removed_roles = old_roles - new_roles

            user = after.name

            for role in added_roles:
                for role_key, role_value in staff_roles.items():
                    if role.id == role_value or role_value == role.id:
                        spreadsheeter.add_role(role=role_key, user=user)

            for role in removed_roles:
                for role_key, role_value in staff_roles.items():
                    if role.id == role_value or role_value == role.id:
                        spreadsheeter.remove_role(role=role_key, user=user)



    """Commands are from here below"""


    def get_staff_ids():
        for role_key, role_value in staff_roles.items():
            return role_value


    @bot.command(name="uptime")
    @commands.has_any_role(get_staff_ids())
    async def uptime(ctx):
        """Checks the uptime of the bot"""
        message = (
            f"AutoMod has been online for <t:{start_time}:R>"
        )

        embed = discord.Embed(description=message, color=discord.Color.green(), title="Uptime")
        await ctx.send(embed=embed)


    @bot.command(name="checkflags")
    @commands.has_any_role(get_staff_ids())
    async def check_flags(ctx):
        """Checks the flags of a user"""
        if ctx.message.mentions:
            target = ctx.message.mentions[0]
            flag_list = []
            flags = target.public_flags

            for flag in flags:
                flag_list.append(flag)
            message = (
                flag_list
            )
            embed = discord.Embed(description=message, color=discord.Color.green(), title=f"Flags of {target.name}")
            await ctx.channel.send(embed=embed)
            logging.info(f"Presented tags of {target.name}")
        else:
            flag_list = []
            author = ctx.author
            flags = author.public_flags

            for flag in flags:
                flag_list.append(flag)
            message = (
                flag_list
            )
            embed = discord.Embed(description=message, color=discord.Color.green(), title=f"Flags of {author.name}")
            await ctx.channel.send(embed=embed)
            logging.info(f"Presented tags of {author.name}")


    @bot.command(name="spamcheck")
    @commands.has_any_role(get_staff_ids())
    async def check_for_spam_warnings(ctx):
        """Check the server for any potential spammers"""
        await check_for_spammers()


    return bot


if __name__ == "__main__":
    bot = setup_bot()
    bot.run(sensitivevariables.bot_token)
