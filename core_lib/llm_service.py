# core_library/llm_services.py
from openai import OpenAI

class OpenAIService:
    """
    A wrapper class for the OpenAI API client.
    This encapsulates the client setup and provides a simple interface for making calls.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key cannot be empty.")
        # Initialize the OpenAI client with the provided key
        self.client = OpenAI(api_key=api_key)

    def invoke(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Sends a prompt to the specified OpenAI model and returns the text response.
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            # Extract and return the content of the message from the first choice
            return response.choices[0].message.content
        except Exception as e:
            # Basic error handling
            print(f"An error occurred while calling the OpenAI API: {e}")
            return "Sorry, I encountered an error."