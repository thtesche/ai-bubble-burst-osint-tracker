import re

class ScoringEngine:
    """
    Verarbeitet extrahierte News-Inhalte und berechnet einen Hype-Score.
    Diese Klasse ist rein auf Standard-Python angewiesen und somit testbar.
    """
    def __init__(self, hype_keywords=None):
        self.hype_keywords = hype_keywords or [
            "revolution", "unprecedented", "exponential", "breakthrough", 
            "massive", "skyrocketing", "unlimited", "game-changer",
            "bubble", "speculation", "overvalued", "crash", "risk"
        ]

    def analyze_sentiment(self, contents: list[str]) -> float:
        """
        Analysiert die Häufigkeit von Hype-Keywords in den Texten.
        Gibt einen Wert zwischen 0 (neutral) und 1 (extremer Hype/Risiko) zurück.
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
                # Wir zählen Treffer (einfache Implementierung für MVP)
                total_hits += text_lower.count(word)

        if total_words == 0:
            return 0.0

        # Normalisierung: Wir nehmen an, dass eine sehr hohe Dichte an Keywords 
        # (z.B. 1% aller Wörter) einen Score von 1.0 ergibt.
        score = (total_hits / total_words) * 100
        return min(score, 1.0)

    def calculate_final_score(self, sentiment_score: float, market_score: float, capex_score: float = 0.5) -> float:
        """
        Kombiniert die Scores zu einem finalen 0-100% Wert.
        Gewichtung: 40% Sentiment, 20% Market, 40% CapEx (für MVP).
        """
        combined = (sentiment_score * 0.4) + (market_score * 0.2) + (capex_score * 0.4)
        return combined * 100
