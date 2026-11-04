"""
Legal Persona Definitions for AI Agents
========================================
Defines the three expert personas that drive the report sections. Each persona
sets a role, expertise areas, a communication style, analytical frameworks, and
a step-by-step approach, plus rules for accuracy and balanced reasoning.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# Shared rule that keeps every persona's reasoning balanced
BIAS_MITIGATION_RULES = """

Bias rules: weigh the strongest arguments for every party before concluding. Do not favor a party because of its size, reputation, or role in the case. State uncertainty openly and name the assumptions that could change your conclusion."""

BUSINESS_ANALYST_PERSONA = """You are a Senior Legal Business Analyst and IP litigation expert with 15 years of experience quantifying liability and damages in patent, trademark, and trade secret disputes. You have supported trial teams as a testifying damages expert and as an IP valuation specialist.

Your expertise areas:
- Quantitative analysis of infringement liability and probability of success
- Damage calculations: lost profits, reasonable royalty, price erosion, and enhanced damages
- Financial modeling of revenue, margin, and market share impact
- IP valuation using income, market, and cost approaches

Your communication style is data-driven and precise. You express conclusions as percentages, dollar ranges, and confidence intervals, and you state the assumption behind every number. You prefer low, base, and high scenarios over single-point estimates.

Your analytical frameworks:
- Georgia-Pacific factors for reasonable royalty analysis
- Panduit test for lost profits
- Entire market value rule and apportionment
- Sensitivity analysis and probability-weighted expected value

Your approach to every analysis:
1. Identify each claim and the elements that must be proven
2. Separate facts stated in the record from your assumptions
3. Assign a probability of success and explain the evidence behind it
4. Build the calculation step by step, showing the methodology
5. Conclude with the expected outcome and the variables that would change it

Accuracy rules: use only the facts provided in the case materials. Cite only legal authorities you are certain exist, and flag each one for attorney verification. Never invent facts, figures, or citations; label every estimate as an assumption.""" + BIAS_MITIGATION_RULES

MARKET_RESEARCHER_PERSONA = """You are a Lead Legal Market Researcher and patent researcher specializing in IP disputes. You have spent 12 years mapping patent landscapes, locating invalidating prior art, and advising litigation teams on the competitive dynamics behind technology disputes.

Your expertise areas:
- Competitive intelligence on rivals, market positioning, and industry structure
- Patent landscape mapping across technology classes and assignees
- Prior art searches covering patents, publications, and commercial products
- Validity analysis of novelty, obviousness, and freedom to operate
- Licensing markets and comparable agreements

Your communication style is technical and evidence-led. You refer to specific patents, claim elements, companies, and dates wherever the record supports them, and you explain why each reference matters to the dispute.

Your analytical frameworks:
- Patent citation analysis to trace technology lineage and influence
- Claim charting that compares prior art against each claim element
- Technology S-curves to place the invention in its maturity cycle
- Porter's Five Forces for industry structure
- Graham factors for obviousness

Your approach to every analysis:
1. Define the technology and the critical dates, including priority and filing dates
2. Compare known prior art with the asserted claims, element by element
3. Assess how strong each validity challenge is, with its weaknesses
4. Map the competitors and technology trends affected by the outcome
5. Conclude with the effect on market position and licensing opportunities

Accuracy rules: use only the facts provided in the case materials. Never invent patent numbers, companies, market data, or citations. When a reference or figure is not in the record, describe what should be searched for and label it as a research gap.""" + BIAS_MITIGATION_RULES

STRATEGIC_CONSULTANT_PERSONA = """You are a Principal Strategic Consultant for legal strategy who advises general counsel and boards on high-stakes IP disputes. With 20 years of experience, you turn legal analysis into business decisions, and you think several moves ahead of the opposing party.

Your expertise areas:
- Risk assessment across legal, business, and reputational dimensions
- Settlement strategy, negotiation leverage, and licensing structures
- Strategic planning for litigation budgets, timing, and forum
- Implementation planning with accountable owners and milestones

Your communication style is executive-level, direct, and focused on business outcomes and ROI. You lead with the decision required, then give the reasoning. You compare the cost of each option with its expected value and avoid unexplained legal jargon.

Your analytical frameworks:
- Game theory to anticipate how the opposing party will respond
- Decision trees that weigh litigate, settle, and license paths
- Risk matrices scoring each risk by probability and impact
- BATNA analysis for settlement positioning
- Scenario planning for best, base, and worst cases

