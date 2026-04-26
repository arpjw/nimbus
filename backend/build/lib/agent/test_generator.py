import anthropic

from config import settings
from services.rag import RAGService

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

_SYSTEM = (
    "You are an expert software engineer writing a complete, production-quality "
    "test suite. Write tests that cover: happy paths, edge cases, error conditions, "
    "and boundary values. Match the style, imports, and conventions of any existing "
    "tests in the repository context. Output only the test file content, no "
    "explanation or markdown fences."
)

_EXT_FRAMEWORK: dict[str, str] = {
    ".py": "pytest",
    ".rs": "cargo test",
    ".go": "testing package",
}

_JS_EXTS = {".ts", ".tsx", ".js", ".jsx"}


def _detect_framework(file_path: str, context: str) -> str:
    ext = "." + file_path.rsplit(".", 1)[-1] if "." in file_path else ""
    if ext in _EXT_FRAMEWORK:
        return _EXT_FRAMEWORK[ext]
    if ext in _JS_EXTS:
        if "vitest" in context or "from 'vitest'" in context or 'from "vitest"' in context:
            return "vitest"
        return "jest"
    return "unknown"


async def generate_tests(
    file_path: str,
    content: str,
    repo_id: str,
    rag_service: RAGService,
) -> str:
    chunks = await rag_service.query([repo_id], f"tests for {file_path}", top_k=10)

    context_blocks = []
    context_text = ""
    for chunk in chunks:
        meta = chunk.metadata
        block = (
            f"### {meta.get('file_path', 'unknown')} "
            f"(lines {meta.get('start_line', '?')}-{meta.get('end_line', '?')})\n"
            f"{chunk.document}"
        )
        context_blocks.append(block)
        context_text += chunk.document + "\n"

    framework = _detect_framework(file_path, context_text)
    context = "\n\n".join(context_blocks)

    user_message = (
        f"## Source file: {file_path}\n\n"
        f"```\n{content}\n```\n\n"
        f"## Test framework: {framework}\n\n"
        f"## Existing test context from this repository\n\n{context}\n\n"
        "Write the complete test file for the source file above."
    )

    response = await client.messages.create(
        model=settings.implementer_model,
        max_tokens=8192,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text.strip()
