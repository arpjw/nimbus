import asyncio
import subprocess
from pathlib import Path
from typing import Optional

import anthropic

client = anthropic.AsyncAnthropic()


async def generate_test_suite(description: str, repo_path: Path, context_chunks: list[str]) -> str:
    context = "\n\n".join(context_chunks[:6])

    response = await client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"""You are a senior engineer writing a test suite BEFORE implementation (TDD).

Task: {description}

Codebase context:
{context}

Write a comprehensive test suite that:
1. Tests ALL expected behaviors described in the task
2. Tests edge cases and error conditions
3. Uses the existing test framework and patterns from the codebase
4. ALL tests must FAIL initially (before implementation)
5. Tests must be runnable with the existing test runner

Return ONLY the test code with no explanation. Include proper imports and test file header."""
        }]
    )
    return response.content[0].text


async def run_tests(repo_path: Path, test_file: Optional[Path] = None) -> tuple[bool, str, int]:
    if (repo_path / "pytest.ini").exists() or (repo_path / "pyproject.toml").exists():
        cmd = ["python", "-m", "pytest", "-v", "--tb=short"]
        if test_file:
            cmd.append(str(test_file))
    elif (repo_path / "package.json").exists():
        cmd = ["npm", "test", "--", "--passWithNoTests"]
        if test_file:
            cmd.extend(["--testPathPattern", str(test_file)])
    else:
        cmd = ["python", "-m", "pytest", "-v"]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=120,
        )
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        return passed, output, result.returncode
    except subprocess.TimeoutExpired:
        return False, "Tests timed out after 120s", 1
    except FileNotFoundError:
        return False, "Test runner not found", 1


async def find_test_file_path(repo_path: Path, description: str) -> Path:
    for test_dir in ["tests", "test", "__tests__", "spec"]:
        if (repo_path / test_dir).exists():
            slug = description[:40].lower().replace(" ", "_").replace("'", "")
            slug = "".join(c for c in slug if c.isalnum() or c == "_")
            return repo_path / test_dir / f"test_nimbus_tdd_{slug}.py"

    slug = description[:40].lower().replace(" ", "_").replace("'", "")
    slug = "".join(c for c in slug if c.isalnum() or c == "_")
    return repo_path / f"test_nimbus_tdd_{slug}.py"


async def run_tdd_task(
    description: str,
    repo_path: Path,
    context_chunks: list[str],
    executor,
    renderer,
) -> dict:
    from cli.renderer import console, GOLD, GREEN, RED, FAINT

    console.print(f"\n  [{GOLD}]◆ TDD mode[/{GOLD}]  [{FAINT}]write tests first, implement to pass[/{FAINT}]\n")

    console.print(f"  [{FAINT}]generating test suite...[/{FAINT}]")
    test_code = await generate_test_suite(description, repo_path, context_chunks)

    test_lines = test_code.strip().split("\n")
    test_functions = [l.strip() for l in test_lines if l.strip().startswith("def test_") or l.strip().startswith("it(")]

    console.print(f"\n  [{GOLD}]test plan[/{GOLD}]  [{FAINT}]{len(test_functions)} tests[/{FAINT}]\n")
    for fn in test_functions[:10]:
        console.print(f"  [{FAINT}]·[/{FAINT}] {fn.replace('def ', '').replace(':', '').strip()}")
    if len(test_functions) > 10:
        console.print(f"  [{FAINT}]... and {len(test_functions) - 10} more[/{FAINT}]")

    console.print(f"\n  Proceed with TDD? [y/N] ", end="")
    try:
        answer = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"

    if answer not in ("y", "yes"):
        console.print(f"\n  [{FAINT}]cancelled[/{FAINT}]\n")
        return {"status": "cancelled"}

    test_file = await find_test_file_path(repo_path, description)
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(test_code)
    console.print(f"\n  [{FAINT}]wrote[/{FAINT}] {test_file.relative_to(repo_path)}")

    console.print(f"  [{FAINT}]running tests (expecting failures)...[/{FAINT}]")
    passed, output, code = await run_tests(repo_path, test_file)

    if passed:
        console.print(f"  [{GOLD}]⚠[/{GOLD}]  tests already pass -- task may already be implemented")
    else:
        failed_count = output.count("FAILED") + output.count("✗") + output.count("failing")
        console.print(f"  [{GREEN}]✓[/{GREEN}]  {failed_count or len(test_functions)} tests failing as expected")

    console.print(f"\n  [{GOLD}]implementing to make tests pass...[/{GOLD}]\n")

    tdd_description = f"""{description}

IMPORTANT: This is TDD mode. The test file has already been written at {test_file}.
Your implementation MUST make all tests in that file pass.
After implementing, the test suite will be run to verify.
Do NOT modify the test file -- only implement the production code."""

    result = await executor.run_task(tdd_description)

    console.print(f"\n  [{FAINT}]verifying all tests pass...[/{FAINT}]")
    passed, output, code = await run_tests(repo_path, test_file)

    if passed:
        console.print(f"  [{GREEN}]✓[/{GREEN}]  all tests pass")
    else:
        failed = output.count("FAILED") + output.count("failing")
        console.print(f"  [{RED}]✗[/{RED}]  {failed} tests still failing")

    return {
        "status": "complete",
        "tests_pass": passed,
        "test_file": str(test_file),
        "test_output": output,
    }
