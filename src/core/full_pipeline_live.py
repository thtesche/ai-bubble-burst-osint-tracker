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
from src.core.engine import ScoringEngine
from src.inference import LLMEngine, LLMResponse, build_system_prompt, build_user_prompt


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


class PipelineError(Exception):
    """Raised when the pipeline cannot proceed due to missing or invalid data."""
    pass


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
            report += f"- **{ticker}**: ${data['current_price']:.2f} (daily: {data['daily_change_pct']:+.2f}%, 5d: {data['five_day_change_pct']:+.2f}%)\n"
        report += "\n"

    # CapEx Data
    if capex_data:
        report += "**💰 CapEx Summary:**\n"
        for ticker, data in capex_data.items():
            quarterly = data.get("quarterly_capex", {})
            if quarterly:
                sorted_q = sorted(quarterly.keys(), reverse=True)[:3]
                latest_vals = [abs(float(quarterly[q])) for q in sorted_q]
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

    # 1. Setup (Dependency Injection)
    engine = ScoringEngine()
    
    if googlenews_fetcher is None:
        googlenews_fetcher = GoogleNewsFetcher(
            query=query, limit=10
        )
        
    if market_fetcher is None:
        market_fetcher = MarketDataFetcher(tickers=tickers)

    # 2. Google News Fetching (async now — scrapes URLs with Firecrawl internally)
    print("\n[*] Step 1: Fetching news via Google News RSS + Firecrawl...")
    googlenews_data = await googlenews_fetcher.fetch_articles()

    if not googlenews_data or not googlenews_data.get("articles"):
        raise PipelineError("Failed to fetch Google News articles. Pipeline aborted.")

    googlenews_articles = googlenews_data.get("articles", [])
    googlenews_total = googlenews_data.get("total_results", 0)
    
    # Extract contents for the scoring engine
    googlenews_contents = [
        a.get("content", a.get("description", ""))
        for a in googlenews_articles
    ]

    print(f"[+] Google News: {len(googlenews_articles)} articles (total 24h results: {googlenews_total})")

    # Save Google News to JSON for quality inspection
    current_dir = os.path.dirname(os.path.abspath(__file__))
    actual_root = os.path.dirname(os.path.dirname(current_dir))
    log_dir = os.path.join(actual_root, "logs", "runs")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    googlenews_json_path = os.path.join(log_dir, f"googlenews_raw_{timestamp}.json")

    with open(googlenews_json_path, "w", encoding="utf-8") as f:
        json.dump(googlenews_data, f, indent=4, ensure_ascii=False)
    print(f"[+] Google News data saved to: {googlenews_json_path}")

    # 3. Real Market Fetching (prices + CapEx)
    print("\n[*] Step 2: Fetching market data via yfinance...")
    market_metrics = market_fetcher.fetch_market_metrics()

    if not market_metrics:
        print("[!] WARNING: No market data available. Continuing with news-only analysis.")

    # 3b. CapEx Fetching
    print("\n[*] Step 2b: Fetching CapEx data via yfinance...")
    capex_data = market_fetcher.fetch_capex_data()
    capex_score = market_fetcher.calculate_capex_score(capex_data)

    if capex_data:
        print(f"[+] Successfully fetched CapEx data for {len(capex_data)} tickers")
        print(f"    CapEx Score (bubble risk): {capex_score:.4f}")
    else:
        print("[!] WARNING: No CapEx data available. Score defaults to neutral (0.5).")
        capex_score = 0.5

    # 4. Scoring
    print("\n[*] Step 3: Calculating REAL score...")
    sentiment_score = engine.analyze_sentiment(googlenews_contents)
    market_score = market_fetcher.calculate_market_score(market_metrics)

    print(f"    Real Sentiment Score: {sentiment_score:.4f}")
    print(f"    Real Market Score:    {market_score:.4f}")
    print(f"    CapEx Score:          {capex_score:.4f}")

    final_bubble_score = engine.calculate_final_score(
        sentiment_score, market_score, capex_score
    )
    print(f"\n[!!!] FINAL REAL BUBBLE SCORE: {final_bubble_score:.2f}%")

    # 4.5 LLM Inference (Optional — gracefully skipped if API unavailable)
    llm_content = ""
    llm_model = ""
    try:
        llm_engine = LLMEngine()
        print("\n[*] Step 4.5: Running LLM-based risk evaluation...")
        system_prompt = build_system_prompt()
        market_summary = ""
        if market_metrics:
            for ticker, data in market_metrics.items():
                market_summary += (
                    f"- **{ticker}**: ${data['current_price']:.2f} "
                    f"(daily: {data['daily_change_pct']:+.2f}%, "
                    f"5d: {data['five_day_change_pct']:+.2f}%)\n"
                )
        user_prompt = build_user_prompt(
            bubble_score=final_bubble_score,
            sentiment_score=sentiment_score,
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
        else:
            print(f"[!] LLM inference failed: {llm_response.error}")
    except Exception as e:
        print(f"[!] LLM inference error: {e}")

    print("=== E2E TEST COMPLETE ===")

    # Generate report string for console output (legacy)
    report = _generate_report(
        final_bubble_score, sentiment_score, market_score, capex_score,
        [], googlenews_data, market_metrics, capex_data
    )

    return PipelineResult(
        bubble_score=final_bubble_score,
        sentiment_score=sentiment_score,
        market_score=market_score,
        capex_score=capex_score,
        market_metrics=market_metrics,
        capex_data=capex_data,
        googlenews_articles=googlenews_articles,
        llm_content=llm_content,
        llm_model=llm_model,
    )


def e2e_test():
    """Legacy entry point — runs pipeline and prints report."""
    report = asyncio.run(run_pipeline())
    print("\n--- FINAL REPORT ---")
    print(report)


if __name__ == "__main__":
    e2e_test()
