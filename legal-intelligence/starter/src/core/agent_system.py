"""
Legal Intelligence Agent System - Core Agent Implementation
===========================================================
Connects to Gemini on Vertex AI and runs the specialist personas in sequence.
Each section receives earlier sections as context, is scored by the quality
validator, and is regenerated with feedback when it falls below the threshold.
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

# Google AI imports
from google import genai
from google.genai import types

# Internal imports
from ..models.legal_models import (
    LegalScenario,
    AnalysisReport,
    AgentResponse,
    ReportSection,
    TokenUsage
)
from ..prompts.personas import LegalPersonas
from .quality_validator import QualityValidator

logger = logging.getLogger(__name__)

# Estimated list prices in USD per 1M tokens: (input, output)
MODEL_PRICING = {
    "gemini-2.0-flash": (0.15, 0.60),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-3.5-flash": (1.50, 9.00),
}
# Unknown models use the highest listed rates so cost is not understated
DEFAULT_PRICING = (1.50, 9.00)


class LegalIntelligenceAgent:
    """
    Main orchestrator for the Legal Intelligence AI System.

    Runs the section sequence, chains context between specialists, enforces the
    quality threshold, and tracks tokens, cost, timing, and success rate.
    """

    def __init__(self, project_id: str, location: str = "us-central1", model_name: str = "gemini-2.0-flash"):
        """Initialize the Legal Intelligence Agent system."""
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.client = None
        self.model = None
        self.initialized = False

        # Components
        self.personas = LegalPersonas()
        self.quality_validator = QualityValidator()

        # Performance tracking
        self.token_usage_history = []
        self.processing_times = []
        self.success_count = 0
        self.total_attempts = 0

        # Configuration
        self.generation_config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            # Thinking models spend part of this budget before writing, so a
            # small limit truncates sections mid-sentence
            max_output_tokens=8192,
        )

        logger.info(f"LegalIntelligenceAgent initialized for project {project_id}")

    def initialize_vertex_ai(self) -> bool:
        """
        Create the Vertex AI client and verify it with a small test prompt.

        Returns:
            True if the model responded, False otherwise. Errors are logged, not raised.
        """
        try:
            logger.info(f"Initializing Vertex AI for project: {self.project_id}")

            # Connect through the Google Gen AI SDK using its Vertex AI backend
            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )

            # client.models is the SDK's generation interface
            self.model = self.client.models

            # Send a small prompt so bad credentials or model names fail at startup
            response = self.model.generate_content(
                model=self.model_name,
                contents="Reply with the single word OK."
            )
            if not response or not response.text:
                logger.error("Vertex AI connection test returned an empty response")
                self.initialized = False
                return False

            self.initialized = True
            logger.info(f"Vertex AI initialized with model {self.model_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {str(e)}")
            self.initialized = False
            return False

    def generate_section_content(
        self,
        persona: str,
        section_type: str,
        scenario: LegalScenario,
        previous_sections: List[ReportSection] = None
    ) -> Tuple[str, TokenUsage, float]:
        """
        Generate one report section, retrying failures with exponential backoff.

        Args:
            persona: The agent persona text (from personas.py)
            section_type: Type of section (e.g., "liability_assessment")
            scenario: The legal case to analyze
            previous_sections: Previous sections for context chaining

        Returns:
            Tuple of (content, token_usage, cost)

        Raises:
            RuntimeError: If the agent is not initialized or all attempts fail
        """
        if not self.initialized:
            raise RuntimeError("Agent system not initialized. Call initialize_vertex_ai() first.")

        start_time = time.time()
        previous_sections = previous_sections or []

        # Build the comprehensive prompt
        prompt = self._build_prompt(persona, section_type, scenario, previous_sections)

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            self.total_attempts += 1
            try:
                response = self.model.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=self.generation_config
                )

                content = response.text
                if not content or not content.strip():
                    raise ValueError(f"Model returned empty content for {section_type}")

                # Derive output from the total so billed thinking tokens are
                # counted; candidates_token_count leaves them out
                usage = response.usage_metadata
                input_tokens = usage.prompt_token_count or 0
                total_tokens = usage.total_token_count or 0
                token_usage = TokenUsage(
                    input_tokens=input_tokens,
                    output_tokens=total_tokens - input_tokens,
                    total_tokens=total_tokens
                )
                cost = self._calculate_cost(token_usage)

                self.token_usage_history.append(token_usage)
                self.processing_times.append(time.time() - start_time)
                self.success_count += 1

                logger.info(
                    f"Generated {section_type}: {token_usage.total_tokens} tokens, ${cost:.4f}"
                )
                return content, token_usage, cost

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Generation attempt {attempt + 1}/{max_retries} failed for "
                    f"{section_type}: {str(e)}"
                )
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

        raise RuntimeError(
            f"Failed to generate {section_type} after {max_retries} attempts: {last_error}"
        )

    async def generate_complete_report(self, scenario: LegalScenario) -> AnalysisReport:
        """
        Generate the full report by running each specialist in sequence.

        Each section is regenerated with validator feedback when it scores below the
        threshold, and the best attempt is kept. A section that cannot be generated
        is marked as unavailable so the remaining sections are still delivered.

        Args:
            scenario: The legal case to analyze

        Returns:
            The assembled report; metadata records retries and failed sections

        Raises:
            RuntimeError: If no section could be generated
        """
        logger.info(f"Starting complete report generation for case: {scenario.case_name}")
        start_time = time.time()

        section_config = [
            ("liability_assessment", "business_analyst"),
            ("damage_calculation", "business_analyst"),
            ("prior_art_analysis", "market_researcher"),
            ("competitive_landscape", "market_researcher"),
            ("risk_assessment", "strategic_consultant"),
            ("strategic_recommendations", "strategic_consultant"),
        ]
        quality_threshold = self.quality_validator.min_quality_threshold
        max_quality_retries = 2

        sections: List[ReportSection] = []
        total_cost = 0.0
        total_tokens = 0
        quality_retries = 0
        failed_sections: List[str] = []

        for section_type, persona_type in section_config:
            persona = self.personas.get_persona(persona_type)
            expected_elements = self._get_expected_elements(section_type)
            best_content, best_score = None, -1.0
            section_tokens = 0
            section_cost = 0.0
            attempt_persona = persona

            # Quality loop: regenerate with the validator's feedback until the
            # section passes, then keep the best-scoring attempt.
            for attempt in range(max_quality_retries + 1):
                # to_thread keeps the blocking SDK call off the event loop
                try:
                    content, token_usage, cost = await asyncio.to_thread(
                        self.generate_section_content,
                        attempt_persona,
                        section_type,
                        scenario,
                        [s for s in sections if s.type not in failed_sections]
                    )
                except Exception as e:
                    logger.error(f"Generation failed for {section_type}: {str(e)}")
                    break

                section_tokens += token_usage.total_tokens
                section_cost += cost

                quality = self.quality_validator.validate_section(
                    content, section_type, expected_elements
                )
                if quality.overall_score > best_score:
                    best_content, best_score = content, quality.overall_score

                if quality.overall_score >= quality_threshold:
                    break

                if attempt < max_quality_retries:
                    quality_retries += 1
                    logger.warning(
                        f"{section_type} scored {quality.overall_score:.2f}, "
                        f"below {quality_threshold}; retrying"
                    )
                    attempt_persona = self._build_retry_persona(persona, quality.feedback)

            if best_content is None:
                failed_sections.append(section_type)
                best_content = (
                    f"[Section unavailable] The {self._get_section_title(section_type)} "
                    "section could not be generated. Rerun the analysis to complete it."
                )
                best_score = 0.0
            elif best_score < quality_threshold:
                logger.warning(f"{section_type} kept at {best_score:.2f} after all retries")

            logger.info(
                f"Section complete: type={section_type} agent={persona_type} "
                f"quality={best_score:.2f} tokens={section_tokens} cost=${section_cost:.4f}"
            )

            sections.append(ReportSection(
                type=section_type,
                title=self._get_section_title(section_type),
                content=best_content,
                agent_type=persona_type,
                quality_score=best_score,
                tokens_used=section_tokens,
                cost=section_cost,
                timestamp=datetime.now().isoformat()
            ))
            total_tokens += section_tokens
            total_cost += section_cost

        if len(failed_sections) == len(section_config):
            raise RuntimeError("Report generation failed: no section could be generated")

        input_rate, output_rate = self._get_pricing()
        processing_time = time.time() - start_time
        logger.info(
            f"Report complete: case={scenario.case_name} sections={len(sections)} "
            f"failed={len(failed_sections)} tokens={total_tokens} "
            f"cost=${total_cost:.4f} time={processing_time:.1f}s"
        )

        return AnalysisReport(
            scenario=scenario,
            sections=sections,
            executive_summary=self._generate_executive_summary(sections, scenario),
            total_cost=total_cost,
            total_tokens=total_tokens,
            processing_time=processing_time,
            confidence_score=sum(s.quality_score for s in sections) / len(sections),
            timestamp=datetime.now().isoformat(),
            metadata={
                "model": self.model_name,
                "status": "partial" if failed_sections else "complete",
                "failed_sections": failed_sections,
                "cost_basis": (
                    f"Estimate at ${input_rate:.2f} input and ${output_rate:.2f} "
                    "output per 1M tokens"
                ),
                "quality_threshold": quality_threshold,
                "quality_retries": quality_retries,
                "sections_below_threshold": [
                    s.type for s in sections if s.quality_score < quality_threshold
                ]
            }
        )

    def _build_retry_persona(self, persona: str, feedback: List[str]) -> str:
        """Add the validator's feedback to a persona for a quality retry."""
        issues = "\n".join(f"- {item}" for item in feedback)
        return (
            f"{persona}\n\nQUALITY IMPROVEMENT REQUIRED:\n"
            f"Your previous draft of this section fell short. Address these issues:\n{issues}"
        )

    def _build_prompt(
        self,
        persona: str,
        section_type: str,
        scenario: LegalScenario,
        previous_sections: List[ReportSection]
    ) -> str:
        """Build a comprehensive prompt combining persona, context, and chain-of-thought instructions."""

        # Start with the persona
        prompt = persona + "\n\n"

        # Add chain-of-thought reasoning instructions
        prompt += """
REASONING INSTRUCTIONS:
You must use step-by-step reasoning to analyze this legal case. Structure your analysis as follows:
1. First, identify the key legal issues
2. Second, analyze the relevant facts
3. Third, apply legal principles
4. Finally, provide your conclusions

Think through each step carefully before moving to the next.
"""

        # Add context from previous sections if available
        if previous_sections:
            prompt += "\n\nPREVIOUS ANALYSIS:\n"
            for section in previous_sections[-2:]:  # Include last 2 sections for context
                prompt += f"\n{section.title}:\n"
                prompt += f"{section.content[:500]}...\n"  # Include summary

        # Add the specific task
        prompt += f"\n\nTASK: Provide a {section_type.replace('_', ' ')} for the following legal case:\n\n"

        # Add case details
        prompt += f"Case Name: {scenario.case_name}\n"
        prompt += f"Case Type: {scenario.case_type}\n"
        prompt += f"Key Issues: {', '.join(scenario.key_issues)}\n"
        prompt += f"Urgency: {scenario.urgency_level}\n"
        prompt += f"Analysis Date: {datetime.now().strftime('%B %d, %Y')}\n\n"
        prompt += f"Complaint Summary:\n{scenario.complaint_text[:1500]}\n\n"
        if scenario.additional_context:
            prompt += f"Additional Context:\n{scenario.additional_context}\n\n"

        # Add section-specific instructions
        prompt += self._get_section_instructions(section_type)

        # The executive summary is built from each section's first paragraph
        prompt += """
OUTPUT FORMAT:
Do not write a memo header, title block, or date line. Begin with one paragraph
of 2-3 sentences stating your bottom-line conclusion, then give your analysis.
"""

        return prompt

    def _get_section_instructions(self, section_type: str) -> str:
        """Get specific instructions for each section type."""
        instructions = {
            "liability_assessment": """
Analyze liability by:
- Identifying each potential claim
- Evaluating strength of evidence
- Assessing probability of success (use percentages)
- Citing relevant precedents or legal principles
""",
            "damage_calculation": """
Calculate potential damages by:
- Identifying categories of damages (actual, statutory, punitive)
- Providing specific dollar ranges
- Explaining calculation methodology
- Considering mitigation factors
""",
            "prior_art_analysis": """
Analyze prior art and precedents by:
- Identifying relevant existing patents/IP
- Assessing validity challenges
- Evaluating obviousness arguments
- Determining freedom to operate
""",
            "competitive_landscape": """
Analyze competitive implications by:
- Identifying key competitors affected
- Assessing market position changes
- Evaluating licensing opportunities
- Predicting competitor responses
""",
            "risk_assessment": """
Assess risks by:
- Identifying legal risks (probability and impact)
- Evaluating business risks
- Analyzing reputational risks
- Providing risk mitigation strategies
""",
            "strategic_recommendations": """
Provide strategic recommendations by:
- Outlining 3-5 specific action items
- Prioritizing by impact and urgency
- Estimating resource requirements
- Defining success metrics
"""
        }
        return instructions.get(section_type, "Provide comprehensive analysis for this section.")

    def _get_expected_elements(self, section_type: str) -> List[str]:
        """Get expected elements for quality validation."""
        elements_map = {
            "liability_assessment": ["claims", "evidence", "probability", "precedent"],
            "damage_calculation": ["damages", "calculation", "amount", "methodology"],
            "prior_art_analysis": ["patents", "prior art", "validity", "obviousness"],
            "competitive_landscape": ["competitors", "market", "position", "licensing"],
            "risk_assessment": ["risks", "probability", "impact", "mitigation"],
            "strategic_recommendations": ["recommendations", "action", "timeline", "resources"]
        }
        return elements_map.get(section_type, ["analysis", "assessment", "conclusion"])

    def _get_section_title(self, section_type: str) -> str:
        """Get formatted title for section."""
        titles = {
            "liability_assessment": "Liability Assessment",
            "damage_calculation": "Damage Calculation",
            "prior_art_analysis": "Prior Art Analysis",
            "competitive_landscape": "Competitive Landscape",
            "risk_assessment": "Risk Assessment",
            "strategic_recommendations": "Strategic Recommendations"
        }
        return titles.get(section_type, section_type.replace("_", " ").title())

    def _get_agent_type(self, persona: str) -> str:
        """Determine agent type from persona text."""
        if "Business Analyst" in persona:
            return "business_analyst"
        elif "Market Research" in persona:
            return "market_researcher"
        elif "Strategic" in persona:
            return "strategic_consultant"
        else:
            return "unknown"

    def _generate_executive_summary(self, sections: List[ReportSection], scenario: LegalScenario) -> str:
        """Generate executive summary from all sections."""
        summary = f"EXECUTIVE SUMMARY - {scenario.case_name}\n"
        summary += "=" * 50 + "\n\n"

        # Extract key points from each section
        for section in sections:
            # Get first substantive paragraph
            paragraphs = [p.strip() for p in section.content.split('\n\n') if len(p.strip()) > 50]
            if paragraphs:
                summary += f"{section.title}:\n"
                summary += f"{paragraphs[0][:200]}...\n\n"

        # Add overall assessment
        avg_quality = sum(s.quality_score for s in sections) / len(sections) if sections else 0
        summary += f"Overall Confidence: {avg_quality:.1%}\n"
        summary += f"Key Issues Identified: {len(scenario.key_issues)}\n"
        summary += f"Urgency Level: {scenario.urgency_level}\n"

        return summary

    def _get_pricing(self) -> Tuple[float, float]:
        """Get the (input, output) USD rates per 1M tokens for the current model."""
        return MODEL_PRICING.get(self.model_name, DEFAULT_PRICING)

    def _calculate_cost(self, token_usage: TokenUsage) -> float:
        """Estimate cost in USD from token usage and list prices."""
        input_rate, output_rate = self._get_pricing()
        input_cost = (token_usage.input_tokens / 1_000_000) * input_rate
        output_cost = (token_usage.output_tokens / 1_000_000) * output_rate
        return input_cost + output_cost

    # Metric tracking methods

    def get_token_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics."""
        if not self.token_usage_history:
            return {"error": "No usage data available"}

        total_input = sum(u.input_tokens for u in self.token_usage_history)
        total_output = sum(u.output_tokens for u in self.token_usage_history)
        total_tokens = sum(u.total_tokens for u in self.token_usage_history)

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_tokens,
            "estimated_cost_usd": sum(self._calculate_cost(u) for u in self.token_usage_history),
            "average_per_request": total_tokens / len(self.token_usage_history) if self.token_usage_history else 0,
            "request_count": len(self.token_usage_history)
        }

    def get_avg_processing_time(self) -> float:
        """Get average processing time."""
        if not self.processing_times:
            return 0.0
        return sum(self.processing_times) / len(self.processing_times)

    def get_success_rate(self) -> float:
        """Get success rate of generations."""
        if self.total_attempts == 0:
            return 0.0
        return self.success_count / self.total_attempts