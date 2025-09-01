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

            # --- helper: compute absolute start date window based on date_filter ---
            from datetime import datetime, timedelta, timezone
            now_utc = datetime.now(timezone.utc)
            window_start = None
            if date_filter == "d":
                window_start = now_utc - timedelta(days=1)
            elif date_filter == "w":
                window_start = now_utc - timedelta(days=7)
            elif date_filter == "m":
                window_start = now_utc - timedelta(days=30)

            # collect articles
            articles = []
            for meta, response in zip(results, responses):
                if isinstance(response, Exception) or not hasattr(response, 'text') or not response.text:
                    continue

                # extract clean text
                body = trafilatura.extract(response.text, include_comments=False, include_formatting=False)
                if not body:
                    continue

                # parse published date (if present)
                date_iso = ""
                published_dt = None
                try:
                    date_str = meta.get("date", "") or meta.get("datePublished", "")
                    if date_str:
                        published_dt = dateparser.parse(date_str, fuzzy=True)
                        if not published_dt.tzinfo:
                            published_dt = published_dt.replace(tzinfo=timezone.utc)
                        date_iso = published_dt.date().isoformat()
                except Exception:
                    published_dt = None
                    date_iso = ""

                # hard date filter (only if a date window is requested and date exists)
                if window_start and published_dt:
                    if published_dt < window_start:
                        continue
                elif window_start and not published_dt:
                    # if you want to *exclude* items with unknown dates when a filter is set, keep continue
                    continue

                articles.append({
                    "title": meta.get("title", "No Title"),
                    "link": meta.get("link", ""),
                    "published": date_iso,
                    "summary": body,
                    "source": meta.get("source", meta.get("link", "").split("/")[2] if meta.get("link") else ""),
                    "category": "web_search"
                })

            if not articles:
                return pd.DataFrame()

            df = pd.DataFrame(articles)

            # --- strict keyword filtering: every article must contain at least one keyword in title or body ---
            def matches_keywords(row):
                # if query is generated like ( "a" OR b OR ... ) we can’t reliably re-parse it;
                # instead pass a flat list of user keywords into this method via closure
                # -> we’ll read them from the 'query' string by extracting quoted and plain tokens
                # but the most reliable way is to pass a 'keywords' list as an extra arg; for now we parse:
                import re
                raw = (row.get("title","") + " " + row.get("summary","")).lower()
                # naive split: pick words >= 2 chars from the original query
                tokens = [t.strip('"').lower() for t in re.findall(r'"([^"]+)"|(\w{2,})', query)]
                # the above returns tuples; flatten:
                tok = []
                for a,b in tokens:
                    if a: tok.append(a)
                    elif b: tok.append(b)
                # require at least one token match:
                return any(k in raw for k in tok) if tok else True

            df = df[df.apply(matches_keywords, axis=1)]
            if df.empty:
                return df

            # downstream enrichment
            df["msa"] = df["summary"].fillna("").str[:5000].apply(extract_msa_region)
            df["keywords"] = df["summary"].apply(lambda text: self.extract_keywords(text))
            return df
        except Exception as e:
            print(f"❌ An error occurred during web search: {e}")
            return pd.DataFrame()
