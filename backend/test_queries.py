
import asyncio
import httpx
import json

API_URL = "http://localhost:8000/api/v1/chat/stream"
OUTPUT_FILE = "businessInteligence.txt"

# Defined standalone questions as context might not be preserved
QUERIES = [
    "How is F&I revenue performing in the Midwest?",
    "Show F&I revenue performance in the Midwest broken down by dealer", 
    "Show weekly F&I revenue trends in the Midwest",
    "Why did F&I revenue drop in the Midwest?"
]

async def run_queries():
    conversation_id = None
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx, query in enumerate(QUERIES):
            print(f"Sending query {idx+1}/{len(QUERIES)}: {query}")
            
            params = {"message": query}
            if conversation_id:
                params["conversation_id"] = conversation_id
                
            full_response_text = ""
            
            try:
                async with client.stream("GET", API_URL, params=params) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            try:
                                data = json.loads(data_str)
                                event_type = data.get("type")
                                
                                if event_type == "start":
                                    if not conversation_id:
                                        conversation_id = data.get("conversation_id")
                                
                                elif event_type == "chunk":
                                    content = data.get("content", "")
                                    if isinstance(content, list):
                                        content = "".join([str(c) for c in content])
                                    else:
                                        content = str(content)
                                    full_response_text += content
                                    print(content, end="", flush=True)
                                    
                                elif event_type == "complete":
                                    # Use the final analysis from result if available, or accumulated text
                                    res_data = data.get("result", {})
                                    analysis = res_data.get("analysis", "")
                                    if analysis and len(analysis) > len(full_response_text):
                                        full_response_text = analysis
                                    print("\n--- Response Complete ---\n")
                                    
                                elif event_type == "error":
                                    print(f"\nError received: {data.get('error')}")
                                    full_response_text = f"ERROR: {data.get('error')}"
                                    
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                print(f"Request failed: {e}")
                full_response_text = f"Request Failed: {e}"

            results.append(f"Question: {query}\nResponse: {full_response_text}\n{'-'*40}\n")
            
            # Small delay between requests
            await asyncio.sleep(1)

    # Write results to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(results))
    
    print(f"Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(run_queries())
