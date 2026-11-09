import asyncio

from anthropic import AsyncAnthropic
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

with open("src/prompts/system.md", "r") as f:
    system_prompt = f.read()

# Step 1: client takes only the api key; system prompt is a per-request param
client = AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value())


async def ask(question: str, *, system: str | None = None) -> LLMResult:

    inMessages = [
        {"role": "user", "content": question},
    ]
    outMessage = await client.messages.create(
        max_tokens=10000,
        messages=inMessages,
        model=settings.anthropic_model,
        # Step 2: top-level `system`, caller's value overrides the file default
        system=system if system is not None else system_prompt,
    )
    print(outMessage.content)
    return LLMResult(
        text=outMessage.content[0].text,
        # Step 3: token counts live under `usage`
        input_tokens=outMessage.usage.input_tokens,
        output_tokens=outMessage.usage.output_tokens,
        stop_reason=outMessage.stop_reason,
        latency_ms=outMessage.latency_ms,  # still broken: fix next (time it yourself)
        model=outMessage.model,
    )


async def main() -> None:
    await ask(
        "Say hi in five words in 2 languages",
        system="You are a helpful assistant that translates text into multiple languages.",
    )


if __name__ == "__main__":
    asyncio.run(main())
