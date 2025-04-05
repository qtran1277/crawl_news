from abc import ABC, abstractmethod
from typing import Dict, List

class SentimentAnalyzerInterface(ABC):
    @abstractmethod
    def analyze_single(self, title: str) -> Dict[str, any]:
        """Analyze sentiment for a single title"""
        pass
    
    @abstractmethod
    def analyze_batch(self, titles: List[str], max_workers: int = 5) -> Dict[str, Dict[str, any]]:
        """Analyze sentiments for multiple titles concurrently"""
        pass 