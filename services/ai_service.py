from openai import OpenAI

from prompts.strategy_report import build_strategy_report_prompt


def build_openrouter_client(api_key: str) -> OpenAI:
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def generate_strategy_report(client: OpenAI, data, model: str = "google/gemini-2.5-flash", depth: str = "Orta") -> str:
    prompt = build_strategy_report_prompt(data, depth=depth)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8000,
    )
    return response.choices[0].message.content
