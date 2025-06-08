# This file makes the 'tasks' directory a Python package.
from .feature_extraction import FeatureExtractionTask
from .analysis_tests import AnalyseTestsTask
from .code_analysis import CodeAnalysisTask
from .code_summarization import CodeSummarizationTask

__all__ = [
    "FeatureExtractionTask",
    "AnalyseTestsTask",
    "CodeAnalysisTask",
    "CodeSummarizationTask",
]
