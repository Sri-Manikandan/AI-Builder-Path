from pathlib import Path

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.rails.llm.options import GenerationOptions

_CONFIG_PATH = Path(__file__).resolve().parent / "guardrails_config"

_config = RailsConfig.from_path(str(_CONFIG_PATH))
_rails = LLMRails(_config)


def check_input(query: str) -> tuple[bool, str]:
    result = _rails.generate(
        messages=[{"role": "user", "content": query}],
        options=GenerationOptions(rails=["input"]),
    )
    blocked = result.response[0]["content"] if isinstance(result.response, list) else result.response
    was_blocked = bool(result.output_data.get("triggered_input_rail")) if result.output_data else False
    return not was_blocked, (blocked if was_blocked else "")


def check_output(text: str) -> tuple[bool, str]:
    result = _rails.generate(
        messages=[
            {"role": "context", "content": {"bot_message": text}},
            {"role": "bot", "content": text},
        ],
        options=GenerationOptions(rails=["output"]),
    )
    was_blocked = bool(result.output_data.get("triggered_output_rail")) if result.output_data else False
    fallback = result.response[0]["content"] if isinstance(result.response, list) else result.response
    return not was_blocked, (fallback if was_blocked else text)
