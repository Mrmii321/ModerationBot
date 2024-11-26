import pymysql
import logging
import json
from dotenv import load_dotenv
import os
from sensitiveVariables import sensitiveVariables

sensitivevars = sensitiveVariables.SensitiveVariables()
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


class MariaDB:
    """
    Class to interact with a MariaDB database using pymysql.
    """

    def __init__(self):
        """
        Initialize the MariaDB class with database connection parameters.
        """
        self.db_data = {
            "host": sensitivevars.database['host'],
            "user": sensitivevars.database['user'],
            "password": sensitivevars.database['password'],
            "database": sensitivevars.database['database']
        }

    def connect_db(self):
        """
        Establish a connection to the MariaDB database.

        Returns:
        - pymysql connection object
        """
        # Validate that all required database connection parameters are present
        if not self.db_data["password"]:
            logger.error("DB_PASSWORD is missing or empty!")
            raise ValueError("DB_PASSWORD is required but not provided.")

        # Log the connection details (excluding the password)
        logger.info("Attempting to connect to the database with the following details:")
        logger.info(f"Host: {self.db_data['host']}")
        logger.info(f"User: {self.db_data['user']}")
        logger.info(f"Database: {self.db_data['database']}")

        # Establish the connection
        connection = pymysql.connect(
            host=self.db_data["host"],
            user=self.db_data["user"],
            password=self.db_data["password"],
            database=self.db_data["database"],
        )

        logger.info("Successfully connected to the database.")
        return connection

    async def log_filter(self, message, author, channel, time_sent, harmful_word):
        """
        Log filtered messages to the database.

        Parameters:
        - message: The content of the message.
        - author: The author of the message.
        - channel: The channel where the message was sent.
        - time_sent: The time when the message was sent.
        - harmful_word: The harmful word detected in the message.
        """
        try:
            db = self.connect_db()
            cursor = db.cursor()

            # Ensure all inputs are strings
            message = str(message)
            author = str(author)
            channel = str(channel)
            time_sent = str(time_sent)
            harmful_word = str(harmful_word)

            insert_query = (
                "INSERT INTO messages (message, author, channel, time_sent, word) "
                "VALUES (%s, %s, %s, %s, %s)"
            )
            logging.info("Executing filter query")
            cursor.execute(
                insert_query, (message, author, channel, time_sent, harmful_word)
            )

            db.commit()
            db.close()
        except pymysql.MySQLError as e:
            logger.error(f"Database error: {e}")

    async def log_ai(self, message, author, channel, time_sent, flags, scores):
        """
        Log AI-generated messages to the database.

        Parameters:
        - message: The content of the message.
        - author: The author of the message.
        - channel: The channel where the message was sent.
        - time_sent: The time when the message was sent.
        - flags: Flags associated with the AI message.
        - scores: The scores for each flag associated with the AI message.
        """
        try:
            db = self.connect_db()
            cursor = db.cursor()

            # Ensure all inputs are strings or properly serialized
            message = str(message)
            author = str(author)
            channel = str(channel)
            time_sent = str(time_sent)
            flags = str(flags)
            scores = json.dumps(scores)  # Serialize scores to JSON

            insert_query = (
                "INSERT INTO ai_messages "
                "(message, author, channel, time_sent, flags, scores) "
                "VALUES (%s, %s, %s, %s, %s, %s)"
            )
            logging.info("Executing AI log query")
            cursor.execute(
                insert_query, (message, author, channel, time_sent, flags, scores)
            )

            db.commit()
            db.close()
        except pymysql.MySQLError as e:
            logger.error(f"Database error: {e}")

    async def retrieve_user_data(self, ctx):
        """
        Retrieve user data from the database and send it to the context.

        Parameters:
        - ctx: The context from which the request was made.
        """
        author = ctx.author
        try:
            db = self.connect_db()
            cursor = db.cursor()

            query = "SELECT * FROM messages WHERE author = %s;"
            cursor.execute(query, (author.name,))
            logging.info(f"Retrieved data for user: {author.name}")

            rows = cursor.fetchall()
            row_list = [row for row in rows]

            await ctx.send(row_list)
            db.close()
        except pymysql.MySQLError as e:
            logger.error(f"Database error: {e}")
