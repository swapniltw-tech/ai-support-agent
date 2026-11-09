from anthropic import Anthropic

from policypal.config import get_settings

# Testing call to anthropic API using the settings from the .env file. The .env file should contain the ANTHROPIC_API_KEY and ANTHROPIC_MODEL values.


def main() -> None:
    settings = get_settings()
    client = Anthropic(api_key=settings.anthropic_api_key.get_secret_value())

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=100,
        messages=[{"role": "user", "content": "Say hi in five words in 2 languages"}],
    )
    for block in response.content:
        print(f"[{block.type}]")  # temporary: shows what came back
        if block.type == "text":
            print(block.text)

    print(
        "i stopped because, ", response.stop_reason
    )  # "end_turn" is good, "max_tokens" means truncated

    print(response.model_dump_json(indent=2))  # whole response as JSON


if __name__ == "__main__":
    main()
