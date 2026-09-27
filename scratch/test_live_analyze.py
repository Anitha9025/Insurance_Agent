import urllib.request
import json

def test_live_analyze():
    # 1. Fetch claims list
    req = urllib.request.Request("http://127.0.0.1:8000/api/v1/claims")
    with urllib.request.urlopen(req) as res:
        claims = json.loads(res.read().decode())
        print(f"Total claims found: {len(claims)}")
        if not claims:
            print("No claims found to analyze.")
            return

        claim_id = claims[0]["id"]
        print(f"Triggering analysis for claim ID: {claim_id} ({claims[0]['claim_number']})")

    # 2. Trigger analyze endpoint
    analyze_url = f"http://127.0.0.1:8000/api/v1/claims/{claim_id}/analyze"
    post_req = urllib.request.Request(analyze_url, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(post_req) as res:
            data = json.loads(res.read().decode())
            print("SUCCESS! Workflow state returned:")
            print(f"- Status: {data.get('workflow_status')}")
            print(f"- Completed Agents: {data.get('completed_agents')}")
            print(f"- Tool Calls Count: {len(data.get('db_tool_calls', []))}")
            print(f"- RAG Analysis Citations: {len(data.get('rag_analysis', {}).get('citations', []))}")
            print(f"- Memory Precedents Count: {data.get('retrieved_memories', {}).get('similar_claims_count', 0)}")
    except urllib.error.HTTPError as err:
        print(f"HTTPError {err.code}: {err.read().decode()}")

if __name__ == "__main__":
    test_live_analyze()
