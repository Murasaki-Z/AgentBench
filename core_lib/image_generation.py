# core_library/image_generation.py
import asyncio
import google.generativeai as genai
from io import BytesIO

from .image_generation_base import BaseImageGenerator

class GeminiImageGenerator(BaseImageGenerator):
    """
    Image generation using Google's Gemini models, following the modern
    image generation API pattern.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Google API key cannot be empty for GeminiImageGenerator.")
        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel('models/gemini-2.5-flash-image-preview')

    async def generate_image_async(self, prompt: str) -> BytesIO:
        """
        Generates an image from a text prompt using the appropriate Gemini API call.
        """
        print(f"--- Gemini: Generating image for prompt: '{prompt[:50]}...' ---")
        try:
            # The core prompt is the description of the image.
            full_prompt = (
                f"Generate a single, photorealistic, beautifully lit, rustic-style photo of: {prompt}. "
                "Focus on the food, make it look appetizing, professional food photography."
            )
            
            response = await self.model.generate_content_async(full_prompt)

            image_data = None
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:

                    if part.inline_data and 'image/' in part.inline_data.mime_type:
                        image_data = part.inline_data.data
                        break # Found the image, no need to look further

            if image_data:
                print("--- Gemini: Image generated and data extracted successfully. ---")
                return BytesIO(image_data)
            else:
                # This can happen if the prompt is rejected for safety reasons
                # or if the model fails to generate an image.
                print("--- Gemini: WARNING: Model generated a response, but no image data was found. ---")
                # We can inspect the response for safety ratings or text feedback
                if response.prompt_feedback:
                    print(f"--- Gemini: Prompt Feedback: {response.prompt_feedback} ---")
                return BytesIO()

        except Exception as e:
            print(f"--- Gemini: ERROR during image generation or processing: {e} ---")
            return BytesIO()

class OpenAIImageGenerator(BaseImageGenerator):
    """Placeholder for image generation using OpenAI's DALL-E models."""
    def __init__(self, api_key: str):
        print("--- OpenAIImageGenerator: Initialized (placeholder). ---")
        if not api_key:
             raise ValueError("OpenAI API key cannot be empty for OpenAIImageGenerator.")

    async def generate_image_async(self, prompt: str) -> BytesIO:
        print(f"--- OpenAIImageGenerator: generate_image_async called (placeholder). ---")
        await asyncio.sleep(1)
        return BytesIO()

def get_image_generator(provider: str, openai_key: str, google_key: str | None) -> BaseImageGenerator:
    if provider == "gemini":
        if not google_key:
            print("--- Factory WARN: Gemini is the provider, but no GOOGLE_API_KEY is set. Using placeholder. ---")
            return OpenAIImageGenerator(api_key=openai_key)
        return GeminiImageGenerator(api_key=google_key)
    elif provider == "openai":
        return OpenAIImageGenerator(api_key=openai_key)
    else:
        raise ValueError(f"Unknown image generation provider: {provider}")