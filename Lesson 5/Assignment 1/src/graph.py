"""Assembles the supervisor + specialist agents into a LangGraph StateGraph."""

from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from src.supervisor import classify
from src.agents import build_it_agent, build_finance_agent


class SupportState(TypedDict):
    messages: Annotated[list, add_messages]
    category: str


def build_graph():
    it_agent = build_it_agent()
    finance_agent = build_finance_agent()

    def supervisor_node(state: SupportState) -> dict:
        query = state["messages"][-1].content
        return {"category": classify(query)}

    def it_node(state: SupportState) -> dict:
        result = it_agent.invoke({"messages": state["messages"]})
        return {"messages": [result["messages"][-1]]}

    def finance_node(state: SupportState) -> dict:
        result = finance_agent.invoke({"messages": state["messages"]})
        return {"messages": [result["messages"][-1]]}

    def route(state: SupportState) -> str:
        return state["category"]

    graph = StateGraph(SupportState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("it", it_node)
    graph.add_node("finance", finance_node)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor", route, {"it": "it", "finance": "finance"}
    )
    graph.add_edge("it", END)
    graph.add_edge("finance", END)

    return graph.compile()
