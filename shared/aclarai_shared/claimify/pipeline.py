"""
Main Claimify pipeline orchestrator.
This module contains the ClaimifyPipeline class that coordinates the three-stage
processing: Selection → Disambiguation → Decomposition.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .agents import (
    DecompositionAgent,
    DisambiguationAgent,
    LLMInterface,
    SelectionAgent,
)
from .data_models import (
    ClaimifyConfig,
    ClaimifyContext,
    ClaimifyResult,
    SentenceChunk,
)

logger = logging.getLogger(__name__)


class ClaimifyPipeline:
    """
    Main pipeline orchestrator for the Claimify claim extraction process.
    Coordinates the three stages:
    1. Selection - Identify relevant sentence chunks
    2. Disambiguation - Rewrite sentences to remove ambiguities
    3. Decomposition - Break sentences into atomic claims
    Supports model injection and context windowing as per the architecture requirements.
    """

    def __init__(
        self,
        config: Optional[ClaimifyConfig] = None,
        selection_llm: Optional[LLMInterface] = None,
        disambiguation_llm: Optional[LLMInterface] = None,
        decomposition_llm: Optional[LLMInterface] = None,
    ):
        """
        Initialize the Claimify pipeline.
        Args:
            config: Pipeline configuration
            selection_llm: LLM instance for Selection stage
            disambiguation_llm: LLM instance for Disambiguation stage
            decomposition_llm: LLM instance for Decomposition stage
        """
        self.config = config or ClaimifyConfig()
        self.logger = logging.getLogger(f"{__name__}.ClaimifyPipeline")
        # Initialize agents with their respective LLMs
        self.selection_agent = SelectionAgent(llm=selection_llm, config=self.config)
        self.disambiguation_agent = DisambiguationAgent(
            llm=disambiguation_llm, config=self.config
        )
        self.decomposition_agent = DecompositionAgent(
            llm=decomposition_llm, config=self.config
        )
        self.logger.info(
            "[pipeline.ClaimifyPipeline.__init__] Claimify pipeline initialized",
            extra={
                "service": "aclarai-core",
                "pipeline": "claimify",
                "config": {
                    "context_window_p": self.config.context_window_p,
                    "context_window_f": self.config.context_window_f,
                    "selection_model": self.config.get_model_for_stage("selection"),
                    "disambiguation_model": self.config.get_model_for_stage(
                        "disambiguation"
                    ),
                    "decomposition_model": self.config.get_model_for_stage(
                        "decomposition"
                    ),
                },
            },
        )

    def process_sentences(self, sentences: List[SentenceChunk]) -> List[ClaimifyResult]:
        """
        Process a list of sentence chunks through the complete Claimify pipeline.
        Args:
            sentences: List of sentence chunks to process
        Returns:
            List of ClaimifyResult objects with processing results
        """
        if not sentences:
            self.logger.warning(
                "[pipeline.ClaimifyPipeline.process] No sentences provided for processing"
            )
            return []
        self.logger.info(
            f"[pipeline.ClaimifyPipeline.process] Starting Claimify pipeline processing for {len(sentences)} sentences",
            extra={
                "service": "aclarai-core",
                "pipeline": "claimify",
                "sentence_count": len(sentences),
            },
        )
        results = []
        total_start_time = time.time()
        for i, sentence in enumerate(sentences):
            try:
                # Build context window for this sentence
                context = self._build_context_window(sentence, sentences, i)
                # Process the sentence through the pipeline
                result = self.process_sentence(context)
                results.append(result)
            except Exception as e:
                self.logger.error(
                    f"[pipeline.ClaimifyPipeline.process] Error processing sentence {i}: {e}",
                    extra={
                        "service": "aclarai-core",
                        "pipeline": "claimify",
                        "sentence_index": i,
                        "error": str(e),
                    },
                )
                # Create error result
                context = self._build_context_window(sentence, sentences, i)
                error_result = ClaimifyResult(
                    original_chunk=sentence,
                    context=context,
                    errors=[f"Pipeline error: {e}"],
                )
                results.append(error_result)
        total_processing_time = time.time() - total_start_time
        # Log summary statistics
        processed_count = sum(1 for r in results if r.was_processed)
        total_claims = sum(len(r.final_claims) for r in results)
        total_sentences = sum(len(r.final_sentences) for r in results)
        self.logger.info(
            f"[pipeline.ClaimifyPipeline.process] Claimify pipeline completed: {processed_count}/{len(sentences)} processed, "
            f"{total_claims} claims, {total_sentences} sentence nodes",
            extra={
                "service": "aclarai-core",
                "pipeline": "claimify",
                "total_sentences": len(sentences),
                "processed_sentences": processed_count,
                "total_claims": total_claims,
                "total_sentence_nodes": total_sentences,
                "total_processing_time": total_processing_time,
            },
        )
        return results

    def process_sentence(self, context: ClaimifyContext) -> ClaimifyResult:
        """
        Process a single sentence through the complete Claimify pipeline.
        Args:
            context: ClaimifyContext with the sentence and surrounding context
        Returns:
            ClaimifyResult with the processing outcome
        """
        sentence = context.current_sentence
        start_time = time.time()
        result = ClaimifyResult(
            original_chunk=sentence,
            context=context,
        )
        try:
            # Stage 1: Selection
            self.logger.debug(
                f"[pipeline.ClaimifyPipeline.process_sentence] Processing sentence through Selection: {sentence.text[:50]}...",
                extra={
                    "service": "aclarai-core",
                    "pipeline": "claimify",
                    "stage": "selection",
                    "sentence_id": sentence.chunk_id,
                },
            )
            selection_result = self.selection_agent.process(context)
            result.selection_result = selection_result
            # If not selected, stop processing
            if not selection_result.is_selected:
                result.total_processing_time = time.time() - start_time
                return result
            # Stage 2: Disambiguation
            self.logger.debug(
                f"[pipeline.ClaimifyPipeline.process_sentence] Processing sentence through Disambiguation: {sentence.text[:50]}...",
                extra={
                    "service": "aclarai-core",
                    "pipeline": "claimify",
                    "stage": "disambiguation",
                    "sentence_id": sentence.chunk_id,
                },
            )
            disambiguation_result = self.disambiguation_agent.process(sentence, context)
            result.disambiguation_result = disambiguation_result
            # Stage 3: Decomposition
            self.logger.debug(
                f"[pipeline.ClaimifyPipeline.process_sentence] Processing sentence through Decomposition: {disambiguation_result.disambiguated_text[:50]}...",
                extra={
                    "service": "aclarai-core",
                    "pipeline": "claimify",
                    "stage": "decomposition",
                    "sentence_id": sentence.chunk_id,
                },
            )
            decomposition_result = self.decomposition_agent.process(
                disambiguation_result.disambiguated_text, sentence
            )
            result.decomposition_result = decomposition_result
            result.total_processing_time = time.time() - start_time
            return result
        except Exception as e:
            result.total_processing_time = time.time() - start_time
            result.errors.append(f"Pipeline processing error: {e}")
            self.logger.error(
                f"[pipeline.ClaimifyPipeline.process_sentence] Error in pipeline processing: {e}",
                extra={
                    "service": "aclarai-core",
                    "pipeline": "claimify",
                    "sentence_id": sentence.chunk_id,
                    "error": str(e),
                },
            )
            return result

    def _build_context_window(
        self,
        current_sentence: SentenceChunk,
        all_sentences: List[SentenceChunk],
        current_index: int,
    ) -> ClaimifyContext:
        """
        Build context window with preceding and following sentences.
        Args:
            current_sentence: The sentence to process
            all_sentences: All available sentences
            current_index: Index of current sentence in the list
        Returns:
            ClaimifyContext with context window
        """
        # Get preceding sentences (p)
        start_p = max(0, current_index - self.config.context_window_p)
        preceding = all_sentences[start_p:current_index]
        # Get following sentences (f)
        end_f = min(
            len(all_sentences), current_index + 1 + self.config.context_window_f
        )
        following = all_sentences[current_index + 1 : end_f]
        context = ClaimifyContext(
            current_sentence=current_sentence,
            preceding_sentences=preceding,
            following_sentences=following,
        )
        self.logger.debug(
            f"[pipeline.ClaimifyPipeline._build_context_window] Built context window: p={len(preceding)}, f={len(following)}",
            extra={
                "service": "aclarai-core",
                "pipeline": "claimify",
                "sentence_id": current_sentence.chunk_id,
                "context_p": len(preceding),
                "context_f": len(following),
            },
        )
        return context

    def get_pipeline_stats(self, results: List[ClaimifyResult]) -> Dict[str, Any]:
        """
        Generate pipeline statistics from processing results.
        Args:
            results: List of ClaimifyResult objects
        Returns:
            Dictionary with pipeline statistics
        """
        total_sentences = len(results)
        processed_sentences = sum(1 for r in results if r.was_processed)
        total_claims = sum(len(r.final_claims) for r in results)
        total_sentence_nodes = sum(len(r.final_sentences) for r in results)
        # Calculate processing times
        selection_times = [
            r.selection_result.processing_time
            for r in results
            if r.selection_result and r.selection_result.processing_time
        ]
        disambiguation_times = [
            r.disambiguation_result.processing_time
            for r in results
            if r.disambiguation_result and r.disambiguation_result.processing_time
        ]
        decomposition_times = [
            r.decomposition_result.processing_time
            for r in results
            if r.decomposition_result and r.decomposition_result.processing_time
        ]
        total_times = [
            r.total_processing_time for r in results if r.total_processing_time
        ]
        stats = {
            "pipeline": "claimify",
            "total_sentences": total_sentences,
            "processed_sentences": processed_sentences,
            "selection_rate": processed_sentences / total_sentences
            if total_sentences > 0
            else 0,
            "total_claims": total_claims,
            "total_sentence_nodes": total_sentence_nodes,
            "claims_per_processed": total_claims / processed_sentences
            if processed_sentences > 0
            else 0,
            "errors": sum(len(r.errors) for r in results),
            "timing": {
                "selection_avg": sum(selection_times) / len(selection_times)
                if selection_times
                else 0,
                "disambiguation_avg": sum(disambiguation_times)
                / len(disambiguation_times)
                if disambiguation_times
                else 0,
                "decomposition_avg": sum(decomposition_times) / len(decomposition_times)
                if decomposition_times
                else 0,
                "total_avg": sum(total_times) / len(total_times) if total_times else 0,
            },
        }
        return stats
