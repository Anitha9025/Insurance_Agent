import re
from typing import Tuple

CATEGORY_KEYWORDS = {
    "Police Report": [
        r"police", r"accident", r"officer", r"badge", r"collision", r"precinct", r"traffic report", r"fault"
    ],
    "Repair Estimate": [
        r"repair", r"estimate", r"auto body", r"parts", r"labor", r"garage", r"bodywork", r"replacement", r"quote"
    ],
    "Invoice / Receipt": [
        r"invoice", r"receipt", r"total", r"subtotal", r"balance due", r"bill", r"amount paid", r"tax"
    ],
    "Medical Report": [
        r"hospital", r"medical", r"physician", r"doctor", r"patient", r"diagnosis", r"treatment", r"clinic", r"admission"
    ],
    "Damage Photo": [
        r"photo", r"image", r"damage", r"impact", r"frontal", r"bumper", r"scratch"
    ],
    "Policy Schedule": [
        r"policy", r"coverage", r"deductible", r"premium", r"insured", r"endorsement", r"rider", r"effective date"
    ],
    "ID Proof": [
        r"ssn", r"driver", r"license", r"passport", r"national id", r"state id", r"identity"
    ]
}

class DocumentClassifier:
    """Classifies document text and file metadata into standard Document Categories."""

    @staticmethod
    def classify(raw_text: str, file_name: str = "", category_hint: str = None) -> Tuple[str, float]:
        """Classifies document content and returns (category_name, confidence_score)."""
        if category_hint and category_hint in CATEGORY_KEYWORDS:
            return category_hint, 95.0

        text_lower = f"{file_name} {raw_text}".lower()
        scores = {}

        for category, patterns in CATEGORY_KEYWORDS.items():
            match_count = 0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    match_count += 1
            if match_count > 0:
                scores[category] = match_count

        if not scores:
            return "Unknown", 50.0

        top_category = max(scores, key=scores.get)
        match_count = scores[top_category]
        confidence = min(99.0, 60.0 + (match_count * 10.0))
        return top_category, confidence
