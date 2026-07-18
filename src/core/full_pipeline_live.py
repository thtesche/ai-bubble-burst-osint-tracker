import sys
import os
import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

# Add project root (parent of src/) to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.fetchers.googlenews import GoogleNewsFetcher
from src.fetchers.market import MarketDataFetcher
from src.core.logger import RunLogger
from src.inference import LLMEngine, LLMResponse, build_system_prompt, build_user_prompt


def _format_capex_value(val) -> str | None:
    """Format a CapEx dollar value as human-readable (e.g. $30.88B)."""
    if val is None:
        return None
    try:
        v = float(val)
    except (ValueError, TypeError):
        return val
    if abs(v) >= 1e12:
        return f"${abs(v)/1e12:.2f}T"
    elif abs(v) >= 1e9:
        return f"${abs(v)/1e9:.2f}B"
    elif abs(v) >= 1e6:
        return f"${abs(v)/1e6:.2f}M"
    elif abs(v) >= 1e3:
        return f"${abs(v)/1e3:.2f}K"
    return f"${abs(v):.2f}"


def _format_capex_data(data: dict) -> dict:
    """Return a copy of capex_data with dates truncated and values formatted."""
    formatted = {}
    for ticker, sections in data.items():
        formatted[ticker] = {}
        for key, values in sections.items():
            formatted[ticker][key] = {}
            for date_key, val in values.items():
                # Truncate date: keep only the date part
                if isinstance(date_key, str) and " " in date_key:
                    date_key = date_key.split(" ")[0]
                formatted[ticker][key][date_key] = _format_capex_value(val)
    return formatted


@dataclass
class PipelineResult:
    """Structured return value for the pipeline."""
    bubble_score: float
    sentiment_score: float
    market_score: float
    capex_score: float
    market_metrics: dict
    capex_data: dict
    googlenews_articles: list[dict]
    llm_content: str = ""
    llm_model: str = ""
    article_sentiments: list[dict] | None = None


class PipelineError(Exception):
    """Raised when the pipeline cannot proceed due to missing or invalid data."""
    pass


_SENTIMENT_SYSTEM_PROMPT = (
    "You are a sentiment analysis expert. Given a news article text, "
    "assign a sentiment score between 0.0 and 1.0 based on the article's "
    "stance toward the AI market/tech sector.\n\n"
    "Scoring rubric (directed at AI bubble risk):\n"
    "- 0.0 = strongly bearish: article warns of AI bubble, describes "
    "speculative mania, overvaluation, impending crash\n"
    "- 0.5 = neutral: balanced reporting, no clear bullish or bearish bias\n"
    "- 1.0 = strongly bullish: article praises AI growth, calls it "
    "revolutionary, discusses explosive growth\n\n"
    "Output ONLY a JSON object with the following structure — no "
    "explanations, no reasoning:\n"
    "{'sentiment_score': <float 0-1>, 'reason': '<short 1-2 sentence "
    "reasoning>'}\n"
)


def _build_sentiment_user_prompt(title: str, content: str) -> str:
    """Build the user prompt for a single article's sentiment analysis."""
    return (
        f"Article Title: {title}\n\n"
        f"Article Content (truncated to ~4000 chars):\n"
        f"{content[:4000]}\n"
        f"\nAnalyze the sentiment of this article regarding the AI market/tech sector."
    )


async def _analyze_sentiment_by_article(
    article: dict,
    llm_engine: LLMEngine,
) -> dict:
    """
    Call the LLM for ONE article and return structured sentiment data.

    Returns:
        {
            'url': str (origin_url or link),
            'title': str,
            'content': str (truncated to 2000 chars),
            'sentiment_score': float,
            'reason': str
        }
    """
    url = article.get("origin_url") or article.get("link", "")
    title = article.get("title", "No Title")
    # Prefer Firecrawl-scraped content (full markdown); fall back to description
    content = article.get("content") or article.get("description", "")

    try:
        response = await llm_engine.generate_async(
            prompt=_build_sentiment_user_prompt(title, content),
            system_prompt=_SENTIMENT_SYSTEM_PROMPT,
        )

        if response.is_success and response.content:
            # Extract JSON from the LLM response (handle possible markdown fences)
            raw = response.content.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.strip("`").strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()
            parsed = json.loads(raw)
            score = float(parsed.get("sentiment_score", 0.5))
            score = max(0.0, min(1.0, score))  # clamp
            return {
                "url": url,
                "title": title,
                "content": content[:2000],  # keep content for reference
                "sentiment_score": score,
                "reason": parsed.get("reason", ""),
            }
        else:
            print(f"[!] LLM sentiment failed for '{title}': {response.error}")
            return {
                "url": url,
                "title": title,
                "content": content[:2000],
                "sentiment_score": 0.5,  # fallback: neutral
                "reason": f"LLM error: {response.error}",
            }
    except json.JSONDecodeError as e:
        print(f"[!] JSON parse error for '{title}': {e}")
        return {
            "url": url,
            "title": title,
            "content": content[:2000],
            "sentiment_score": 0.5,
            "reason": f"JSON parse error: {e}",
        }
    except Exception as e:
        print(f"[!] Unexpected error for '{title}': {e}")
        return {
            "url": url,
            "title": title,
            "content": content[:2000],
            "sentiment_score": 0.5,
            "reason": f"Unexpected error: {e}",
        }


