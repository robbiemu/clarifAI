"""
Base agent classes and implementations for the Claimify pipeline.

This module contains the three core agents:
- SelectionAgent: Identifies relevant sentence chunks
- DisambiguationAgent: Rewrites sentences to remove ambiguities
- DecompositionAgent: Breaks sentences into atomic claims

Each agent is designed to accept different LLM instances for future configurability.
"""

import logging
import time
from abc import ABC
from typing import Optional, Protocol

from .data_models import (
    SentenceChunk,
    ClaimifyContext,
    SelectionResult,
    DisambiguationResult,
    DecompositionResult,
    ClaimCandidate,
    ClaimifyConfig,
)

logger = logging.getLogger(__name__)


class LLMInterface(Protocol):
    """Protocol defining the interface for LLM interactions."""

    def complete(self, prompt: str, **kwargs) -> str:
        """Generate a completion for the given prompt."""
        ...


class BaseClaimifyAgent(ABC):
    """Base class for all Claimify pipeline agents."""

    def __init__(
        self,
        llm: Optional[LLMInterface] = None,
        config: Optional[ClaimifyConfig] = None,
    ):
        self.llm = llm
        self.config = config or ClaimifyConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _log_decision(self, stage: str, decision: str, reasoning: str = "") -> None:
        """Log agent decisions if configured."""
        if self.config.log_decisions:
            self.logger.info(
                f"[agents.{self.__class__.__name__}._log_decision] Claimify.{stage} decision: {decision}",
                extra={
                    "service": "clarifai-core",
                    "stage": stage,
                    "decision": decision,
                    "reasoning": reasoning,
                },
            )

    def _log_transformation(
        self, stage: str, original: str, transformed: str, changes: list
    ) -> None:
        """Log transformations if configured."""
        if self.config.log_transformations:
            self.logger.info(
                f"[agents.{self.__class__.__name__}._log_transformation] Claimify.{stage} transformation: {len(changes)} changes made",
                extra={
                    "service": "clarifai-core",
                    "stage": stage,
                    "original_length": len(original),
                    "transformed_length": len(transformed),
                    "changes": changes,
                },
            )

    def _log_timing(self, stage: str, processing_time: float) -> None:
        """Log processing time if configured."""
        if self.config.log_timing:
            self.logger.debug(
                f"[agents.{self.__class__.__name__}._log_timing] Claimify.{stage} processing time: {processing_time:.3f}s",
                extra={
                    "service": "clarifai-core",
                    "stage": stage,
                    "processing_time": processing_time,
                },
            )


