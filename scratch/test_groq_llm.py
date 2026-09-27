import asyncio
from app.core.cloud_llm import generate_text

async def test():
    res = await generate_text("Briefly summarize collision insurance in 1 line.")
    print("Cloud LLM Output:")
    print(res)

if __name__ == "__main__":
    asyncio.run(test())