def _generate_report(final_bubble_score: float, sentiment_score: float,
                     market_score: float, capex_score: float,
                     news_data: list, googlenews_data: dict,
                     market_metrics: dict, capex_data: dict,
                     llm_response: Optional[LLMResponse] = None) -> str:
    """Formats the final findings into a professional report."""
    report = "### 🫧 AI Bubble Burst Report\n"
    report += f"**Current Bubble Score: {final_bubble_score:.1f}%**\n\n"

    # Risk Assessment
    if final_bubble_score >= 70:
        status, desc = "🔴 **CRITICAL RISK**", "Extreme signs of overheating and speculative mania."
    elif final_bubble_score >= 40:
        status, desc = "🟡 **MODERATE RISK**", "Mixed signals. Significant hype is present, but some fundamental caution remains."
    else:
        status, desc = "🟢 **LOW RISK**", "Market sentiment appears stable or grounded."

    report += f"**Status: {status}**\n"
    report += f"{desc}\n\n"

    # Scores breakdown
    report += "**📊 Score Breakdown:**\n"
    report += f"- Sentiment Score (News): {sentiment_score:.2f}\n"
    report += f"- Market Score (Prices):  {market_score:.2f}\n"
    report += f"- CapEx Score (Investments): {capex_score:.2f}\n\n"

    # Market Data
    if market_metrics:
        report += "**📈 Market Data:**\n"
        for ticker, data in market_metrics.items():
            report += f"- **{ticker}**: ${data['current_price_dollar']:.2f} (daily: {data['daily_change_percent']:+.2f}%, SMA 200: {data['distance_from_sma_200_percent']:+.2f}%, YTD: {data['ytd_change_percent']:+.2f}%)\n"
        report += "\n"

    # CapEx Data
    if capex_data:
        report += "**💰 CapEx Summary:**\n"
        for ticker, data in capex_data.items():
            quarterly = data.get("quarterly_capex", {})
            if quarterly:
                sorted_q = sorted(quarterly.keys(), reverse=True)[:3]
                latest_vals = [abs(float(quarterly[q])) for q in sorted_q if quarterly[q] is not None]
                if latest_vals:
                    report += f"- **{ticker}**: Latest 3 quarters: {', '.join(f'{v:.0f}' for v in latest_vals)}\n"
        report += "\n"

    # News Analysis (Firecrawl)
    if news_data and len(news_data) > 0:
        report += "**📰 Latest News (Firecrawl):**\n"
        for article in news_data:
            title = article.get('title', 'No Title')
            url = article.get('url', '#')
            report += f"- [{title}]({url})\n"
        report += "\n"

    # Google News
    googlenews_articles = googlenews_data.get("articles", [])
    if googlenews_articles:
        report += "**📰 Google News (neueste 10):**\n"
        for article in googlenews_articles:
            title = article.get("title", "No Title")
            # Prefer originUrl (real source URL); fall back to Google redirect link
            link = article.get("origin_url") or article.get("link", "#")
            raw_date = article.get("pub_date", "")
            if raw_date:
                try:
                    dt = parsedate_to_datetime(raw_date)
                    date_str = dt.strftime("%d.%m.%Y")
                except (ValueError, TypeError):
                    date_str = "N/A"
            else:
                date_str = "N/A"
            report += f"- **{date_str}** [{title}]({link})\n"
        report += "\n"

    # LLM Risk Evaluation (if available)
    if llm_response and llm_response.is_success and llm_response.content:
        report += "**🤖 LLM Risk Evaluation:**\n"
        report += f"__Model__: `{llm_response.model}`\n\n"
        report += f"{llm_response.content}\n\n"
    elif llm_response and not llm_response.is_success:
        report += f"**⚠️ LLM Inference skipped:** {llm_response.error}\n\n"

    report += f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

    return report


