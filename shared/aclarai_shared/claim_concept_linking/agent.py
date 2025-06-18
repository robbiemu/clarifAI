"""
LLM agent for claim-concept relationship classification.

This module implements the ClaimConceptLinkerAgent that uses an LLM to classify
the relationship between claims and concepts, following the prompt structure
defined in docs/arch/on-linking_claims_to_concepts.md.
"""

import json
import logging
from typing import Optional

from llama_index.llms.openai import OpenAI

from ..config import aclaraiConfig, load_config
from .models import (
    ClaimConceptPair,
    AgentClassificationResult,
    RelationshipType,
)

logger = logging.getLogger(__name__)


class ClaimConceptLinkerAgent:
    """
    LLM agent for classifying relationships between claims and concepts.

    This agent analyzes claim-concept pairs and classifies their relationship
    as SUPPORTS_CONCEPT, MENTIONS_CONCEPT, or CONTRADICTS_CONCEPT.
    """

    def __init__(self, config: Optional[aclaraiConfig] = None):
        """
        Initialize the claim-concept linker agent.

        Args:
            config: aclarai configuration (loads default if None)
        """
        self.config = config or load_config()

        # Get LLM configuration
        llm_config = self.config.llm

        # Initialize LLM
        if llm_config.provider == "openai":
            self.llm = OpenAI(
                model=llm_config.model,
                api_key=llm_config.api_key,
                temperature=0.1,  # Low temperature for consistent classification
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_config.provider}")

        # Store model name for metadata
        self.model_name = llm_config.model

        logger.info(
            f"Initialized ClaimConceptLinkerAgent with model: {self.model_name}",
            extra={
                "service": "aclarai",
                "filename.function_name": "claim_concept_linking.ClaimConceptLinkerAgent.__init__",
                "model": self.model_name,
            },
        )

    def classify_relationship(
        self, pair: ClaimConceptPair
    ) -> Optional[AgentClassificationResult]:
        """
        Classify the relationship between a claim and concept.

        Args:
            pair: The claim-concept pair to analyze

        Returns:
            AgentClassificationResult if successful, None if failed
        """
        try:
            # Build the prompt
            prompt = self._build_classification_prompt(pair)

            # Get LLM response
            response = self.llm.complete(prompt)

            # Parse the JSON response
            result = self._parse_agent_response(response.text)

            if result:
                logger.debug(
                    "Successfully classified claim-concept relationship",
                    extra={
                        "service": "aclarai",
                        "filename.function_name": "claim_concept_linking.ClaimConceptLinkerAgent.classify_relationship",
                        "claim_id": pair.claim_id,
                        "concept_id": pair.concept_id,
                        "relation": result.relation,
                        "strength": result.strength,
                    },
                )

            return result

        except Exception as e:
            logger.error(
                f"Failed to classify claim-concept relationship: {e}",
                extra={
                    "service": "aclarai",
                    "filename.function_name": "claim_concept_linking.ClaimConceptLinkerAgent.classify_relationship",
                    "claim_id": pair.claim_id,
                    "concept_id": pair.concept_id,
                    "error": str(e),
                },
            )
            return None

    def _build_classification_prompt(self, pair: ClaimConceptPair) -> str:
        """
        Build the classification prompt from the claim-concept pair.

        Args:
            pair: The claim-concept pair

        Returns:
            The formatted prompt string
        """
        # Base prompt structure from the architecture document
        prompt_lines = [
            "You are a semantic classifier tasked with identifying the relationship between a claim and a concept.",
            "",
            "Claim:",
            f'"{pair.claim_text}"',
            "",
            "Concept:",
            f'"{pair.concept_text}"',
        ]

        # Add context if available
        if pair.source_sentence or pair.summary_block:
            prompt_lines.extend(["", "Context (optional):"])

            if pair.source_sentence:
                prompt_lines.append(f'- Source sentence: "{pair.source_sentence}"')

            if pair.summary_block:
                prompt_lines.append(f'- Summary block: "{pair.summary_block}"')

        # Add instructions
        prompt_lines.extend(
            [
                "",
                "Instructions:",
                "1. Classify the relationship:",
                "   - SUPPORTS_CONCEPT: The claim directly supports or affirms the concept.",
                "   - MENTIONS_CONCEPT: The claim is related to the concept but does not affirm or refute it.",
                "   - CONTRADICTS_CONCEPT: The claim contradicts the concept.",
                "",
                "2. Rate the strength of the relationship (0.0 to 1.0), where 1.0 is strong and direct.",
                "3. Estimate whether the claim is entailed by its context (entailed_score).",
                "4. Estimate how completely the claim covers the verifiable content of its context (coverage_score).",
                "",
                "Output as JSON:",
                "{",
                '  "relation": "SUPPORTS_CONCEPT",',
                '  "strength": 0.92,',
                '  "entailed_score": 0.98,',
                '  "coverage_score": 0.87',
                "}",
            ]
        )

        return "\n".join(prompt_lines)

    def _parse_agent_response(
        self, response_text: str
    ) -> Optional[AgentClassificationResult]:
        """
        Parse the agent's JSON response into a result object.

        Args:
            response_text: Raw response text from the LLM

        Returns:
            AgentClassificationResult if parsing successful, None otherwise
        """
        try:
            # Extract JSON from response (handle cases where LLM includes extra text)
            response_text = response_text.strip()

            # Find JSON content
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                logger.error(
                    "No JSON found in agent response",
                    extra={
                        "service": "aclarai",
                        "filename.function_name": "claim_concept_linking.ClaimConceptLinkerAgent._parse_agent_response",
                        "response": response_text[
                            :200
                        ],  # First 200 chars for debugging
                    },
                )
                return None

            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)

            # Validate required fields
            if "relation" not in data or "strength" not in data:
                logger.error(
                    "Missing required fields in agent response",
                    extra={
                        "service": "aclarai",
                        "filename.function_name": "claim_concept_linking.ClaimConceptLinkerAgent._parse_agent_response",
                        "data": data,
                    },
                )
                return None

            # Validate relation type
            relation = data["relation"]
            if relation not in [rt.value for rt in RelationshipType]:
                logger.error(
                    f"Invalid relation type: {relation}",
                    extra={
                        "service": "aclarai",
                        "filename.function_name": "claim_concept_linking.ClaimConceptLinkerAgent._parse_agent_response",
                        "relation": relation,
                    },
                )
                return None

            # Validate strength
            strength = float(data["strength"])
            if not (0.0 <= strength <= 1.0):
                logger.warning(
                    f"Strength out of range [0.0, 1.0]: {strength}, clamping",
                    extra={
                        "service": "aclarai",
                        "filename.function_name": "claim_concept_linking.ClaimConceptLinkerAgent._parse_agent_response",
                        "strength": strength,
                    },
                )
                strength = max(0.0, min(1.0, strength))

            # Extract optional scores
            entailed_score = data.get("entailed_score")
            coverage_score = data.get("coverage_score")

            # Validate scores if present
            if entailed_score is not None:
                entailed_score = float(entailed_score)
                if not (0.0 <= entailed_score <= 1.0):
                    logger.warning(f"entailed_score out of range: {entailed_score}")
                    entailed_score = max(0.0, min(1.0, entailed_score))

            if coverage_score is not None:
                coverage_score = float(coverage_score)
                if not (0.0 <= coverage_score <= 1.0):
                    logger.warning(f"coverage_score out of range: {coverage_score}")
                    coverage_score = max(0.0, min(1.0, coverage_score))

            return AgentClassificationResult(
                relation=relation,
                strength=strength,
                entailed_score=entailed_score,
                coverage_score=coverage_score,
            )

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse JSON response: {e}",
                extra={
                    "service": "aclarai",
                    "filename.function_name": "claim_concept_linking.ClaimConceptLinkerAgent._parse_agent_response",
                    "response": response_text[:200],  # First 200 chars for debugging
                    "error": str(e),
                },
            )
            return None

        except (ValueError, TypeError) as e:
            logger.error(
                f"Failed to validate response data: {e}",
                extra={
                    "service": "aclarai",
                    "filename.function_name": "claim_concept_linking.ClaimConceptLinkerAgent._parse_agent_response",
                    "error": str(e),
                },
            )
            return None
