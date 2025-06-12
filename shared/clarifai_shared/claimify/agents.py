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
        """
        LLM-based selection following the Claimify approach.
        
        This implements Stage 1: Selection from the Claimify pipeline, which:
        1. Identifies if the sentence contains verifiable factual information
        2. Removes subjective or speculative language if verifiable content exists
        3. Returns either the cleaned sentence or "NO_VERIFIABLE_CONTENT"
        """
        sentence = context.current_sentence
        context_text = self._build_context_text(context)
        
        # Prompt based on Claimify for Dummies Stage 1: Selection
        prompt = f"""You are a fact-checking assistant. Your job is to identify if the following sentence contains a specific, verifiable proposition. A verifiable proposition is a statement of fact, not an opinion, a recommendation, or a vague statement.

**Source Sentence:** "{sentence.text}"

**Context (surrounding sentences):**
{context_text}

**Task:**
1. **Analyze:** Does the sentence contain a verifiable fact?
2. **Decide:**
   - If NO, respond with "NO_VERIFIABLE_CONTENT".
   - If YES, rewrite the sentence to *only* include the verifiable parts. Remove any subjective or speculative language.

**Your rewritten sentence or "NO_VERIFIABLE_CONTENT":**"""

        try:
            # Call the LLM with the prompt
            response = self.llm.complete(
                prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens or 500
            ).strip()
            
            # Parse the response
            if response == "NO_VERIFIABLE_CONTENT":
                return SelectionResult(
                    sentence_chunk=sentence,
                    is_selected=False,
                    reasoning="No verifiable content found",
                    rewritten_text=None
                )
            else:
                # The response is a rewritten sentence with only verifiable content
                return SelectionResult(
                    sentence_chunk=sentence,
                    is_selected=True,
                    reasoning="Contains verifiable content",
                    rewritten_text=response
                )
                
        except Exception as e:
            # If LLM fails, we cannot perform selection without heuristics
            raise ValueError(f"LLM selection failed and no fallback available: {e}")

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
        """
        LLM-based disambiguation following the Claimify approach.
        
        This implements Stage 2: Disambiguation from the Claimify pipeline, which:
        1. Identifies ambiguities (pronouns, time references, structural ambiguities)
        2. Uses context to resolve ambiguities confidently
        3. Returns either the clarified sentence or "CANNOT_DISAMBIGUATE"
        """
        context_text = self._build_context_text(context)
        
        # Prompt based on Claimify for Dummies Stage 2: Disambiguation
        prompt = f"""You are a fact-checking assistant. Your goal is to resolve ambiguity.

**Context (surrounding text):** 
{context_text}

**Sentence to Analyze:** "{sentence.text}"

**Task:**
1. **Identify Ambiguity:** Does the sentence contain any pronouns (he, it, they), ambiguous time references (last year), or structural ambiguities (where grammar allows multiple readings)?
2. **Resolve with Context:** Can the context clearly and confidently resolve all ambiguities?
3. **Decide:**
   - If the ambiguity CANNOT be confidently resolved, respond with "CANNOT_DISAMBIGUATE".
   - If it CAN be resolved (or if there was no ambiguity), return the fully clarified and rewritten sentence.

**Your rewritten sentence or "CANNOT_DISAMBIGUATE":**"""

        try:
            # Call the LLM with the prompt
            response = self.llm.complete(
                prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens or 500
            ).strip()
            
            # Parse the response
            if response == "CANNOT_DISAMBIGUATE":
                return DisambiguationResult(
                    original_sentence=sentence,
                    disambiguated_text=sentence.text,  # Keep original
                    changes_made=["Could not resolve ambiguities"],
                    confidence=0.0
                )
            else:
                # The response is a disambiguated sentence
                changes_made = []
                if response != sentence.text:
                    changes_made.append("Resolved pronouns and ambiguous references")
                    
                return DisambiguationResult(
                    original_sentence=sentence,
                    disambiguated_text=response,
                    changes_made=changes_made,
                    confidence=0.8
                )
                
        except Exception as e:
            # If LLM fails, we cannot perform disambiguation without heuristics
            raise ValueError(f"LLM disambiguation failed and no fallback available: {e}")
            
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
        """
        LLM-based decomposition following the Claimify approach.
        
        This implements Stage 3: Decomposition from the Claimify pipeline, which:
        1. Breaks the sentence into atomic, self-contained claims
        2. Adds clarifying information in [square brackets] if needed
        3. Ensures each claim meets quality criteria (atomic, self-contained, verifiable)
        """
        
        # Prompt based on Claimify for Dummies Stage 3: Decomposition
        prompt = f"""You are an expert fact-checker. Your task is to decompose the given sentence into a list of simple, atomic, and fully decontextualized factual claims.

**Rules:**
1. Each claim must be a complete, self-contained sentence.
2. Break the sentence into the smallest possible pieces of verifiable information.
3. If a claim needs context to be understood, add the clarifying information inside [square brackets].
4. Only include factual, verifiable statements - no opinions or speculative content.
5. Each claim should be atomic (single fact), self-contained (no ambiguous references), and verifiable (can be fact-checked).

**Sentence to Decompose:** "{text}"

**List of Decomposed Claims (one per line, or write "NO_VALID_CLAIMS" if no verifiable claims can be extracted):**"""

        try:
            # Call the LLM with the prompt
            response = self.llm.complete(
                prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens or 1000
            ).strip()
            
            # Parse the response
            if response == "NO_VALID_CLAIMS":
                return DecompositionResult(
                    original_text=text,
                    claim_candidates=[]
                )
            
            # Split response into individual claims
            claim_lines = [line.strip() for line in response.split('\n') if line.strip()]
            claim_candidates = []
            
            for claim_text in claim_lines:
                # Remove bullet points or numbering if present
                claim_text = claim_text.lstrip('- •*123456789.)')
                claim_text = claim_text.strip()
                
                if claim_text and claim_text != "NO_VALID_CLAIMS":
                    # Evaluate the claim quality (simplified for now)
                    candidate = ClaimCandidate(
                        text=claim_text,
                        is_atomic=True,  # Assume LLM followed instructions
                        is_self_contained=True,  # Assume LLM followed instructions  
                        is_verifiable=True,  # Assume LLM followed instructions
                        confidence=0.8,
                        reasoning="Extracted by LLM decomposition"
                    )
                    claim_candidates.append(candidate)
            
            return DecompositionResult(
                original_text=text,
                claim_candidates=claim_candidates
            )
                
        except Exception as e:
            # If LLM fails, we cannot perform decomposition without heuristics
            raise ValueError(f"LLM decomposition failed and no fallback available: {e}")
