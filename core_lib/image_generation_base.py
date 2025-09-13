# core_library/image_generators_base.py
from abc import ABC, abstractmethod
from io import BytesIO

class BaseImageGenerator(ABC):
    @abstractmethod
    async def generate_image_async(self, prompt: str) -> BytesIO:
        pass