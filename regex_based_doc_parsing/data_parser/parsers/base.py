from typing import Dict, List
from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def extract_and_split(self, data: Dict) -> List[Dict[str, str]]:
        pass
