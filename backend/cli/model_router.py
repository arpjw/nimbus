"""
ModelRouter: route each Nimbus phase to the configured model.

Config (in ~/.nimbus/config.toml):
[models]
planner     = "claude-opus-4-6"
implementer = "claude-sonnet-4-6"
reviewer    = "claude-haiku-4-5-20251001"
chat        = "claude-sonnet-4-6"

# Optional: OpenAI
[models.openai]
enabled = false
api_key = ""  # or set OPENAI_API_KEY env var

# Optional: Ollama (local models)
[models.ollama]
enabled = false
base_url = "http://localhost:11434"
planner = "deepseek-coder:33b"
"""

import os
from typing import Optional, Literal

Role = Literal["planner", "implementer", "reviewer", "chat"]

DEFAULTS: dict[Role, str] = {
    "planner":     "claude-opus-4-6",
    "implementer": "claude-sonnet-4-6",
    "reviewer":    "claude-haiku-4-5-20251001",
    "chat":        "claude-sonnet-4-6",
}

ANTHROPIC_MODELS = {"claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"}
OPENAI_MODELS = {"gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"}


def _load_config() -> dict:
    config_path = os.path.expanduser("~/.nimbus/config.toml")
    if not os.path.exists(config_path):
        return {}
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            return {}
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f).get("models", {})
    except Exception:
        return {}


class ModelRouter:
    def __init__(self):
        self._config = _load_config()

    def get_model(self, role: Role) -> str:
        return self._config.get(role, DEFAULTS[role])

    def get_provider(self, role: Role) -> str:
        model = self.get_model(role)
        if model in OPENAI_MODELS:
            return "openai"
        if self._config.get("ollama", {}).get("enabled") and model in (
            self._config.get("ollama", {}).get(role, ""),
        ):
            return "ollama"
        return "anthropic"

    async def complete(
        self,
        role: Role,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> str:
        model = self.get_model(role)
        provider = self.get_provider(role)

        if provider == "anthropic":
            return await self._anthropic_complete(model, messages, system, max_tokens)
        elif provider == "openai":
            return await self._openai_complete(model, messages, system, max_tokens)
        elif provider == "ollama":
            return await self._ollama_complete(model, messages, system, max_tokens)
        else:
            return await self._anthropic_complete(model, messages, system, max_tokens)

    async def _anthropic_complete(
        self, model: str, messages: list[dict], system: Optional[str], max_tokens: int
    ) -> str:
        import anthropic
        client = anthropic.AsyncAnthropic()
        kwargs: dict = dict(model=model, max_tokens=max_tokens, messages=messages)
        if system:
            kwargs["system"] = system
        response = await client.messages.create(**kwargs)
        return response.content[0].text

    async def _openai_complete(
        self, model: str, messages: list[dict], system: Optional[str], max_tokens: int
    ) -> str:
        try:
            import openai
        except ImportError:
            raise ImportError("pip install openai to use OpenAI models")

        api_key = self._config.get("openai", {}).get("api_key") or os.environ.get("OPENAI_API_KEY")
        client = openai.AsyncOpenAI(api_key=api_key)

        oai_messages = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        oai_messages.extend(messages)

        response = await client.chat.completions.create(
            model=model,
            messages=oai_messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def _ollama_complete(
        self, model: str, messages: list[dict], system: Optional[str], max_tokens: int
    ) -> str:
        import httpx
        base_url = self._config.get("ollama", {}).get("base_url", "http://localhost:11434")

        ollama_messages = []
        if system:
            ollama_messages.append({"role": "system", "content": system})
        ollama_messages.extend(messages)

        async with httpx.AsyncClient(timeout=120) as http:
            response = await http.post(
                f"{base_url}/api/chat",
                json={"model": model, "messages": ollama_messages, "stream": False},
            )
            data = response.json()
            return data["message"]["content"]


_router: Optional[ModelRouter] = None


def get_router() -> ModelRouter:
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router
