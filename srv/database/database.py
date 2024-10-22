import sqlite3
import logging

logger = logging.getLogger(__name__)


class MariaDB:
    def __init__(self):
        self.db_path = r"logs.db"  # TODO update logs.db on filezilla

    async def log_filter(self, message, author, channel, time_sent, harmful_word):
        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()

            # Ensure all inputs are strings
            message = str(message)
            author = str(author)
            channel = str(channel)
            time_sent = str(time_sent)
            harmful_word = str(harmful_word)

            insert_query = "INSERT INTO messages (message, author, channel, time_sent, word) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(insert_query, (message, author, channel, time_sent, harmful_word))

            db.commit()
            db.close()

        except sqlite3.Error as e:
            logger.error(e)

    async def log_ai(self, message, author, channel, time_sent, flags):
        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()

            # Ensure all inputs are strings
            message = str(message)
            author = str(author)
            channel = str(channel)
            time_sent = str(time_sent)
            flags = str(flags)

            insert_query = "INSERT INTO ai_messages (message, author, channel, time_sent, flags) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(insert_query, (message, author, channel, time_sent, flags))

            db.commit()
            db.close()

        except sqlite3.Error as e:
            logger.error(e)


    async def retrieve_user_data(self, ctx):
        author = ctx.author
        db = sqlite3.connect(self.db_path)
        cursor = db.cursor()

        query = "SELECT * FROM messages WHERE author = ?;"

        cursor.execute(query, (author.name,))
        logging.info(f"Scanned {str (author.name)}")

        rows = cursor.fetchall()

        row_list = []

        for row in rows:
            row_list.append(row)
        await ctx.send(row_list)

        db.close()
