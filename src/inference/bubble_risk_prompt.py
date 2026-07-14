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
