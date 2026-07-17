"""
Bubble Risk Prompt Templates

Provides structured prompts for LLM-based AI bubble risk assessment.
The LLM receives the full pipeline analysis results and returns a
structured risk evaluation with reasoning.
"""

from typing import Optional


def build_system_prompt() -> str:
    """Returns the system prompt for bubble risk analysis."""
    return (
        "You are a senior market analyst specializing in technology valuations "
        "and bubble risk assessment. Your task is to evaluate whether the AI "
        "market is in a speculative bubble and assess the probability of a "
        "significant market correction or crash.\n\n"
        "You receive quantitative data (market scores, CapEx trends, sentiment "
        "scores) and qualitative data (news articles) about the AI market. "
        "Your job is to synthesize this information and provide a structured "
        "risk assessment.\n\n"
        "IMPORTANT: Output ONLY the final structured analysis. Do NOT show "
        "your thinking process, reasoning steps, or internal monologue. "
        "Do NOT use phrases like 'Here's a thinking process:' or 'Step 1:' "
        "or any intermediate reasoning. Output only the final structured "
        "response in the requested format.\n\n"
        "Always base your analysis on the provided data only. Do not "
        "hallucinate information. If data is missing or insufficient, state "
        "so explicitly in your response."
    )


def build_user_prompt(
    bubble_score: float,
    sentiment_score: float,
    market_score: float,
    capex_score: float,
    findings: Optional[list[dict]] = None,
    market_summary: str = "",
) -> str:
    """
    Builds the user prompt with all pipeline data for LLM evaluation.

    Args:
        bubble_score: Final pipeline bubble score (0-100).
        sentiment_score: News sentiment score (0-1).
        market_score: Market performance score (0-1).
        capex_score: CapEx investment trend score (0-1).
        findings: List of individual article analysis findings.
        market_summary: Formatted market data summary string.

    Returns:
        Formatted prompt string for the LLM.
    """
    prompt_parts = [
        f"### AI Bubble Risk Assessment — Pipeline Analysis Results\n\n",
        f"**Scoring Reference (interpret all scores below with these bounds):**\n",
        f"- **Bubble Score Range: 0–100%**\n",
        f"  - 0–40% = LOW RISK (market appears stable or grounded)\n",
        f"  - 40–70% = MODERATE RISK (mixed signals, some hype present)\n",
        f"  - 70–100% = CRITICAL RISK (extreme overheating, speculative mania)\n",
        f"\n",
        f"- **Sentiment Score (News): 0.0–1.0**\n",
        f"  - 0.0 = strongly bearish (warnings of bubble, overvaluation, crash)\n",
        f"  - 0.5 = neutral (balanced reporting, no clear bias)\n",
        f"  - 1.0 = strongly bullish (praises AI growth, explosive expansion)\n",
        f"  → Inverted for risk: bullish news → higher bubble risk\n",
        f"\n",
        f"- **Market Score (Prices): 0.0–1.0**\n",
        f"  - 0.0 = stable or under fair value\n",
        f"    (price ≤ 20% above 200-day SMA AND YTD ≤ 30%)\n",
        f"  - 0.5 = moderately elevated\n",
        f"    (price 20–50% above SMA 200 OR YTD 30–70%)\n",
        f"  - 1.0 = extreme overvaluation / bubble territory\n",
        f"    (price ≥ 50% above 200-day SMA AND YTD ≥ 70%)\n",
        f"  → Computed from distance to 200-day SMA and Year-to-Date performance\n",
        f"\n",
        f"- **CapEx Score (Investments): 0.0–1.0**\n",
        f"  - 0.0 = stable or declining CapEx (no infrastructure rush)\n",
        f"  - 0.5 = moderate CapEx growth\n",
        f"  - 1.0 = rapidly expanding CapEx (aggressive infrastructure buildout)\n",
        f"  → Rising CapEx is a bubble signal (companies racing to build AI capacity)\n",
        f"\n",
        f"**Pipeline Output (Full Score: {bubble_score:.1f}%):**\n",
        f"- Sentiment Score (News):  {sentiment_score:.4f}\n",
        f"- Market Score (Prices):  {market_score:.4f}\n",
        f"- CapEx Score (Investments): {capex_score:.4f}\n\n",
    ]

    if market_summary:
        prompt_parts.append(f"**Market Data:**\n{market_summary}\n\n")

    if findings and len(findings) > 0:
        prompt_parts.append("**News Article Analysis:**\n")
        for i, f in enumerate(findings, 1):
            title = f.get("title", "No Title")
            score_val = f.get("score", 0)
            reasons = f.get("reasons", [])
            prompt_parts.append(f"- Article {i}: \"{title}\" (score: {score_val})")
            if reasons:
                prompt_parts.append(f"  Indicators: {', '.join(reasons)}")
        prompt_parts.append("\n")

    prompt_parts.append(
        "Please provide a structured response with the following format:\n\n"
        "## Risk Evaluation\n"
        "- **Bubble Probability Rating:** (Low/Medium/High/Critical)\n"
        "- **Confidence Level:** (Low/Medium/High)\n"
        "- **Key Bubble Indicators:** (bullet points of the most concerning signals)\n\n"
        "## Market Health Assessment\n"
        "- **Valuation Concerns:** (comment on current valuations)\n"
        "- **Investment Trends:** (comment on CapEx/infrastructure spending)\n"
        "- **Sentiment Analysis:** (comment on media sentiment)\n\n"
        "## Risk Factors\n"
        "- **Bullish arguments:** (reasons the market might NOT be a bubble)\n"
        "- **Bearish arguments:** (reasons the market COULD be a bubble)\n\n"
        "## Prediction\n"
        "- **Timeframe for potential correction:** (if any)\n"
        "- **Likelihood of significant correction (>20% drop):** (percentage estimate)\n\n"
        "## Final Verdict\n"
        "A concise summary of your assessment.\n"
    )

    return "".join(prompt_parts)
