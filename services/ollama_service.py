from ollama import AsyncClient
from config import OLLAMA_HOST, OLLAMA_MODEL

class OllamaService:
    def __init__(self):
        self.client = AsyncClient(host=OLLAMA_HOST)
        self.model = OLLAMA_MODEL

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        json_format: bool = False
    ) -> str:
        options = {"temperature": temperature}
        request_data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "options": options
        }
        if json_format:
            request_data["format"] = "json"
        response = await self.client.chat(**request_data)
        return response["message"]["content"]
