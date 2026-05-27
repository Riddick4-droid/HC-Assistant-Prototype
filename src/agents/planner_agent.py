# src/agents/planner_agent.py
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.config import settings
from src.agents.state import AgentState, Plan
from typing import List, Dict, Optional

class PlannerAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0
        )
        self.system_prompt = """You are a medical query planner. Given a user question, break it down into 1-3 sub‑queries, each targeting a specific knowledge source.

Available collections:
- gale_encyclopedia: general medical knowledge, symptoms, diseases, treatments
- daily_med: drug information, dosages, interactions, side effects
- pubmed_central: recent research papers, clinical studies

Output a JSON list with objects: {"query": "...", "collections": ["collection1", ...], "priority": integer (1 highest)}.

Example:
User: "What causes headaches and what painkillers are safe?"
Output: [
  {"query": "headache causes and pathophysiology", "collections": ["gale_encyclopedia"], "priority": 1},
  {"query": "safe painkillers for headache", "collections": ["daily_med", "pubmed_central"], "priority": 2}
]

Return ONLY the JSON array, no other text."""
    
    def plan(self, user_query: str, history: Optional[List[Dict]] = None) -> list[Plan]:
        context = ""
        if history:
            recent = history[-4:] if len(history) > 4 else history
            context = "\nPrevious conversation:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in recent])
        full_query = f"{context}\nCurrent query: {user_query}" if context else user_query
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=full_query)
        ]
        response = self.llm.invoke(messages)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        try:
            plans = json.loads(content)
            for p in plans:
                p.setdefault("priority", 1)
            return plans
        except Exception as e:
            print(f"Planner error: {e}\nResponse: {content}")
            return [{"query": user_query, "collections": ["gale_encyclopedia", "daily_med", "pubmed_central"], "priority": 1}]
    
    def __call__(self, state: AgentState) -> dict:
        # Convert LangChain message objects to dicts
        raw_messages = state.get("messages", [])
        history = []
        for m in raw_messages:
            if hasattr(m, 'type') and hasattr(m, 'content'):
                role = "user" if m.type == "human" else "assistant" if m.type == "ai" else m.type
                history.append({"role": role, "content": m.content})
            elif isinstance(m, dict):
                history.append(m)
        plans = self.plan(state["user_query"], history=history)
        return {"plans": plans}