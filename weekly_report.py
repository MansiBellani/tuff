# weekly_report.py
import os
import sys
import pandas as pd
from datetime import datetime

# Reuse your existing modules
from data_collection import MarketIntelligenceCollector
from nlp_processor import MarketIntelligenceNLP
from llm_generator import NewsletterGenerator
from tools import add_content_to_document, send_email

# ---- Safety checks for required secrets
REQUIRED_KEYS = ["ARCADE_API_KEY", "ARCADE_USER_ID", "SERPER_API_KEY"]
missing = [k for k in REQUIRED_KEYS if not os.getenv(k)]
if missing:
    print(f"❌ Missing required secrets: {', '.join(missing)}")
    sys.exit(1)

# ---- Load keywords
try:
    keywords_df = pd.read_csv("keywords.csv")
except FileNotFoundError:
    print("❌ keywords.csv not found at repo root.")
    sys.exit(1)

# Strategy: use all keywords (or filter by specific themes if you want)
all_keywords = keywords_df["keyword"].dropna().unique().tolist()
if not all_keywords:
    print("⚠️ No keywords found in keywords.csv; exiting.")
    sys.exit(0)

# ---- Build a simple query (same logic as app)
def generate_search_query(keywords: list) -> str:
    exact_phrases = [f'"{kw}"' for kw in keywords if len(str(kw).split()) > 1]
    single_words   = [kw for kw in keywords if len(str(kw).split()) == 1]
    query_parts = exact_phrases + single_words
    keyword_query = f"({' OR '.join(query_parts)})"
    # refine for R&D, constrain to authoritative domains
    full_query = (
        f"{keyword_query} AND "
        f"('university research funding' OR 'federal research grants' OR 'R&D policy') "
        f"AND (site:.gov OR site:.edu OR site:.org)"
    )
    return full_query

search_query = generate_search_query(all_keywords)

# ---- Collect last-week news (using serper native date filter 'w')
collector = MarketIntelligenceCollector()
articles_df = collector.search_web_and_extract(
    search_query,
    search_type="news",
    num_results=20,
    date_filter="w",  # past week
)

if articles_df is None or articles_df.empty:
    print("ℹ️ No articles found this week. Exiting gracefully.")
    sys.exit(0)

# ---- NLP: categorize + summarize
nlp_processor = MarketIntelligenceNLP()
themed_articles, themes = nlp_processor.categorize_by_theme(articles_df, all_keywords)

if themed_articles is None or themed_articles.empty:
    print("ℹ️ No themed articles to summarize this week.")
    sys.exit(0)

generator = NewsletterGenerator()

# Build consolidated report content
final_report_content = ""
selected_count = 0
for theme_name, theme_details in themes.items():
    df = theme_details.get("articles")
    if df is None or df.empty:
        continue
    summary = generator.generate_newsletter_section(df, theme_details.get("keywords", []))
    final_report_content += f"## Intelligence Briefing: {theme_name}\n\n{summary}\n\n---\n\n"
    selected_count += 1

if selected_count == 0:
    print("ℹ️ No summaries produced. Exiting.")
    sys.exit(0)

# ---- Create Google Doc (and optionally email)
report_title = f"Consolidated R&D Intelligence Briefing — Week of {datetime.utcnow().date()}"
doc_response = add_content_to_document(content=final_report_content, file_name=report_title)
print(f"📄 Doc result: {doc_response}")

# Optional: email the report body (uncomment if you want automatic email)
RECIPIENT = os.getenv("BRIEFING_RECIPIENT_EMAIL", "")  # set this in Actions secrets if desired
if RECIPIENT:
    mail_resp = send_email(
        content=final_report_content,
        subject=report_title,
        recipient=RECIPIENT
    )
    print(f"📧 Email result: {mail_resp}")
else:
    print("📧 Email skipped (no BRIEFING_RECIPIENT_EMAIL set).")
