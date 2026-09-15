"""Thin wrapper around Azure OpenAI chat completions.

Credentials come only from environment variables / Function App settings
(ideally Key Vault references) - never hardcode secrets here.
"""
import os

from openai import AzureOpenAI


class LLMConfigError(Exception):
    pass


def get_client() -> tuple:
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    if not endpoint or not api_key or not deployment:
        raise LLMConfigError(
            "AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY and AZURE_OPENAI_DEPLOYMENT "
            "must be set as Function App settings."
        )

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )
    return client, deployment


def chat(system_prompt: str, user_message: str, temperature: float = 0.2) -> str:
    client, deployment = get_client()
    response = client.chat.completions.create(
        model=deployment,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content or ""
