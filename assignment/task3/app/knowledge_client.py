import httpx
from .config import settings

async def query_brain(question: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        response=await client.post(f"{settings.knowledge_brain_url}/query",
                                   json={"question":question,"top_k":5})
        response.raise_for_status()
        return response.json()
