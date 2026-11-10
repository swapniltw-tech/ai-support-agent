import asyncio
import time
from pathlib import Path

from anthropic import AsyncAnthropic, Omit, omit
from anthropic.types import Message, MessageParam, ThinkingConfigAdaptiveParam
from pydantic import BaseModel

from policypal.config import get_settings


class LLMResult(BaseModel):
    text: str
    input_tokens: int
    output_tokens: int
    stop_reason: str | None = None
    latency_ms: int
    model: str


settings = get_settings()

system_prompt = (Path(__file__).parent / "prompts" / "system.md").read_text()

client = AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value())


async def ask(
    question: str, *, system: str | None = None, thinking: bool = False
) -> LLMResult:
    t0 = time.perf_counter()
    inMessages: list[MessageParam] = [
        {"role": "user", "content": question},
    ]

    thinking_cfg: ThinkingConfigAdaptiveParam | Omit = (
        {"type": "adaptive"} if thinking else omit
    )

    outMessage: Message = await client.messages.create(
        max_tokens=1000,
        messages=inMessages,
        model=settings.anthropic_model,
        system=system if system is not None else system_prompt,
        output_config={
            "effort": "low"  # Options: "low", "medium", "high", "xhigh", "max"
        },
        thinking=thinking_cfg,
    )

    latency_ms = int((time.perf_counter() - t0) * 1000)

    if outMessage.stop_reason == "max_tokens":
        print("Warning: response truncated due to max_tokens limit.")

    print(
        f"usage is {outMessage.usage if outMessage.usage else 'No usage info available.'}"
    )
    text = "".join(b.text for b in outMessage.content if b.type == "text")
    return LLMResult(
        text=text,
        input_tokens=outMessage.usage.input_tokens,
        output_tokens=outMessage.usage.output_tokens,
        latency_ms=latency_ms,
        stop_reason=outMessage.stop_reason,
        model=outMessage.model,
    )


async def main() -> None:
    result = await ask(
        "Say hi in five words in 2 languages",
        system="You are a helpful assistant that translates text into multiple languages.",
    )

    print(f"Result: {result.text}")


if __name__ == "__main__":
    asyncio.run(main())
