"""
LLM Services for Data Intake Pipeline

Three-layer LLM processing:
- L2: Normalization (GPT-4 Strict Mode)
- L3: Feature Engineering (Claude 3.5 Sonnet)
- L4: Analysis & Insights (Perplexity Sonar / Claude fallback)

Usage:
    from data_intake.llm import NormalizationService, FeatureService, AnalysisService

    # L2: Normalize raw events
    normalizer = NormalizationService()
    normalized = await normalizer.normalize(raw_events)

    # L3: Calculate features
    features = FeatureService()
    features_data = await features.calculate(normalized_events)

    # L4: Generate insights
    analyzer = AnalysisService()
    insights = await analyzer.analyze(features_data)
"""

from data_intake.llm.base import BaseLLMService, LLMConfig, LLMProvider
from data_intake.llm.normalization import NormalizationService
from data_intake.llm.features import FeatureService
from data_intake.llm.analysis import AnalysisService
from data_intake.llm.pipeline import LLMPipeline, process_events

__all__ = [
    "BaseLLMService",
    "LLMConfig",
    "LLMProvider",
    "NormalizationService",
    "FeatureService",
    "AnalysisService",
    "LLMPipeline",
    "process_events",
]