class SelectionAgent(BaseClaimifyAgent):
    """
    Agent responsible for identifying sentence chunks that contain verifiable information
    relevant for claim extraction.

    This is the first stage of the Claimify pipeline.
    """

    def process(self, context: ClaimifyContext) -> SelectionResult:
        """
        Process a sentence chunk to determine if it should be selected for further processing.

        Args:
            context: ClaimifyContext containing the sentence and surrounding context

        Returns:
            SelectionResult with decision and reasoning
        """
        start_time = time.time()
        sentence = context.current_sentence

        try:
            # If no LLM is provided, use simple heuristics
            if self.llm is None:
                result = self._heuristic_selection(context)
            else:
                result = self._llm_selection(context)

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            self._log_decision(
                "selection",
                "selected" if result.is_selected else "rejected",
                result.reasoning or "",
            )
            self._log_timing("selection", processing_time)

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(
                f"[agents.{self.__class__.__name__}.process] Error in selection processing: {e}",
                extra={
                    "service": "clarifai-core",
                    "stage": "selection",
                    "error": str(e),
                },
            )
            return SelectionResult(
                sentence_chunk=sentence,
                is_selected=False,
                reasoning=f"Error during processing: {e}",
                processing_time=processing_time,
            )

    def _heuristic_selection(self, context: ClaimifyContext) -> SelectionResult:
        """Simple heuristic-based selection when no LLM is available."""
        sentence = context.current_sentence
        text = sentence.text.strip()

        # Basic heuristics for selecting potentially verifiable content
        verifiable_indicators = [
            # Technical/error content
            "error",
            "exception",
            "bug",
            "issue",
            "problem",
            "erro",
            # Portuguese error indicators
            "argumento",
            "tipo",
            "não pode",
            "atribuído",
            "função",
            # Factual statements
            "is",
            "are",
            "was",
            "were",
            "has",
            "have",
            "had",
            # Actions and outcomes
            "caused",
            "resulted",
            "occurred",
            "happened",
            "found",
            "reported",
            # Measurements and quantities
            "percent",
            "%",
            "number",
            "count",
            "amount",
            "size",
            # Comparisons
            "better",
            "worse",
            "more",
            "less",
            "faster",
            "slower",
            # Technical content
            "slice",
            "none",
            "int",
            "__setitem__",
            "pylance",
        ]

        # Skip very short or empty sentences
        if len(text) < 10:
            return SelectionResult(
                sentence_chunk=sentence,
                is_selected=False,
                confidence=0.9,
                reasoning="Sentence too short to contain verifiable information",
            )

        # Skip questions (usually not verifiable claims)
        if text.endswith("?"):
            return SelectionResult(
                sentence_chunk=sentence,
                is_selected=False,
                confidence=0.8,
                reasoning="Questions are not verifiable claims",
            )

        # Check for verifiable indicators
        text_lower = text.lower()
        indicator_count = sum(
            1 for indicator in verifiable_indicators if indicator in text_lower
        )

        # Select if we find verifiable content indicators
        is_selected = indicator_count > 0
        confidence = min(0.6 + (indicator_count * 0.1), 0.9)

        reasoning = (
            f"Found {indicator_count} verifiable indicators"
            if is_selected
            else "No verifiable indicators found"
        )

        return SelectionResult(
            sentence_chunk=sentence,
            is_selected=is_selected,
            confidence=confidence,
            reasoning=reasoning,
        )

    def _llm_selection(self, context: ClaimifyContext) -> SelectionResult:
        """LLM-based selection for more sophisticated analysis."""
        # For now, implement a placeholder that would use the LLM
        # This will be expanded when LLM integration is available

        # TODO: Implement LLM-based selection using prompt
        # sentence = context.current_sentence
        # context_text = self._build_context_text(context)
        # prompt = f"""Analyze the following sentence to determine if it contains verifiable, factual information that could be extracted as a claim.
        #
        # Context (surrounding sentences):
        # {context_text}
        #
        # Target sentence: "{sentence.text}"
        #
        # Consider:
        # 1. Does this sentence contain factual, verifiable information?
        # 2. Is it a statement (not a question or command)?
        # 3. Could this information be fact-checked or validated?
        # 4. Does it describe events, relationships, or measurable properties?
        #
        # Respond with JSON: {{"selected": true/false, "confidence": 0.0-1.0, "reasoning": "explanation"}}"""

        try:
            # This would call the LLM when available
            # For now, fall back to heuristics
            return self._heuristic_selection(context)
        except Exception as e:
            self.logger.warning(
                f"[agents.{self.__class__.__name__}._llm_selection] LLM selection failed, falling back to heuristics: {e}"
            )
            return self._heuristic_selection(context)

    def _build_context_text(self, context: ClaimifyContext) -> str:
        """Build context text from surrounding sentences."""
        parts = []

        # Add preceding sentences
        for i, sent in enumerate(context.preceding_sentences):
            parts.append(f"[{-len(context.preceding_sentences) + i}] {sent.text}")

        # Add current sentence marker
        parts.append(f"[0] {context.current_sentence.text} ← TARGET")

        # Add following sentences
        for i, sent in enumerate(context.following_sentences):
            parts.append(f"[{i + 1}] {sent.text}")

        return "\n".join(parts)


