import os

class BubbleAnalyzer:
    """
    Analyzes scraped markdown content AND quantitative market data.
    """
    def __init__(self, model_name="gemma-4"):
        self.model_name = model_name

    def analyze_content(self, articles: list, market_data: dict = None):
        """
        Combines qualitative (news) and quantitative (market) analysis.
        """
        print(f"[*] Analyzing {len(articles)} articles and market data...")
        
        # --- Part 1: Qualitative Sentiment (News) ---
        total_hype_score = 0
        findings = []

        for article in articles:
            content = article['content'].lower()
            title = article['title']
            url = article['url']
            
            score = 50 # Neutral baseline
            reasons = []

            # Indicators for High Risk (Bubble)
            if any(word in content for word in ['bubble', 'crash', 'burst', 'overvalued', 'speculation', 'hype']):
                score += 30
                reasons.append("High frequency of bubble/crash terminology.")
            
            if any(word in content for word in ['unprecedented', 'exponential', 'infinite', 'revolution']):
                score += 15
                reasons.append("Extreme hyperbolic language detected.")

            # Indicators for Low Risk (Stability)
            if any(word in content for word in ['stable', 'fundamentals', 'earnings', 'valuation', 'moderate']):
                score -= 20
                reasons.append("Focus on fundamentals and stability.")

            # Clamp score between 0 and 100
            score = max(0, min(100, score))
            total_hype_score += score
            
            findings.append({
                "title": title, "url": url, "score": score, "reasons": reasons
            })

        qualitative_score = round(total_hype_score / len(articles), 2) if articles else 50

        # --- Part 2: Quantitative Market Score ---
        quantitative_score = 50 # Neutral baseline
        market_summary = ""

        if market_data:
            print("[*] Calculating quantitative score from market data...")
            market_points = []
            
            for ticker, data in market_data.items():
                # Factor 1: Price Momentum (High growth = higher bubble risk)
                # We map +20% change to 100 points, 0% to 50 points
                momentum_score = 50 + (data['pct_change_30d'] * 2.5)
                momentum_score = max(0, min(100, momentum_score))
                market_points.append(momentum_score)

                # Factor 2: Volatility (High volatility = higher risk/bubble)
                vol_score = min(100, data['annualized_volatility'] * 2) # Example scaling
                market_points.append(vol_score)

                market_summary += f"- **{ticker}**: {data['pct_change_30d']}% (30d), Vol: {data['annualized_volatility']}%\n"

            if market_points:
                quantitative_score = sum(market_points) / len(market_points)

        # --- Part 3: Final Weighted Score ---
        # 60% Qualitative (News) | 40% Quantitative (Market)
        final_score = round((qualitative_score * 0.6) + (quantitative_score * 0.4), 2)

        return final_score, findings, market_summary

    def generate_report(self, score: float, findings: list, market_summary: str = ""):
        """Formats the final findings into a professional report."""
        report = "### 🫧 AI Bubble Burst Report\n"
        report += f"**Current Bubble Score: {score}/100**\n\n"
        
        # Risk Assessment
        if score >= 70:
            status, desc = "🔴 **CRITICAL RISK**", "Extreme signs of overheating and speculative mania."
        elif score >= 40:
            status, desc = "🟡 **MODERATE RISK**", "Mixed signals. Significant hype is present, but some fundamental caution remains."
        else:
            status, desc = "🟢 **LOW RISK**", "Market sentiment appears stable or grounded."
        
        report += f"**Status: {status}**\n"
        report += f"{desc}\n\n"

        if market_summary:
            report += "**📊 Market Data (Quantitative):**\n"
            report += f"{market_summary}\n"

        report += "**📰 News Analysis (Qualitative):**\n"
        for f in findings:
            report += f"- **[{f['title']}]({f['url']})** (Score: `{f['score']}`)\n"
            if f['reasons']:
                report += f"  - *Reasoning:* {', '.join(f['reasons'])}\n"
            report += "\n"

        return report
