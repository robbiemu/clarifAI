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
            # LLM is required for selection processing
            if self.llm is None:
                raise ValueError("LLM is required for Selection agent processing")
                
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
            # LLM is required for disambiguation processing
            if self.llm is None:
                raise ValueError("LLM is required for Disambiguation agent processing")
                
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

    def _llm_disambiguation(
        self, sentence: SentenceChunk, context: ClaimifyContext
    ) -> DisambiguationResult:
        """LLM-based disambiguation for more sophisticated rewriting."""
        # TODO: Implement LLM-based disambiguation using prompt
        # For now, return original text as placeholder
        return DisambiguationResult(
            original_sentence=sentence,
            disambiguated_text=sentence.text,
            changes_made=[],
            confidence=1.0,
        )


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
            # LLM is required for decomposition processing
            if self.llm is None:
                raise ValueError("LLM is required for Decomposition agent processing")
                
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

    def _llm_decomposition(self, text: str) -> DecompositionResult:
        """LLM-based decomposition for more sophisticated analysis."""
        # TODO: Implement LLM-based decomposition using prompt
        # For now, return simple single-claim candidate as placeholder
        candidate = ClaimCandidate(
            text=text,
            is_atomic=True,
            is_self_contained=True,
            is_verifiable=True,
            confidence=0.8,
            reasoning="Placeholder LLM decomposition - single claim"
        )
        
        return DecompositionResult(
            original_text=text,
            claim_candidates=[candidate]
        )

