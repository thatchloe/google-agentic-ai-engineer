#!/usr/bin/env python3
"""
Offline validation run: persona scores and quality ranking.

Needs no credentials. Exits non-zero if a persona scores below 0.8 or the
high, medium, and low quality samples do not rank in that order.

Usage:
    python run_validation.py
"""

import sys

from src.core.quality_validator import QualityValidator
from src.prompts.personas import (
    BUSINESS_ANALYST_PERSONA,
    MARKET_RESEARCHER_PERSONA,
    STRATEGIC_CONSULTANT_PERSONA,
    LegalPersonas,
)
from tests.test_todos import TestQualityRanking

PERSONA_THRESHOLD = 0.8


def check_personas() -> bool:
    """Print each persona's validation score and return True if all pass."""
    validator = LegalPersonas()
    print(f"Persona validation (minimum {PERSONA_THRESHOLD})")
    passed = True
    for name, text in [
        ("BUSINESS_ANALYST_PERSONA", BUSINESS_ANALYST_PERSONA),
        ("MARKET_RESEARCHER_PERSONA", MARKET_RESEARCHER_PERSONA),
        ("STRATEGIC_CONSULTANT_PERSONA", STRATEGIC_CONSULTANT_PERSONA),
    ]:
        score = validator.validate_persona(text)["score"]
        passed = passed and score >= PERSONA_THRESHOLD
        print(f"  {name:<30} score={score:.2f}  words={len(text.split())}")
    return passed


def check_ranking() -> bool:
    """Print scores for the three samples and return True if they rank correctly."""
    validator = QualityValidator()
    elements = ["claims", "evidence", "probability", "precedent"]
    samples = [
        ("high", TestQualityRanking.HIGH),
        ("medium", TestQualityRanking.MEDIUM),
        ("low", TestQualityRanking.LOW),
    ]
    print(f"\nQuality ranking (threshold {validator.min_quality_threshold})")
    print(f"  {'sample':<8}{'coherence':>11}{'groundedness':>14}{'overall':>9}  gate")
    results = []
    for name, text in samples:
        score = validator.validate_section(text, "liability_assessment", elements)
        results.append(score)
        gate = "pass" if score.overall_score >= validator.min_quality_threshold else "retry"
        print(
            f"  {name:<8}{score.coherence_score:>11.3f}"
            f"{score.groundedness_score:>14.3f}{score.overall_score:>9.3f}  {gate}"
        )
    high, medium, low = results
    return all(
        getattr(high, field) > getattr(medium, field) > getattr(low, field)
        for field in ("coherence_score", "groundedness_score", "overall_score")
    )


def main() -> int:
    personas_ok = check_personas()
    ranking_ok = check_ranking()
    print(f"\nPersonas: {'PASSED' if personas_ok else 'FAILED'}")
    print(f"Ranking high > medium > low: {'PASSED' if ranking_ok else 'FAILED'}")
    return 0 if personas_ok and ranking_ok else 1


if __name__ == "__main__":
    sys.exit(main())
