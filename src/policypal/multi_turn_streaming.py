import asyncio
import logging
import time
from pathlib import Path

import anthropic
from anthropic import AsyncAnthropic, Omit, omit
from anthropic.types import MessageParam, ThinkingConfigAdaptiveParam
from pydantic import BaseModel

from policypal.config import get_settings


class LLMResult(BaseModel):
    text: str
    input_tokens: int
    output_tokens: int
    stop_reason: str | None = None
    latency_ms: int
    model: str
    usage: str | None = None


logger = logging.getLogger(__name__)

settings = get_settings()

system_prompt = (Path(__file__).parent / "prompts" / "system.md").read_text()

client = AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value())


async def ask(
    messages: list[MessageParam], *, system: str | None = None, thinking: bool = False
) -> LLMResult:
    t0 = time.perf_counter()
    inMessages: list[MessageParam] = messages

    thinking_cfg: ThinkingConfigAdaptiveParam | Omit = (
        {"type": "adaptive"} if thinking else omit
    )

    async with client.messages.stream(
        max_tokens=1000,
        messages=inMessages,
        model=settings.anthropic_model,
        system=system if system is not None else system_prompt,
        output_config={
            "effort": "low"  # Options: "low", "medium", "high", "xhigh", "max"
        },
        thinking=thinking_cfg,
    ) as stream:
        async for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
        print()

        outMessage = await stream.get_final_message()

    latency_ms = int((time.perf_counter() - t0) * 1000)

    if outMessage.stop_reason == "max_tokens":
        logger.warning("Response truncated at max_tokens (model=%s)", outMessage.model)

    text = "".join(b.text for b in outMessage.content if b.type == "text")
    return LLMResult(
        text=text,
        input_tokens=outMessage.usage.input_tokens,
        output_tokens=outMessage.usage.output_tokens,
        latency_ms=latency_ms,
        stop_reason=outMessage.stop_reason,
        model=outMessage.model,
        usage=str(outMessage.usage),
    )


async def main() -> None:
    conversation_history = list[MessageParam]()

    while True:
        user_input = input("Enter your question (or 'exit' to quit): ")
        if user_input.lower() == "exit":
            break

        conversation_history.append({"role": "user", "content": user_input})
        try:
            result = await ask(conversation_history)
        except anthropic.RateLimitError:
            logger.warning("Rate limited. Wait a bit and try again.")
            conversation_history.pop()
            continue
        except anthropic.APIConnectionError as e:
            logger.error("Can't reach the API: %s", e.__cause__)
            conversation_history.pop()
            continue
        except anthropic.APIStatusError as e:
            # Covers 401 bad key, 404 bad model, 400 bad request, 5xx, etc.
            logger.error("API returned %s: %s", e.status_code, e.message)
            conversation_history.pop()
            continue

        assistant_reply = result.text
        # Text was already streamed inside ask(); just log usage here.
        logger.info(
            "tokens in=%d out=%d latency_ms=%d stop=%s",
            result.input_tokens,
            result.output_tokens,
            result.latency_ms,
            result.stop_reason,
        )

        conversation_history.append({"role": "assistant", "content": assistant_reply})


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(main())
