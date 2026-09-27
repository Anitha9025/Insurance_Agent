import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv("e:/Multi-Agent_Insurance_Claim_Support/backend/.env")

api_key = os.getenv("VISION_API_KEY") or os.getenv("GROQ_API_KEY")

async def test_groq():
    print(f"Testing Groq API key: {api_key[:10]}...")
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama-3.2-11b-vision-instruct"]
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        for model in models:
            try:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Hello, respond with OK."}],
                        "max_tokens": 10
                    }
                )
                print(f"Model '{model}' -> HTTP {res.status_code}: {res.text[:150]}")
            except Exception as e:
                print(f"Model '{model}' -> Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_groq())
