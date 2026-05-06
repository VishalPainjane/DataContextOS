"""
Ragas Evaluation — Runs evaluation metrics on RAG responses.
"""

import logging
from typing import List, Dict, Any

from config import settings

logger = logging.getLogger(__name__)

class RagasEvaluator:
    """Evaluates RAG generation using Ragas metrics."""
    
    def __init__(self):
        # Imports are here to prevent slowing down normal execution
        try:
            from ragas import evaluate
            from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
            from datasets import Dataset
            
            self.evaluate = evaluate
            self.metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
            self.Dataset = Dataset
            self.initialized = True
        except ImportError:
            logger.warning("Ragas or Datasets not installed. Evaluation disabled.")
            self.initialized = False

    def run_evaluation(self, queries: List[str], answers: List[str], contexts: List[List[str]], ground_truths: List[str]) -> Dict[str, Any]:
        """Run evaluation on a batch of queries."""
        if not self.initialized:
            return {"error": "Ragas evaluator not initialized."}
            
        data = {
            "question": queries,
            "answer": answers,
            "contexts": contexts,
            "ground_truths": [[gt] for gt in ground_truths]
        }
        
        dataset = self.Dataset.from_dict(data)
        logger.info(f"Running evaluation on {len(queries)} samples...")
        
        # Use appropriate LLM for evaluation based on settings
        result = self.evaluate(
            dataset=dataset,
            metrics=self.metrics,
        )
        
        return result