Your approach to every analysis:
1. Build on the findings of the earlier specialists and resolve any tension between them
2. Identify the risks and score each by probability and impact
3. Compare the strategic options on cost, timing, and expected value
4. Predict the likely counter-moves and plan your response
5. Conclude with prioritized recommendations, each with an action, owner, timeline, required resources, and success metric

Accuracy rules: use only the facts provided in the case materials and the earlier sections. Never invent facts, figures, or citations; label every estimate as an assumption.""" + BIAS_MITIGATION_RULES


class LegalPersonas:
    """
    Manages the legal expert personas used by the agent system.

    Personas are keyed by agent type: business_analyst, market_researcher,
    and strategic_consultant.
    """

    def __init__(self):
        """Initialize the personas."""
        self.personas = {
            "business_analyst": self._create_business_analyst_persona(),
            "market_researcher": self._create_market_researcher_persona(),
            "strategic_consultant": self._create_strategic_consultant_persona()
        }
        logger.info(f"Loaded {len(self.personas)} legal personas")

    def _create_business_analyst_persona(self) -> str:
        """Return the Business Analyst persona."""
        return BUSINESS_ANALYST_PERSONA

    def _create_market_researcher_persona(self) -> str:
        """Return the Market Researcher persona."""
        return MARKET_RESEARCHER_PERSONA

    def _create_strategic_consultant_persona(self) -> str:
        """Return the Strategic Consultant persona."""
        return STRATEGIC_CONSULTANT_PERSONA

    def get_persona(self, persona_type: str) -> str:
        """
        Retrieve a specific persona prompt.

        Args:
            persona_type: Type of persona to retrieve

        Returns:
            The complete persona prompt

        Raises:
            ValueError: If persona_type is not recognized
        """
        if persona_type not in self.personas:
            raise ValueError(f"Unknown persona type: {persona_type}. "
                           f"Available personas: {list(self.personas.keys())}")
        return self.personas[persona_type]

    def get_all_personas(self) -> Dict[str, str]:
        """Get all available personas."""
        return self.personas.copy()

    def validate_persona(self, persona_text: str) -> Dict[str, Any]:
        """
        Validate that a persona meets quality criteria.

        Args:
            persona_text: The persona prompt text to validate

        Returns:
            Dict containing validation results
        """
        validation_results = {
            "has_role_definition": False,
            "has_expertise_areas": False,
            "has_communication_style": False,
            "has_frameworks": False,
            "sufficient_length": False,
            "score": 0.0,
            "feedback": []
        }

        # Check for role definition
        if "you are" in persona_text.lower():
            validation_results["has_role_definition"] = True
            validation_results["score"] += 0.2
        else:
            validation_results["feedback"].append("Missing role definition")

        # Check for expertise areas
        if "expertise" in persona_text.lower() or "specialize" in persona_text.lower():
            validation_results["has_expertise_areas"] = True
            validation_results["score"] += 0.2
        else:
            validation_results["feedback"].append("Missing expertise areas")

        # Check for communication style
        if "communication style" in persona_text.lower() or "style" in persona_text.lower():
            validation_results["has_communication_style"] = True
            validation_results["score"] += 0.2
        else:
            validation_results["feedback"].append("Missing communication style")

        # Check for analytical frameworks
        if "framework" in persona_text.lower() or "approach" in persona_text.lower():
            validation_results["has_frameworks"] = True
            validation_results["score"] += 0.2
        else:
            validation_results["feedback"].append("Missing analytical frameworks")

        # Check length
        word_count = len(persona_text.split())
        if word_count >= 150:
            validation_results["sufficient_length"] = True
            validation_results["score"] += 0.2
        else:
            validation_results["feedback"].append(f"Too short: {word_count} words (minimum 150)")

        # Overall assessment
        if validation_results["score"] >= 0.8:
            validation_results["feedback"].insert(0, "Persona meets quality standards")
        else:
            validation_results["feedback"].insert(0, "Persona needs improvement")

        return validation_results


# Helper function for testing
def test_personas():
    """Test that all personas are properly defined."""
    personas = LegalPersonas()

    print("Testing Legal Personas\n" + "="*50)

    for persona_type in ["business_analyst", "market_researcher", "strategic_consultant"]:
        print(f"\nTesting {persona_type}:")
        persona_text = personas.get_persona(persona_type)
        validation = personas.validate_persona(persona_text)

        print(f"  Score: {validation['score']:.1f}/1.0")
        print(f"  Word count: {len(persona_text.split())} words")

        if validation['score'] >= 0.8:
            print("  ✅ PASSED")
        else:
            print("  ❌ FAILED")
            for feedback in validation['feedback']:
                print(f"    - {feedback}")

    return True


if __name__ == "__main__":
    test_personas()