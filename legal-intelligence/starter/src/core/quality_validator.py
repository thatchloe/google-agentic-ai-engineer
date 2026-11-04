"""
Quality Validation System for Legal Intelligence AI
===================================================
Scores generated analysis on coherence, groundedness, completeness, and
structure. The scores are text heuristics: they measure form and coverage, not
legal correctness, so reports still need attorney review.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import statistics

from ..models.legal_models import AnalysisReport, ReportSection

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """Quality score with detailed breakdown."""
    overall_score: float
    coherence_score: float
    groundedness_score: float
    completeness_score: float
    structure_score: float
    feedback: List[str]


@dataclass
class ValidationResult:
    """Validation result for a report."""
    overall_score: float
    passed: bool
    section_scores: Dict[str, float]
    issues: List[str]
    recommendations: List[str]


class QualityValidator:
    """
    Validates the quality of AI-generated legal analysis.

    Section scores drive the retry loop in the agent system, and the feedback
    from each score tells the next attempt what to improve.
    """

    def __init__(self, min_quality_threshold: float = 0.7):
        """Initialize the quality validator."""
        self.min_quality_threshold = min_quality_threshold
        self.validation_history = []

    def validate_section(
        self,
        content: str,
        section_type: str,
        expected_elements: List[str]
    ) -> QualityScore:
        """Validate a single report section."""

        # Calculate individual scores
        coherence = self.calculate_coherence_score(content, section_type)
        groundedness = self.calculate_groundedness_score(content, section_type, expected_elements)
        completeness = self._calculate_completeness_score(content, expected_elements)
        structure = self._calculate_structure_score(content)

        # Calculate overall score (weighted average)
        overall = (
            coherence * 0.3 +
            groundedness * 0.3 +
            completeness * 0.25 +
            structure * 0.15
        )

        # Generate feedback
        feedback = []
        if coherence < 0.7:
            feedback.append("Improve logical flow and use more transition phrases")
        if groundedness < 0.7:
            feedback.append(f"Include more {section_type}-specific terminology and evidence")
        if completeness < 0.7:
            feedback.append(f"Address all expected elements: {', '.join(expected_elements)}")
        if structure < 0.7:
            feedback.append("Improve paragraph structure and organization")

        return QualityScore(
            overall_score=overall,
            coherence_score=coherence,
            groundedness_score=groundedness,
            completeness_score=completeness,
            structure_score=structure,
            feedback=feedback
        )

    def calculate_coherence_score(self, content: str, section_type: str) -> float:
        """
        Score logical structure, flow, and depth from 0.0 to 1.0.

        Components:
        - Paragraph structure: up to 0.3
        - Logical connectors: up to 0.2
        - Structured thinking markers: up to 0.2
        - Content depth by sentence count: up to 0.3

        Args:
            content: The text to analyze
            section_type: Type of section

        Returns:
            Coherence score between 0.0 and 1.0
        """
        if not content or not content.strip():
            return 0.0

        score = 0.0
        content_lower = content.lower()

        # 1. Paragraph structure (up to 0.3)
        paragraphs = [p for p in re.split(r'\n\s*\n', content) if p.strip()]
        if len(paragraphs) >= 3:
            score += 0.3
        elif len(paragraphs) == 2:
            score += 0.15

        # 2. Logical connectors (up to 0.2, full credit at 3 distinct connectors)
        connectors = [
            "therefore", "however", "furthermore", "moreover", "consequently",
            "additionally", "accordingly", "thus", "hence", "nevertheless",
            "in addition", "as a result", "in contrast", "on the other hand"
        ]
        connector_count = sum(
            1 for c in connectors if re.search(rf'\b{c}\b', content_lower)
        )
        score += 0.2 * min(connector_count / 3, 1.0)

        # 3. Structured thinking (up to 0.2, full credit at 3 distinct markers)
        structure_words = ["first", "second", "third", "next", "finally", "in conclusion"]
        marker_count = sum(
            1 for w in structure_words if re.search(rf'\b{w}\b', content_lower)
        )
        marker_count += len(re.findall(r'^\s*(?:\d+\.|#{1,6})\s', content, re.MULTILINE))
        score += 0.2 * min(marker_count / 3, 1.0)

        # 4. Content depth (up to 0.3, full credit at 8 sentences).
        # Requiring whitespace after the mark keeps "$2.5" as one sentence.
        sentences = [s for s in re.split(r'[.!?]+(?:\s+|$)', content) if len(s.strip()) > 3]
        score += 0.3 * min(len(sentences) / 8, 1.0)

        return min(score, 1.0)

    def calculate_groundedness_score(
        self,
        content: str,
        section_type: str,
        expected_elements: List[str]
    ) -> float:
        """
        Score domain relevance and supported reasoning from 0.0 to 1.0.

        Components:
        - Section-specific keyword coverage: up to 0.4
        - Reasoning indicators: up to 0.3
        - Expected element coverage: up to 0.3

        Args:
            content: The text to analyze
            section_type: Type of section, used to select keywords
            expected_elements: Elements that should be present

        Returns:
            Groundedness score between 0.0 and 1.0
        """
        if not content or not content.strip():
            return 0.0

        content_lower = content.lower()

        section_keywords = {
            "liability_assessment": [
                "liability", "negligence", "breach", "duty", "causation",
                "infringement", "claim", "evidence", "precedent", "defense"
            ],
            "damage_calculation": [
                "damages", "compensation", "calculation", "quantum", "lost profits",
                "royalty", "economic", "price erosion", "punitive", "mitigation"
            ],
            "prior_art_analysis": [
                "prior art", "patent", "novelty", "obviousness", "validity",
                "claims", "invalidity", "anticipation", "publication", "freedom to operate"
            ],
            "competitive_landscape": [
                "competitor", "market share", "positioning", "market", "licensing",
                "advantage", "industry", "differentiation", "barrier", "pricing"
            ],
            "risk_assessment": [
                "risk", "probability", "impact", "mitigation", "exposure",
                "likelihood", "severity", "contingency", "reputational", "uncertainty"
            ],
            "strategic_recommendations": [
                "recommend", "strategy", "implementation", "action", "priority",
                "timeline", "resources", "settlement", "metric", "objective"
            ]
        }
        keywords = section_keywords.get(
            section_type, ["analysis", "evidence", "assessment", "conclusion"]
        )

        # 1. Keyword coverage (up to 0.4, full credit at half the section's keywords)
        keyword_hits = sum(1 for k in keywords if k in content_lower)
        keyword_score = 0.4 * min(keyword_hits / (len(keywords) / 2), 1.0)

        # 2. Reasoning indicators (up to 0.3, full credit at 3 distinct indicators)
        reasoning_indicators = [
            "based on", "because", "due to", "as a result", "given that",
            "according to", "supported by", "demonstrates", "indicates",
            "evidence shows", "since", "therefore"
        ]
        reasoning_hits = sum(1 for r in reasoning_indicators if r in content_lower)
        reasoning_score = 0.3 * min(reasoning_hits / 3, 1.0)

        # 3. Expected element coverage (up to 0.3)
        if expected_elements:
            covered = sum(1 for e in expected_elements if e.lower() in content_lower)
            element_score = 0.3 * (covered / len(expected_elements))
        else:
            element_score = 0.3

        return min(keyword_score + reasoning_score + element_score, 1.0)

    def _calculate_completeness_score(self, content: str, expected_elements: List[str]) -> float:
        """Calculate how completely the content addresses requirements."""
        if not expected_elements:
            # If no specific elements expected, check general completeness
            word_count = len(content.split())
            if word_count >= 200:
                return 1.0
            elif word_count >= 100:
                return 0.7
            elif word_count >= 50:
                return 0.5
            else:
                return 0.3

        # Check coverage of expected elements
        content_lower = content.lower()
        covered_elements = sum(1 for element in expected_elements
                             if element.lower() in content_lower)

        coverage_ratio = covered_elements / len(expected_elements)

        # Also consider content length
        word_count = len(content.split())
        length_score = min(word_count / 200, 1.0)  # Expect at least 200 words

        # Combined score
        return (coverage_ratio * 0.7) + (length_score * 0.3)

    def _calculate_structure_score(self, content: str) -> float:
        """Calculate structural quality of the content."""
        score = 0.0

        # Check for paragraphs
        paragraphs = content.split('\n\n')
        if len(paragraphs) >= 3:
            score += 0.3
        elif len(paragraphs) >= 2:
            score += 0.2
        elif len(paragraphs) >= 1:
            score += 0.1

        # Check for lists or bullet points
        has_lists = any(marker in content for marker in ['•', '-', '*', '1.', '2.', '3.'])
        if has_lists:
            score += 0.2

        # Check for headers or emphasized text
        has_headers = any(line.isupper() or line.startswith('#')
                        for line in content.split('\n') if len(line.strip()) > 0)
        if has_headers:
            score += 0.1

        # Check sentence variety
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 10]
        if len(sentences) >= 3:
            sentence_lengths = [len(s.split()) for s in sentences]
            if len(set(sentence_lengths)) >= 3:  # Variety in sentence length
                score += 0.2

        # Check for conclusion indicators
        conclusion_indicators = ['conclusion', 'summary', 'therefore', 'in summary', 'overall']
        has_conclusion = any(indicator in content.lower() for indicator in conclusion_indicators)
        if has_conclusion:
            score += 0.2

        return min(score, 1.0)

    def validate_report(self, report: AnalysisReport) -> ValidationResult:
        """Validate a complete report."""
        section_scores = {}
        all_issues = []
        all_recommendations = []

        # Validate each section
        for section in report.sections:
            expected_elements = self._get_expected_elements_for_section(section.type)
            quality = self.validate_section(
                content=section.content,
                section_type=section.type,
                expected_elements=expected_elements
            )

            section_scores[section.type] = quality.overall_score

            # Collect issues and recommendations
            if quality.overall_score < self.min_quality_threshold:
                all_issues.append(f"{section.title}: Score {quality.overall_score:.2f} below threshold")
                all_recommendations.extend(quality.feedback)

        # Calculate overall score
        overall_score = statistics.mean(section_scores.values()) if section_scores else 0.0

        # Determine if report passes
        passed = overall_score >= self.min_quality_threshold

        # Store in history
        self.validation_history.append({
            "timestamp": report.timestamp,
            "overall_score": overall_score,
            "passed": passed
        })

        return ValidationResult(
            overall_score=overall_score,
            passed=passed,
            section_scores=section_scores,
            issues=all_issues,
            recommendations=all_recommendations[:5]  # Top 5 recommendations
        )

    def _get_expected_elements_for_section(self, section_type: str) -> List[str]:
        """Get expected elements for a section type."""
        elements_map = {
            "liability_assessment": ["liability", "breach", "duty", "causation"],
            "damage_calculation": ["damages", "calculation", "compensation", "quantum"],
            "prior_art_analysis": ["prior art", "patent", "novelty", "claims"],
            "competitive_landscape": ["competitors", "market", "positioning", "advantage"],
            "risk_assessment": ["risk", "probability", "impact", "mitigation"],
            "strategic_recommendations": ["recommendation", "strategy", "implementation", "timeline"]
        }
        return elements_map.get(section_type, ["analysis", "assessment"])

    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get quality metrics from validation history."""
        if not self.validation_history:
            return {"error": "No validation history available"}

        recent = self.validation_history[-10:]  # Last 10 validations

        return {
            "total_validations": len(self.validation_history),
            "recent_average_score": statistics.mean([v["overall_score"] for v in recent]),
            "recent_pass_rate": sum(1 for v in recent if v["passed"]) / len(recent),
            "threshold": self.min_quality_threshold
        }