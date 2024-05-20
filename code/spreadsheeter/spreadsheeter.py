import logging


logger = logging.getLogger(__name__)


class Spreadsheeter:
    def __init__(self):
        pass

    def add_role(self, role, user):
        logging.info(f"spreadsheeter added {role} to {user}")

    def remove_role(self, role, user):
        logging.info(f"spreadsheeter removed {role} from {user}")
