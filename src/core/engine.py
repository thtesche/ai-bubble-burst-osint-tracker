import re

class ScoringEngine:
    """
    Processes extracted news content and calculates a Hype Score.
    This class relies solely on standard Python and is therefore testable.
    """
    def __init__(self, hype_keywords=None):
        self.hype_keywords = hype_keywords or [
            "revolution", "unprecedented", "exponential", "breakthrough", 
            "massive", "skyrocketing", "unlimited", "game-changer",
            "bubble", "speculation", "overvalued", "crash", "risk"
        ]

    def analyze_sentiment(self, contents: list[str]) -> float:
        """
        Analyzes the frequency of Hype keywords in the texts.
        Returns a value between 0 (neutral) and 1 (extreme hype/risk).
        """
        if not contents:
            return 0.0

        total_hits = 0
        total_words = 0

        for text in contents:
            text_lower = text.lower()
            words = re.findall(r'\w+', text_lower)
            total_words += len(words)
            
            for word in self.hype_keywords:
                # We count hits (simple implementation for MVP)
                total_hits += text_lower.count(word)

        if total_words == 0:
            return 0.0

        # Normalization: We assume that a very high density of keywords
        # (e.g. 1% of all words) yields a Score of 1.0.
        score = (total_hits / total_words) * 100
        return min(score, 1.0)

    def calculate_final_score(self, sentiment_score: float, market_score: float, capex_score: float = 0.5) -> float:
        """
        Combines the scores into a final 0-100% value.
        Weighting: 40% Sentiment, 20% Market, 40% CapEx (for MVP).
        """
        combined = (sentiment_score * 0.4) + (market_score * 0.2) + (capex_score * 0.4)
        return combined * 100
