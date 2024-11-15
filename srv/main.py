import json
import logging
import time
import discord
from discord.ext import commands, tasks
from openai import OpenAI
from database import database
from sensitiveVariables import sensitiveVariables


sensitivevariables = sensitiveVariables.SensitiveVariables()
database = database.MariaDB()
staff_roles = sensitivevariables.staff_roles


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.StreamHandler()
])
logger = logging.getLogger(__name__)


class Main:
    def __init__(self, ai_key, bot_class_var):
        self.status = discord.Activity(type=discord.ActivityType.watching, name="for =help", start=0)
        # start=0 is the timestamp for when activity starts
        self.client = OpenAI(api_key=ai_key)
        self.bot = bot_class_var

    async def get_flagged_categories(self, text):
        """The actual AI part"""
        response = self.client.moderations.create(
            model="omni-moderation-latest",
            input=text
            )
        response_dict = response.model_dump()
        results = response_dict['results'][0]
        flagged_categories = {category: flagged for category, flagged in results['categories'].items() if flagged}
        logging.info(f"Checked text {text}")
        return flagged_categories

    async def create_embed(self, message, author=None, title="", color=discord.Color.default()):
        embed = discord.Embed(description=message, color=color, title=title)
        if author:
            embed.set_footer(text=f"Sent by: {author}")
        return embed


    async def send_embed(self, channel_id, *, message, author=None, title="Harmful message", color=discord.Color.red()):
        """
        Send an embedded message to a specified channel.

        This function creates and sends an embedded message to a Discord channel.

        Args:
            channel_id (int): The ID of the channel to send the embed to.
            message (str): The main content of the embed.
            author (discord.Member, optional): The author of the message. Defaults to None.
            title (str, optional): The title of the embed. Defaults to "Harmful message".
            color (discord.Color, optional): The color of the embed. Defaults to discord.Color.red().

        Returns:
            None

        Note:
            This function logs the creation of the embed for a harmful message.
        """
        channel = self.bot.get_channel(channel_id)
        embed = await self.create_embed(message=message, author=author, title=title, color=color)
        await channel.send(embed=embed)  # Send the embed
        logging.info(f"Created Embed for harmful message {message}")


    async def send_dm(self, *, message, author):
        dm_channel = author.dm_channel
        if dm_channel is None:
            dm_channel = await author.create_dm()
        await dm_channel.send(message)
        logging.info(f"Sent DM to {author}: {message}")

    
    async def send_embed_dm(self, *, message, author, title="", color=discord.Color.default()):
        """
        Send an embedded direct message to a user.

        This function creates and sends an embedded message to a user's DM channel.

        Args:
            message (str): The main content of the embed.
            author (discord.Member): The user to whom the DM will be sent.
            title (str, optional): The title of the embed. Defaults to an empty string.
            color (discord.Color, optional): The color of the embed. Defaults to discord.Color.default().

        Returns:
            None

        Note:
            This function logs the sending of the embed DM.
        """
        dm_channel = author.dm_channel
        if dm_channel is None:
            dm_channel = await author.create_dm()
        embed = await self.create_embed(message=message, author=author, title=title, color=color)
        await dm_channel.send(embed=embed)
        logging.info(f"Sent Embed DM to {author}: {message}")



