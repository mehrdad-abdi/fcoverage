# This file makes the 'tasks' directory a Python package.
from .feature_extraction import FeatureExtractionTask
from .analysis_tests import AnalyseTestsTask
from .sourcecode_embedding import SourceCodeEmbeddingTask

__all__ = [
    "FeatureExtractionTask",
    "AnalyseTestsTask",
    "SourceCodeEmbeddingTask",
]
