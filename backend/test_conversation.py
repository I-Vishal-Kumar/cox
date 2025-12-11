import asyncio
from app.agents.langchain_orchestrator import LangChainAnalyticsOrchestrator

async def test_conversation_history():
    orchestrator = LangChainAnalyticsOrchestrator()
    
    # First message
    print("\n=== FIRST MESSAGE ===")
    chunks = []
    async for chunk in orchestrator.process_query_stream(
        query="hello",
        session_id="5ae34a83-c9bd-4fa7-95b7-ad68bbd792a6"
    ):
        if chunk["type"] == "chunk":
            chunks.append(chunk["content"])
        elif chunk["type"] == "complete":
            print(f"Complete result: {chunk['result']['analysis'][:200]}")
    
    # Second message - should have history
    print("\n\n=== SECOND MESSAGE (should have history) ===")
    chunks = []
    async for chunk in orchestrator.process_query_stream(
        query="what can you help me with?",
        session_id="5ae34a83-c9bd-4fa7-95b7-ad68bbd792a6"
    ):
        if chunk["type"] == "chunk":
            chunks.append(chunk["content"])
        elif chunk["type"] == "complete":
            print(f"Complete result: {chunk['result']['analysis'][:200]}")

if __name__ == "__main__":
    asyncio.run(test_conversation_history())