def setup_bot():
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix='==', intents=intents)
    bypass_roles = ["Owner", "Admin", "General Manager", "Community manager", "Staff manager",
                    "Events Manager", "Consultant", "Senior Moderator", "Developer"]
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
        await main.send_embed(channel_id=tybalt_logs.id, message=message, title="**AutoMod Online**", color=discord.Color.green())
        check_for_spammers.start(manual=False)


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
                await main.send_embed(channel_id=1250475863976312944,
                                        message=f"Harmful message: {message.content}.\n"
                                                f"Category: {flagged_categories}.\n "
                                                f"Sent by: {message.author}.\n"
                                                f"Channel: {message.channel}.\n"
                                                f"Timespamp: {message.created_at}.",
                                        author=message.author)
                key = list(flagged_categories.keys())[0]

                await database.log_ai(message=message.content,
                                      author=message.author,
                                      channel=message.channel,
                                      time_sent=message.created_at,
                                      flags=key.strip("''"))

            """Part for bad words list"""

            with open("srv/nono_words.json", "r") as file:
                data = json.loads(file.read())
            words = message.content.split()
            for word in data:
                if word in words:
                    logging.info(f"Bad word ({word}) detected")
                    await main.send_embed(channel_id=1250475863976312944,
                                            message=f"Offending word: {word}.\n"
                                                    f"Message: {message.content}.\n "
                                                    f"Sent by: {message.author}.\n"
                                                    f"Channel: {message.channel}.\n"
                                                    f"Timespamp: {message.created_at}.",
                                            author=message.author,
                                            title="Harmful word in message",
                                            color=discord.Color.red())
                    await message.channel.send(f"Please do not say vulgar things {message.author.mention}")
                    await database.log_filter(message=message.content,
                                              author=message.author,
                                              channel=message.channel,
                                              time_sent=message.created_at,
                                              harmful_word=word)
                    
                    await main.send_embed_dm(author=message.author,
                     message=f"Hey {message.author}, your message goes against our community guidelines. "
                            f"Please keep things respectful to maintain a positive environment!\n\n"
                            f"Offending word: {word}.\n"
                            f"Message: {message.content}.\n"
                            f"Sent by: {message.author}.\n"
                            f"Channel: {message.channel}.\n"
                            f"Timestamp: {message.created_at}.",
                    title="**Harmful language**",
                    color=discord.Color.red())
                    await message.delete()
        else:
            await bot.process_commands(message)


    @tasks.loop(hours=3)
    async def check_for_spammers(manual):
        if manual:
            logging.info("Started spammer check manually")
            await main.send_embed(channel_id=1250475863976312944, message="Started spammer check manually", title="**Spammer Check**", color=discord.Color.green())
        else:
            logging.info("Started spammer check automatically")
        guild_id = bot.get_guild(272148882048155649)
        channel = bot.get_channel(1250475863976312944)
        members = guild_id.members
        for member in members:

            if member.public_flags.spammer:
                await main.send_embed(channel_id=channel.id,
                                        message=f"User {member.mention} ({member.name}) has been flagged as suspicious.",
                                        title="**Suspicious Account**", color=discord.Color.red())
                logging.info(f"User {member.name} has been flagged as potential spammer.")
            if len(members) == 0 and manual:
                await main.send_embed(channel_id=channel.id, message="No suspicious accounts found.", title="**No Suspicious Accounts**", color=discord.Color.green())
                logging.info(f"No suspicious accounts found.")


    async def send_embed(channel_id, message):
        await main.send_embed(channel_id=channel_id, message=message, title="Harmful word in message", color=discord.Color.red())


    """Commands are from here below"""
    def get_staff_role_ids():
        return list(staff_roles.values())


    @bot.command(name="uptime")
    @commands.has_any_role(*get_staff_role_ids())
    async def uptime(ctx):
        """Checks the uptime of the bot"""
        message = (
            f"AutoMod went online <t:{start_time}:R>"
        )

        await main.send_embed(channel_id=ctx.channel.id, message=message, title="Uptime", color=discord.Color.green())


    @bot.command(name="checkflags")
    @commands.has_any_role(*get_staff_role_ids())
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
            await main.send_embed(channel_id=ctx.channel.id, message=message, title=f"Flags of {target.name}", color=discord.Color.green())
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
            await main.send_embed(channel_id=ctx.channel.id, message=message, title=f"Flags of {author.name}", color=discord.Color.green())
            logging.info(f"Presented tags of {author.name}")


    @bot.command(name="spamcheck")
    @commands.has_any_role(*get_staff_role_ids())
    async def check_for_spam_warnings(ctx):
        """Check the server for any potential spammers"""
        await check_for_spammers(manual=True)


    @bot.command(name="scan")
    @commands.has_any_role(*get_staff_role_ids())
    async def database_query_user(ctx):
        await database.retrieve_user_data(ctx=ctx)


    return bot


if __name__ == "__main__":
    bot = setup_bot()
    bot.run(sensitivevariables.bot_token)
