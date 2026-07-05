from pathlib import Path

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.rails.llm.options import GenerationOptions

_CONFIG_PATH = Path(__file__).resolve().parent / "guardrails_config"

_config = RailsConfig.from_path(str(_CONFIG_PATH))
_rails = LLMRails(_config)


def _response_text(result) -> str:
    response = result.response
    if isinstance(response, list):
        return response[0].get("content", "") if response else ""
    return response


def _rail_stopped(result, rail_type: str) -> bool:
    """A rail blocked the message if any activated rail of this type halted the flow."""
    log = getattr(result, "log", None)
    activated = getattr(log, "activated_rails", None) if log else None
    return any(
        getattr(rail, "type", None) == rail_type and getattr(rail, "stop", False)
        for rail in activated or []
    )


def check_input(query: str) -> tuple[bool, str]:
    result = _rails.generate(
        messages=[{"role": "user", "content": query}],
        options=GenerationOptions(rails=["input"], log={"activated_rails": True}),
    )
    was_blocked = _rail_stopped(result, "input")
    return not was_blocked, (_response_text(result) if was_blocked else "")


def check_output(text: str) -> tuple[bool, str]:
    result = _rails.generate(
        messages=[
            {"role": "user", "content": "(internal output check)"},
            {"role": "assistant", "content": text},
        ],
        options=GenerationOptions(rails=["output"], log={"activated_rails": True}),
    )
    was_blocked = _rail_stopped(result, "output")
    return not was_blocked, (_response_text(result) if was_blocked else text)