async def run_pipeline(
    query: str = "AI market bubble burst risk analysis 2025 2026",
    limit: int = 5,
    tickers: Optional[list[str]] = None,
    googlenews_fetcher: Optional[GoogleNewsFetcher] = None,
    market_fetcher: Optional[MarketDataFetcher] = None,
) -> PipelineResult:
    """
    Full E2E pipeline: fetches news (Google News), market data,
    calculates scores, and returns structured data for delivery.

    Uses Dependency Injection for fetchers to allow easier testing.
    If no fetchers are provided, default instances are created.

    Returns:
        PipelineResult: Structured data containing all scores, data, and LLM output.
    
    Raises:
        PipelineError: if critical data fetching fails.
    """
    if tickers is None:
        tickers = ["MSFT", "GOOGL", "AMZN", "META", "NVDA",
                    "AMD", "ASML", "AVGO", "MU", "DELL",
                    "SMCI", "HPE"]

    print("=== STARTING LIVE DATA ===")

    # 0. Setup Logger
    logger = RunLogger()

    if googlenews_fetcher is None:
        googlenews_fetcher = GoogleNewsFetcher(
            query=query, limit=10
        )

    if market_fetcher is None:
        market_fetcher = MarketDataFetcher(tickers=tickers)

    # 1. Google News Fetching (async now — scrapes URLs with Firecrawl internally)
    print("\n[*] Step 1: Fetching news via Google News RSS + Firecrawl...")
    googlenews_data = await googlenews_fetcher.fetch_articles()

    if not googlenews_data or not googlenews_data.get("articles"):
        raise PipelineError("Failed to fetch Google News articles. Pipeline aborted.")

    googlenews_articles = googlenews_data.get("articles", [])
    googlenews_total = googlenews_data.get("total_results", 0)

    print(f"[+] Google News: {len(googlenews_articles)} articles (total 24h results: {googlenews_total})")

    # Save Google News to logger (replaces hardcoded file logic)
    logger.save_search_results("googlenews", googlenews_data)

    # 2. Real Market Fetching (prices + CapEx)
    print("\n[*] Step 2: Fetching market data via yfinance...")
    market_metrics = market_fetcher.fetch_market_metrics()

    if not market_metrics:
        print("[!] WARNING: No market data available. Continuing with news-only analysis.")
    else:
        logger.save_search_results("market", market_metrics)

    # 2b. CapEx Fetching
    print("\n[*] Step 2b: Fetching CapEx data via yfinance...")
    capex_data = market_fetcher.fetch_capex_data()
    capex_score = market_fetcher.calculate_capex_score(capex_data)

    if capex_data:
        print(f"[+] Successfully fetched CapEx data for {len(capex_data)} tickers")
        print(f"    CapEx Score (bubble risk): {capex_score:.4f}")
        formatted_capex = _format_capex_data(capex_data)
        logger.save_search_results("capex", formatted_capex)
    else:
        print("[!] WARNING: No CapEx data available. Score defaults to neutral (0.5).")
        capex_score = 0.5

    # 3. LLM-based Sentiment Analysis (per article)
    print("\n[*] Step 3: Running LLM-based sentiment analysis per article...")

    # Reuse a single LLMEngine for both sentiment and final risk evaluation
    llm_engine = LLMEngine()

    # Run sentiment for all articles in parallel (concurrent futures)
    tasks = [_analyze_sentiment_by_article(article, llm_engine) for article in googlenews_articles]
    article_sentiments: list[dict] = await asyncio.gather(*tasks)

    # Calculate mean sentiment score
    mean_sentiment_score = (
        sum(a["sentiment_score"] for a in article_sentiments) / len(article_sentiments)
        if article_sentiments else 0.5
    )

    print(f"    Article-level sentiment scores:")
    for i, a in enumerate(article_sentiments, 1):
        print(f"      [{i}] {a['title'][:60]}... → {a['sentiment_score']:.3f}")
    print(f"    Mean Sentiment Score: {mean_sentiment_score:.4f}")

    # Save per-article sentiment JSON to logs
    sentiment_json_path = os.path.join(
        logger.run_dir, "article_sentiments.json"
    )
    sentiment_json_data = {
        "timestamp": logger.timestamp,
        "query": query,
        "num_articles": len(article_sentiments),
        "mean_sentiment_score": round(mean_sentiment_score, 4),
        "articles": [
            {
                "url": a["url"],
                "title": a["title"],
                "sentiment_score": a["sentiment_score"],
                "reason": a["reason"],
            }
            for a in article_sentiments
        ],
    }
    with open(sentiment_json_path, 'w', encoding='utf-8') as f:
        json.dump(sentiment_json_data, f, indent=4, ensure_ascii=False)
    print(f"[LOG] Article sentiment results saved to {sentiment_json_path}")

    # 4. Bubble Score (reuses mean_sentiment_score from step 3)
    print("\n[*] Step 4: Calculating final bubble score...")
    market_score = market_fetcher.calculate_market_score(market_metrics)

    print(f"    Mean Sentiment Score: {mean_sentiment_score:.4f}")
    print(f"    Market Score:       {market_score:.4f}")
    print(f"    CapEx Score:        {capex_score:.4f}")

    # Sentiment is 0.0=bearish, 1.0=bullish.
    # Direct contribution: bullish euphoria → higher bubble risk.
    final_bubble_score = (mean_sentiment_score * 0.4) + (market_score * 0.2) + (capex_score * 0.4)
    final_bubble_score *= 100
    print(f"\n[!!!] FINAL REAL BUBBLE SCORE: {final_bubble_score:.2f}%")

    # Save scores to logger
    scores = {
        "final_bubble_score": final_bubble_score,
        "sentiment_score": mean_sentiment_score,
        "market_score": market_score,
        "capex_score": capex_score,
    }
    logger.save_search_results("scores", scores)

    # 4.5 LLM Risk Evaluation (Optional — gracefully skipped if API unavailable)
    llm_content = ""
    llm_model = ""
    llm_success = False
    llm_error = None
    try:
        print("\n[*] Step 4.5: Running LLM-based risk evaluation...")
        system_prompt = build_system_prompt()
        market_summary = ""
        if market_metrics:
            for ticker, data in market_metrics.items():
                market_summary += (
                    f"- **{ticker}**: ${data['current_price_dollar']:.2f} "
                    f"(daily: {data['daily_change_percent']:+.2f}%, "
                    f"SMA 200: {data['distance_from_sma_200_percent']:+.2f}%, "
                    f"YTD: {data['ytd_change_percent']:+.2f}%)\n"
                )
        user_prompt = build_user_prompt(
            bubble_score=final_bubble_score,
            sentiment_score=mean_sentiment_score,
            market_score=market_score,
            capex_score=capex_score,
            findings=None,
            market_summary=market_summary,
        )
        llm_response = await llm_engine.generate_async(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )
        if llm_response.is_success:
            print("[+] LLM risk evaluation completed successfully")
            llm_content = llm_response.content or ""
            llm_model = llm_response.model or ""
            llm_success = True
        else:
            print(f"[!] LLM inference failed: {llm_response.error}")
            llm_error = llm_response.error
    except Exception as e:
        print(f"[!] LLM inference error: {e}")
        llm_error = str(e)

    print("=== E2E TEST COMPLETE ===")

    # Save LLM result to logger (if any)
    if llm_content or llm_error:
        logger.save_content("llm", llm_model or "unknown", llm_content or f"ERROR: {llm_error}")

    # Generate report string for console output (legacy)
    report = _generate_report(
        final_bubble_score, mean_sentiment_score, market_score, capex_score,
        [], googlenews_data, market_metrics, capex_data
    )

    # Build and save run summary via logger
    run_summary = {
        "timestamp": logger.timestamp,
        "query": query,
        "bubble_score": final_bubble_score,
        "sentiment_score": mean_sentiment_score,
        "market_score": market_score,
        "capex_score": capex_score,
        "num_articles": len(googlenews_articles),
        "llm_model": llm_model,
        "llm_success": llm_success,
        "llm_content": llm_content,
    }
    logger.save_summary(run_summary)

    return PipelineResult(
        bubble_score=final_bubble_score,
        sentiment_score=mean_sentiment_score,
        market_score=market_score,
        capex_score=capex_score,
        market_metrics=market_metrics,
        capex_data=capex_data,
        googlenews_articles=googlenews_articles,
        llm_content=llm_content,
        llm_model=llm_model,
        article_sentiments=article_sentiments,  # now available on PipelineResult
    )


def e2e_test():
    """Legacy entry point — runs pipeline and prints report."""
    report = asyncio.run(run_pipeline())
    print("\n--- FINAL REPORT ---")
    print(report)


if __name__ == "__main__":
    e2e_test()
