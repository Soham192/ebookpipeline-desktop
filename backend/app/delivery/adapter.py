from abc import ABC, abstractmethod
from pathlib import Path


class DeliveryAdapter(ABC):
    @abstractmethod
    def deliver(self, epub_path: Path, metadata: dict[str, str], destination: str) -> dict[str, str | bool]:
        pass
