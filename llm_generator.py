import os
from openai import OpenAI, APIError
from dotenv import load_dotenv

load_dotenv()

class NewsletterGenerator:
    def __init__(self):
        # ... (existing init code)
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("⚠️ Warning: OpenAI API key not found.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)

    def generate_newsletter_section(self, articles_df, theme_keywords):
        """
        Generates a themed summary of articles using the updated OpenAI API syntax.
        """
        # Check if the client was initialized successfully
        if not self.client:
            return self._generate_simple_summary(articles_df, theme_keywords)
        
        if articles_df.empty:
            return "No articles were found for this theme."
        
        # Prepare a concise summary of the top articles for the prompt
        articles_text = ""
        for _, row in articles_df.head(5).iterrows():
            articles_text += f"- Title: {row['title']}\n"
            articles_text += f"  Summary: {row['summary'][:250]}...\n\n"
        
        system_prompt = (
            "You are a policy analyst specializing in U.S. science and technology policy. "
            "Your focus is on federal R&D funding, legislation, and its impact on universities, "
            "colleges, and regional economic development."
        )
        
        user_prompt = f"""
        Analyze the following articles related to the theme "{', '.join(theme_keywords)}".

        Articles:
        {articles_text}
        
        Synthesize the key information into a concise intelligence briefing. Follow these instructions strictly:
        1. Identify the core government action or policy trend (e.g., new legislation, grant program, or federal initiative).
        2. Explain the direct impact on universities, research institutions, or regional tech hubs.
        3. Mention any specific states, organizations, or funding amounts if available.
        4. Summarize your analysis into 3-4 clear, distinct bullet points.
        5. Each bullet point must be a single, direct sentence.
        """
            
        try:
            # New syntax for making an API call
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=350,
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        
        except APIError as e:
            print(f"❌ OpenAI API error: {e}")
            return f"LLM analysis failed due to an API error. Falling back to a basic summary:\n{self._generate_simple_summary(articles_df, theme_keywords)}"
    
    def _generate_simple_summary(self, articles_df, theme_keywords):
        """Fallback method to generate a basic summary if the LLM call fails or is disabled."""
        if articles_df.empty:
            return "No articles found for this theme."
        
        summary = f"This analysis covers {len(articles_df)} articles related to '{theme_keywords[0]}'.\n"
        summary += "Key developments appear in the following articles:\n"
        
        for _, article in articles_df.head(3).iterrows():
            summary += f"- {article['title']}\n"
        
        summary += f"\nThese articles suggest notable activity regarding federal policy and its effects on research and academic institutions."
        
        return summary
    
    def generate_report_summary(self, report_text: str) -> str:
        """
        Takes a block of raw text containing multiple articles and summarizes
        it into a clean, point-wise Markdown format.
        """
        if not self.client:
            return "LLM Client not initialized. Check your OPENAI_API_KEY."

        system_prompt = (
            "You are a professional research analyst. Your task is to synthesize a collection "
            "of articles into a concise, point-wise summary document suitable for a briefing."
        )
        
        user_prompt = f"""
        Please process the following block of text, which contains multiple articles separated by '---'. 
        For each article, format the output strictly as follows:

        1. The article's title as a level 3 Markdown heading (###).
        2. The publication date on the next line in the format: **Published:** YYYY-MM-DD
        3. A bulleted list of 3-5 key summary points from the article's content.
        4. A Markdown horizontal rule (---) to separate each article's summary.

        Here is the text to summarize:
        ---
        {report_text}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
            )
            return response.choices[0].message.content.strip()
        except APIError as e:
            print(f"❌ OpenAI API error during report summarization: {e}")
            return "Error: The AI failed to generate the summary."