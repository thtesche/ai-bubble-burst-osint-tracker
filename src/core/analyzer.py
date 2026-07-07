import os
import re

class BubbleAnalyzer:
    """
    Analyzes scraped markdown content to extract bubble indicators and calculate a score.
    """
    def __init__(self, model_name="gemma-4"):
        self.model_name = model_name

    def analyze_content(self, articles: list):
        """
        Processes a list of articles and returns a structured analysis.
        In a real implementation, this would call an LLM with the markdown content.
        """
        print(f"[*] Analyzing {len(articles)} articles using {self.model_name}...")
        
        total_hype_score = 0
        findings = []

        for article in articles:
            content = article['content'].lower()
            title = article['title']
            url = article['url']
            
            # Simulated LLM Scoring Logic based on keyword density and context
            # In production, this is replaced by: 
            # response = llm.generate(f"Analyze this for bubble risk: {content}")
            
            score = 50  # Neutral baseline
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
                "title": title,
                "url": url,
                "score": score,
                "reasons": reasons
            })

        avg_score = round(total_hype_score / len(articles), 2) if articles else 0
        return avg_score, findings

    def generate_report(self, score: float, findings: list):
        """Formats the final findings into a professional report."""
        report = "### 🫧 AI Bubble Burst Report\n"
        report += f"**Current Bubble Score: {score}/100**\n\n"
        
        # Risk Assessment
        if score >= 70:
            status = "🔴 **CRITICAL RISK**"
            desc = "The market shows extreme signs of overheating and speculative mania."
        elif score >= 40:
            status = "🟡 **MODERATE RISK**"
            desc = "Mixed signals. Significant hype is present, but some fundamental caution remains."
        else:
            status = "🟢 **LOW RISK**"
            desc = "Market sentiment appears grounded in reality or lacks sufficient hype."
        
        report += f"**Status: {status}**\n"
        report += f"{desc}\n\n"

        report += "**Detailed Findings:**\n"
        for f in findings:
            report += f"- **[{f['title']}]({f['url']})**\n"
            report += f"  - Score: `{f['score']}/100`\n"
            if f['reasons']:
                report += f"  - *Reasoning:* {', '.join(f['reasons'])}\n"
            report += "\n"

        return report
