import json
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from agentevals.trajectory.match import create_trajectory_match_evaluator
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT

from agent import build_agent
from guardrails import check_input
from observability import get_langfuse_handler
from eval.dataset import DATASET

_RESULTS_PATH = Path(__file__).resolve().parent / "results.json"

trajectory_match = create_trajectory_match_evaluator(
    trajectory_match_mode="unordered", tool_args_match_mode="ignore"
)
trajectory_judge = create_trajectory_llm_as_judge(
    prompt=TRAJECTORY_ACCURACY_PROMPT, model="openai:gpt-4o-mini"
)


def _tool_calls(messages) -> list[str]:
    names = []
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            names.append(call["name"])
    return names


def run_case(agent, handler, case: dict) -> dict:
    query = case["query"]
    start = time.time()

    allowed, _ = check_input(query)
    if not allowed:
        return {
            "id": case["id"],
            "category": case["category"],
            "blocked_by_input_guardrail": True,
            "actual_tools": [],
            "expected_tools": case["expected_tools"],
            "trajectory_match": case["category"] == "adversarial",
            "judge_score": None,
            "latency_s": round(time.time() - start, 2),
        }

    config = {"callbacks": [handler]} if handler else {}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": query}]}, config=config
    )
    messages = result["messages"]
    actual_tools = _tool_calls(messages)

    match_result = trajectory_match(
        outputs=messages,
        reference_outputs=[{"role": "user", "content": query}],
    ) if case["category"] == "adversarial" else trajectory_match(
        outputs=messages,
        reference_outputs=_reference_messages(query, case["expected_tools"]),
    )

    judge_result = trajectory_judge(outputs=messages)

    return {
        "id": case["id"],
        "category": case["category"],
        "blocked_by_input_guardrail": False,
        "actual_tools": actual_tools,
        "expected_tools": case["expected_tools"],
        "trajectory_match": bool(match_result["score"]),
        "judge_score": judge_result["score"],
        "latency_s": round(time.time() - start, 2),
    }


def _reference_messages(query: str, expected_tools: list[str]) -> list[dict]:
    messages = [{"role": "user", "content": query}]
    for tool_name in expected_tools:
        messages.append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"id": tool_name, "name": tool_name, "args": {}}],
            }
        )
        messages.append({"role": "tool", "content": "", "tool_call_id": tool_name})
    return messages


def main():
    agent = build_agent()
    handler = get_langfuse_handler()

    results = []
    for case in DATASET:
        try:
            results.append(run_case(agent, handler, case))
        except Exception as e:
            results.append(
                {
                    "id": case["id"],
                    "category": case["category"],
                    "error": str(e),
                }
            )

    _RESULTS_PATH.write_text(json.dumps(results, indent=2))

    scored = [r for r in results if "error" not in r]
    matches = [r for r in scored if r["trajectory_match"]]
    judged = [r for r in scored if r["judge_score"] is not None]
    adversarial = [r for r in scored if r["category"] == "adversarial"]
    blocked = [r for r in adversarial if r["blocked_by_input_guardrail"]]

    print(f"Total cases: {len(results)}")
    print(f"Trajectory match rate: {len(matches)}/{len(scored)}")
    if judged:
        print(f"Avg judge score: {sum(r['judge_score'] for r in judged) / len(judged):.2f}")
    if adversarial:
        print(f"Guardrail block rate: {len(blocked)}/{len(adversarial)}")
    print(f"Results written to {_RESULTS_PATH}")


if __name__ == "__main__":
    main()
