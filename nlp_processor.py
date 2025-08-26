import pandas as pd
import re

# This dictionary defines your "themes". You can easily update this
# to create new themes or change which keywords belong to each.
THEME_DEFINITIONS = {
    "Federal Science & Tech Policy": [
        "NSF Recompete Pilot Program", "Economic Development Agency", "EDA",
        "CHIPS Act", "AI Legislation", "Federal AI Legislation", "EDA's Impact Newsletter"
    ],
    "Semiconductor Industry & Supply Chain": [
        "Semiconductors", "CHIPS Act"
    ],
    "University Research & Innovation": [
        "University", "research", "Research Expenditures", "Research Grant/Award", "HBCUs", "College"
    ],
    "Regional Tech Hubs & Economic Impact": [
        "Pittsburgh", "Nashville", "Georgia", "Texas", "Tech Hub", "Economic Impact"
    ]
}

class MarketIntelligenceNLP:
    def __init__(self):
        """
        Initializes the NLP processor.
        The old TF-IDF vectorizer is no longer needed for this approach.
        """
        pass

    def categorize_by_theme(self, articles_df: pd.DataFrame, all_keywords: list) -> (pd.DataFrame, dict):
        """
        Categorizes articles into predefined themes based on keywords.

        This method replaces unsupervised clustering with a more reliable,
        rule-based approach tailored to your specific intelligence needs.

        Args:
            articles_df: DataFrame containing all collected articles.
            all_keywords: A complete list of all possible keywords to search for.

        Returns:
            A tuple containing:
            - A DataFrame of all articles that matched at least one theme.
            - A dictionary where keys are theme names and values contain
              the theme's keywords and a DataFrame of its articles.
        """
        if articles_df.empty:
            return pd.DataFrame(), {}

        # Prepare a single text column for efficient searching.
        articles_df['text_for_search'] = (
            articles_df['title'].fillna('') + " " + articles_df['summary'].fillna('')
        ).str.lower()

        # Helper function to check for keyword presence using word boundaries for accuracy.
        def contains_any_keyword(text, keywords):
            for kw in keywords:
                # \b ensures we match whole words only (e.g., "eda" doesn't match "leader").
                pattern = r'\b' + re.escape(kw.lower()) + r'\b'
                if re.search(pattern, text):
                    return True
            return False

        # --- Step 1: Filter for any relevant article ---
        # Keep only articles that contain at least one of our keywords of interest.
        relevant_articles_df = articles_df[
            articles_df['text_for_search'].apply(lambda x: contains_any_keyword(x, all_keywords))
        ].copy()

        if relevant_articles_df.empty:
            return pd.DataFrame(), {}

        # --- Step 2: Assign filtered articles to specific themes ---
        themes_with_articles = {}
        for theme_name, theme_keywords in THEME_DEFINITIONS.items():
            # Find articles that match the keywords for this specific theme.
            matching_articles = relevant_articles_df[
                relevant_articles_df['text_for_search'].apply(lambda x: contains_any_keyword(x, theme_keywords))
            ]

            if not matching_articles.empty:
                themes_with_articles[theme_name] = {
                    'keywords': theme_keywords,
                    'articles': matching_articles.copy()
                }

        return relevant_articles_df, themes_with_articles