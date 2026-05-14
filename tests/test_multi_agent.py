# scripts/test_multi_agent.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from src.agents.graph_builder import build_medical_graph
from src.agents.state import create_initial_state

def main():
    graph = build_medical_graph()
    query = input("Enter your medical question: ")
    state = create_initial_state(query)
    result = graph.invoke(state)
    print("\n" + "="*60)
    print("FINAL ANSWER:\n")
    print(result["final_answer"])
    if result["citations"]:
        print("\nCITATIONS:")
        for c in result["citations"]:
            print(f"[{c['id']}] {c['source']} - {c['text_snippet'][:100]}...")

if __name__ == "__main__":
    main()