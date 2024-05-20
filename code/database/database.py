import mariadb
import logging


logger = logging.getLogger(__name__)


class MariaDB:
    def __init__(self):
        self.host = "localhost"
        self.user = "tybalt"
        self.password = "OWuq)xg4j7mdU2hr"
        self.database = "tybalt-logs"

    def log_filter(self, message, author, channel, time_sent, harmful_word):
        try:
            db = mariadb.connect(
                host=self.host,
                user=self.user,
                passwd=self.password,
                database=self.database
            )

            cursor = db.cursor()

            insert_into_table = ("INSERT INTO messages (message, author, channel, time_sent, word) "
                                 "VALUES (?, ?, ?, ?, ?)")
            cursor.execute(insert_into_table, (message, author.name, channel.name, time_sent, harmful_word))
            logging.info(f"Run database command {insert_into_table} with values {message},"
                         f" {author.name},"
                         f" {channel.name},"
                         f" {time_sent},"
                         f" {harmful_word}")
            db.commit()
            db.close()
            logging.info(f"Logged harmful word to database")
        except mariadb.Error as e:
            logging.error(e)

    def log_ai(self, message, author, channel, time_sent, flags):
        try:
            db = mariadb.connect(
                host=self.host,
                user=self.user,
                passwd=self.password,
                database=self.database
            )

            cursor = db.cursor()

            insert_into_table = ("INSERT INTO ai_messages (message, author, channel, time_sent, flags) "
                                 "VALUES (?, ?, ?, ?, ?)")
            cursor.execute(insert_into_table, (message, author.name, channel.name, time_sent, flags))
            logging.info(f"Run AI database command {insert_into_table} with values {message},"
                         f" {author.name},"
                         f" {channel.name},"
                         f" {time_sent},"
                         f" {flags}")
            db.commit()
            db.close()
            logging.info("Logged AI report to database")
        except mariadb.Error as e:
            logging.error(e)
