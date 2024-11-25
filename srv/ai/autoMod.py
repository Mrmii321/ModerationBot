from openai import OpenAI


class AutoMod:
    def __init__(self, key):
        self.client = OpenAI(api_key=key)

        self.flagged_categories = []
        self.category_scores = []


    def get_flagged_categories(self, text):
        """
        Analyzes the given text for potentially harmful content using OpenAI's moderation API.

        This method sends the input text to OpenAI's moderation service and processes the
        response to identify any flagged categories of harmful content. It also stores the
        category scores for each category.

        Args:
            text (str): The text to be analyzed for harmful content.

        Returns:
            dict: A dictionary where keys are the names of flagged categories and values are
                boolean True. Only categories that are flagged are included in this dictionary.
                If no categories are flagged, an empty dictionary is returned.

        Note:
            This method logs the checked text using the logging module.
            It updates the instance variables self.flagged_categories and self.category_scores.
        """
        #TODO: make it show the certainty of the category being flagged
        response = self.client.moderations.create(
            model="omni-moderation-latest",
            input=text
            )
        response_dict = response.model_dump()
        results = response_dict['results'][0]
        self.flagged_categories = {category: flagged for category, flagged in results['categories'].items() if flagged}
        self.category_scores = {category: score for category, score in results['category_scores'].items()}
        logging.info(f"Checked text {text}")
        result = {
            "flagged_categories": self.flagged_categories,
            "category_scores": self.category_scores
        }
        return result

