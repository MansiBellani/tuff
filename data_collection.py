import os
import asyncio
import httpx
import pandas as pd
import trafilatura
from dotenv import load_dotenv
from dateutil import parser as dateparser
import spacy
from msa_mapping import extract_msa_region
from sklearn.feature_extraction.text import TfidfVectorizer

load_dotenv()

class MarketIntelligenceCollector:
    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.serper_headers = {
            "X-API-KEY": self.serper_api_key, "Content-Type": "application/json"
        }
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def search_web_and_extract(self, query: str, search_type: str = "news", num_results: int = 15, date_filter: str = None) -> pd.DataFrame:
        if not self.serper_api_key:
            print("⚠️ SERPER_API_KEY not found.")
            return pd.DataFrame()
        return asyncio.run(self._async_search_and_extract(query, search_type, num_results, date_filter))

    async def _async_search_and_extract(self, query: str, search_type: str, num_results: int, date_filter: str) -> pd.DataFrame:
        endpoint = "https://google.serper.dev/news" if search_type == "news" else "https://google.serper.dev/search"
        payload = {"q": query, "num": num_results}

        # --- RE-IMPLEMENTED NATIVE DATE FILTERING ---
        date_filter_map = {
            "d": "qdr:d",  # past day
            "w": "qdr:w",  # past week
            "m": "qdr:m",  # past month
        }
        if date_filter in date_filter_map:
            payload["tbs"] = date_filter_map[date_filter]
        # --- END OF FIX ---

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(endpoint, headers=self.serper_headers, json=payload)
                resp.raise_for_status()
            results = resp.json().get("news" if search_type == "news" else "organic", [])
            if not results:
                print(f"No results found for query: '{query}'")
                return pd.DataFrame()

            urls = [r["link"] for r in results]
            async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
                tasks = [client.get(u) for u in urls]
                responses = await asyncio.gather(*tasks, return_exceptions=True)

            articles = []
            for meta, response in zip(results, responses):
                if isinstance(response, Exception) or not hasattr(response, 'text') or not response.text:
                    continue
                body = trafilatura.extract(response.text, include_comments=False, include_formatting=False)
                if not body:
                    continue

                date_iso = ""
                try:
                    date_str = meta.get("date", "")
                    if date_str:
                        date_iso = dateparser.parse(date_str, fuzzy=True).strftime("%Y-%m-%d")
                except Exception:
                    date_iso = ""

                articles.append({
                    "title": meta.get("title", "No Title"), "link": meta.get("link", ""),
                    "published": date_iso, "summary": body,
                    "source": meta.get("source", meta.get("link", "").split("/")[2]),
                    "category": "web_search"
                })
            
            if not articles:
                return pd.DataFrame()

            df = pd.DataFrame(articles)
            df["msa"] = df["summary"].fillna("").str[:5000].apply(extract_msa_region)
            df['keywords'] = df['summary'].apply(lambda text: self.extract_keywords(text))
            return df
        except Exception as e:
            print(f"❌ An error occurred during web search: {e}")
            return pd.DataFrame()

    def extract_keywords(self, text, top_n=5):
        if not isinstance(text, str) or len(text.strip()) < 20:
            return []
        try:
            tfidf = TfidfVectorizer(stop_words='english', max_features=100)
            X = tfidf.fit_transform([text])
            feature_names = tfidf.get_feature_names_out()
            scores = X.toarray()[0]
            keywords = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
            return [kw for kw, _ in keywords[:top_n]]
        except ValueError:
            return []