class DisambiguationAgent(BaseClaimifyAgent):
    """
    Agent responsible for rewriting sentences to remove ambiguities and add context.

    This is the second stage of the Claimify pipeline.
    """

    def process(
        self, sentence: SentenceChunk, context: ClaimifyContext
    ) -> DisambiguationResult:
        """
        Process a selected sentence to remove ambiguities and add inferred subjects.

        Args:
            sentence: The sentence chunk to disambiguate
            context: Surrounding context for disambiguation

        Returns:
            DisambiguationResult with rewritten text and changes
        """
        start_time = time.time()

        try:
            if self.llm is None:
                result = self._heuristic_disambiguation(sentence, context)
            else:
                result = self._llm_disambiguation(sentence, context)

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            self._log_transformation(
                "disambiguation",
                sentence.text,
                result.disambiguated_text,
                result.changes_made,
            )
            self._log_timing("disambiguation", processing_time)

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(
                f"[agents.{self.__class__.__name__}.process] Error in disambiguation processing: {e}",
                extra={
                    "service": "clarifai-core",
                    "stage": "disambiguation",
                    "error": str(e),
                },
            )
            return DisambiguationResult(
                original_sentence=sentence,
                disambiguated_text=sentence.text,  # Return original on error
                changes_made=[f"Error during processing: {e}"],
                processing_time=processing_time,
            )

    def _heuristic_disambiguation(
        self, sentence: SentenceChunk, context: ClaimifyContext
    ) -> DisambiguationResult:
        """Simple heuristic-based disambiguation."""
        original_text = sentence.text
        disambiguated = original_text
        changes = []

        # Simple pronoun resolution heuristics
        pronouns_to_replace = {
            " it ": " the system ",
            " It ": " The system ",
            "It ": "The system ",  # Handle sentence start
            " this ": " this issue ",
            " This ": " This issue ",
            " that ": " that problem ",
            " That ": " That problem ",
        }

        for pronoun, replacement in pronouns_to_replace.items():
            if pronoun in disambiguated:
                disambiguated = disambiguated.replace(pronoun, replacement)
                changes.append(
                    f"Replaced '{pronoun.strip()}' with '{replacement.strip()}'"
                )

        # Add subject inference for sentences starting with verbs
        verb_starters = [
            "reported",
            "shows",
            "indicates",
            "caused",
            "resulted",
            "occurred",
        ]
        text_lower = disambiguated.lower()

        for verb in verb_starters:
            if text_lower.startswith(verb):
                disambiguated = f"[The system] {disambiguated}"
                changes.append(
                    "Added inferred subject '[The system]' to verb-starting sentence"
                )
                break

        return DisambiguationResult(
            original_sentence=sentence,
            disambiguated_text=disambiguated,
            changes_made=changes,
            confidence=0.7 if changes else 1.0,
        )

    def _llm_disambiguation(
        self, sentence: SentenceChunk, context: ClaimifyContext
    ) -> DisambiguationResult:
        """LLM-based disambiguation for more sophisticated rewriting."""
        # Placeholder for LLM implementation
        # Fall back to heuristics for now
        return self._heuristic_disambiguation(sentence, context)


class DecompositionAgent(BaseClaimifyAgent):
    """
    Agent responsible for breaking disambiguated sentences into atomic, self-contained claims.

    This is the third and final stage of the Claimify pipeline.
    """

    def process(
        self, disambiguated_text: str, original_sentence: SentenceChunk
    ) -> DecompositionResult:
        """
        Process a disambiguated sentence to extract atomic claims.

        Args:
            disambiguated_text: The disambiguated sentence text
            original_sentence: The original sentence chunk for reference

        Returns:
            DecompositionResult with claim candidates
        """
        start_time = time.time()

        try:
            if self.llm is None:
                result = self._heuristic_decomposition(disambiguated_text)
            else:
                result = self._llm_decomposition(disambiguated_text)

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            # Log results
            valid_claims = result.valid_claims
            sentence_nodes = result.sentence_nodes

            self.logger.info(
                f"[agents.{self.__class__.__name__}.process] Claimify.decomposition completed: {len(valid_claims)} claims, {len(sentence_nodes)} sentences",
                extra={
                    "service": "clarifai-core",
                    "stage": "decomposition",
                    "claims_count": len(valid_claims),
                    "sentences_count": len(sentence_nodes),
                    "total_candidates": len(result.claim_candidates),
                },
            )
            self._log_timing("decomposition", processing_time)

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(
                f"[agents.{self.__class__.__name__}.process] Error in decomposition processing: {e}",
                extra={
                    "service": "clarifai-core",
                    "stage": "decomposition",
                    "error": str(e),
                },
            )
            return DecompositionResult(
                original_text=disambiguated_text,
                claim_candidates=[],
                processing_time=processing_time,
            )

    def _heuristic_decomposition(self, text: str) -> DecompositionResult:
        """Simple heuristic-based decomposition."""
        candidates = []

        # For simple cases, treat the whole sentence as one candidate
        # and apply basic criteria checks
        candidate = ClaimCandidate(
            text=text.strip(),
            is_atomic=self._check_atomicity(text),
            is_self_contained=self._check_self_containment(text),
            is_verifiable=self._check_verifiability(text),
            confidence=0.7,
        )

        # Add reasoning based on the checks
        issues = []
        if not candidate.is_atomic:
            issues.append("contains compound statements")
        if not candidate.is_self_contained:
            issues.append("contains ambiguous references")
        if not candidate.is_verifiable:
            issues.append("not verifiable")

        candidate.reasoning = (
            "Passes all criteria"
            if candidate.passes_criteria
            else f"Issues: {', '.join(issues)}"
        )
        candidates.append(candidate)

        # Try to split compound sentences
        if " and " in text or " but " in text or " or " in text:
            # Simple splitting on conjunctions
            parts = []
            for separator in [" and ", " but ", " or "]:
                if separator in text:
                    parts = [
                        part.strip() for part in text.split(separator) if part.strip()
                    ]
                    break

            if len(parts) > 1:
                candidates = []  # Replace single candidate with split ones
                for part in parts:
                    candidate = ClaimCandidate(
                        text=part,
                        is_atomic=True,  # Split parts are more likely atomic
                        is_self_contained=self._check_self_containment(part),
                        is_verifiable=self._check_verifiability(part),
                        confidence=0.8,
                    )
                    candidate.reasoning = "Split from compound sentence"
                    candidates.append(candidate)

        return DecompositionResult(original_text=text, claim_candidates=candidates)

    def _check_atomicity(self, text: str) -> bool:
        """Check if the text represents an atomic claim."""
        # Simple heuristics for atomicity
        conjunctions = [" and ", " but ", " or ", " while ", " because ", " since "]
        return not any(conj in text.lower() for conj in conjunctions)

    def _check_self_containment(self, text: str) -> bool:
        """Check if the text is self-contained (no ambiguous references)."""
        # Check for ambiguous pronouns and references
        ambiguous_refs = [
            " it ",
            " this ",
            " that ",
            " they ",
            " these ",
            " those ",
            " the error",
            " the issue",
        ]
        text_lower = text.lower()

        # Also check for sentence-starting ambiguous pronouns
        if (
            text_lower.startswith("it ")
            or text_lower.startswith("this ")
            or text_lower.startswith("that ")
        ):
            return False

        # Allow some specific, clear references
        clear_refs = ["the system", "the user", "the application", "the code"]

        for ref in ambiguous_refs:
            if ref in text_lower:
                # Check if it's clarified by context
                if not any(clear_ref in text_lower for clear_ref in clear_refs):
                    return False

        return True

    def _check_verifiability(self, text: str) -> bool:
        """Check if the text contains verifiable information."""
        # Check for factual, verifiable content
        verifiable_patterns = [
            # Technical facts
            "error",
            "exception",
            "bug",
            "issue",
            # States and properties
            "is",
            "are",
            "was",
            "were",
            "has",
            "have",
            "had",
            # Events and actions
            "occurred",
            "happened",
            "caused",
            "resulted",
            "reported",
            # Measurements
            "percent",
            "%",
            "number",
            "size",
            "count",
        ]

        text_lower = text.lower()
        return any(pattern in text_lower for pattern in verifiable_patterns)

    def _llm_decomposition(self, text: str) -> DecompositionResult:
        """LLM-based decomposition for more sophisticated analysis."""
        # Placeholder for LLM implementation
        # Fall back to heuristics for now
        return self._heuristic_decomposition(text)
