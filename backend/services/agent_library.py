from dataclasses import dataclass
from typing import Optional


@dataclass
class BuiltinAgent:
    name: str
    category: str
    description: str
    full_description: str
    system_prompt: str
    retrieval_strategy: str
    verification_command: str
    estimated_prs: str
    dry_run_safe: bool = True


BUILTIN_AGENTS: dict[str, BuiltinAgent] = {

  "security-audit": BuiltinAgent(
    name="security-audit",
    category="security",
    description="Scan and fix OWASP Top 10 vulnerabilities across the codebase.",
    full_description="""Scans the entire codebase for OWASP Top 10 vulnerabilities --
SQL injection, XSS, insecure deserialization, hardcoded secrets, exposed credentials,
missing auth checks, insecure direct object references. Fixes each finding in a
separate PR with a description of the vulnerability and the remediation applied.""",
    system_prompt="""You are a security engineer auditing a codebase for OWASP Top 10 vulnerabilities.
For each file you analyze:
1. Look for: SQL injection (string interpolation in queries), XSS (unescaped user output),
   hardcoded secrets or credentials, missing authentication checks on sensitive routes,
   insecure direct object references, missing input validation.
2. Fix each vulnerability you find with the minimal, targeted change.
3. Add a comment above each fix explaining the vulnerability class and remediation.
4. Do NOT refactor unrelated code -- only fix security issues.
One PR per vulnerability class found.""",
    retrieval_strategy="full_codebase",
    verification_command="bandit -r . -ll || eslint --no-eslintrc -c '{\"plugins\":[\"security\"]}' .",
    estimated_prs="1 per finding",
  ),

  "secret-scanner": BuiltinAgent(
    name="secret-scanner",
    category="security",
    description="Find hardcoded secrets, move them to env vars, update references.",
    full_description="""Finds hardcoded API keys, passwords, tokens, and credentials across all files.
Moves secrets to environment variables, updates all references, generates a .env.example
with correct variable names, and adds secrets to .gitignore.""",
    system_prompt="""You are a security engineer finding and remediating hardcoded secrets.
Scan every file for: API keys, tokens, passwords, private keys, connection strings, credentials.
For each secret found:
1. Replace the hardcoded value with os.environ.get('VAR_NAME') or process.env.VAR_NAME
2. Add the variable name (not the value) to .env.example with a description
3. Ensure .gitignore includes .env
4. Update all references to use the env var
Never include actual secret values in any file.""",
    retrieval_strategy="full_codebase",
    verification_command="git grep -rE '[A-Za-z0-9]{32,}' --include='*.py' --include='*.ts' | grep -v '.env'",
    estimated_prs="1 total",
  ),

  "dependency-cve": BuiltinAgent(
    name="dependency-cve",
    category="security",
    description="Audit dependencies for CVEs and patch each to a safe version.",
    full_description="""Audits all dependencies for known CVEs. For each vulnerability:
patches to the fixed version if one exists, or replaces with a safe alternative
if the package is abandoned. Opens one PR per affected dependency.""",
    system_prompt="""You are a dependency security engineer.
Run the appropriate audit command for the detected package manager.
For each vulnerability found:
1. Update the dependency to the minimum safe version
2. Fix any breaking changes the update introduces
3. Document the CVE number and severity in the PR description
One PR per affected dependency.""",
    retrieval_strategy="full_codebase",
    verification_command="pip audit || npm audit --audit-level=high",
    estimated_prs="1 per finding",
  ),

  "type-safety": BuiltinAgent(
    name="type-safety",
    category="quality",
    description="Add full type annotations -- Python type hints or TypeScript strict mode.",
    full_description="""Adds full type annotations throughout the codebase. Python: type hints on all
functions and class attributes. TypeScript: strict mode compliance, removes all 'any' types
and replaces with proper interfaces. Runs the type checker after each file.""",
    system_prompt="""You are a type safety engineer adding complete type annotations.
For Python: add type hints to all function signatures and class attributes.
Use typing module for complex types. Avoid 'Any' unless genuinely necessary.
For TypeScript: remove all 'any' types. Create proper interfaces for object shapes.
Enable and satisfy strict mode. Run the type checker after each file and fix all errors.
Do not change any runtime behavior -- only add/improve types.""",
    retrieval_strategy="full_codebase",
    verification_command="mypy . --strict || tsc --noEmit --strict",
    estimated_prs="1 per file",
  ),

  "error-handling": BuiltinAgent(
    name="error-handling",
    category="quality",
    description="Wrap all external calls with typed error handling. No silent failures.",
    full_description="""Audits every function that can fail. Adds typed exception classes,
wraps all external calls in proper try/except or try/catch with specific error types,
ensures errors are logged with context before being re-raised or returned.""",
    system_prompt="""You are an error handling specialist.
For every external call (API, database, filesystem, network, third-party library):
1. Wrap in try/except (Python) or try/catch (TypeScript) with specific exception types
2. Log the error with context before re-raising: logger.error("context: %s", e)
3. Never swallow exceptions silently -- always log or re-raise
4. Create typed exception classes where they don't exist
5. Return typed error results where appropriate (Result pattern, Optional, etc.)
Do not change the happy path -- only add error handling.""",
    retrieval_strategy="full_codebase",
    verification_command="python -m py_compile **/*.py || tsc --noEmit",
    estimated_prs="1 per file",
  ),

  "dead-code-eliminator": BuiltinAgent(
    name="dead-code-eliminator",
    category="quality",
    description="Remove unused imports, variables, functions, and commented-out code.",
    full_description="""Finds and removes unreachable code, unused imports, unused variables,
unused functions, commented-out code blocks, and deprecated code paths that are never called.""",
    system_prompt="""You are a code quality engineer removing dead code.
Find and remove:
1. Unused imports (verify nothing uses them before removing)
2. Unused variables (assigned but never read)
3. Unused functions (defined but never called anywhere in the codebase)
4. Commented-out code blocks (not documentation comments -- actual disabled code)
5. Unreachable code after return/raise statements
Before removing any function, search the entire codebase to confirm it is truly unused.
Run tests after each removal to confirm nothing breaks.""",
    retrieval_strategy="full_codebase",
    verification_command="pytest -q || npm test -- --passWithNoTests",
    estimated_prs="1 per file",
  ),

  "complexity-reducer": BuiltinAgent(
    name="complexity-reducer",
    category="quality",
    description="Refactor functions with cyclomatic complexity > 10 to below 7.",
    full_description="""Identifies functions with cyclomatic complexity > 10. Refactors each one
by extracting sub-functions, simplifying conditionals, replacing complex switch statements
with lookup tables, and reducing nesting depth. Target: no function exceeds complexity 7.""",
    system_prompt="""You are a refactoring engineer reducing code complexity.
For each function with complexity > 10:
1. Extract logical sub-operations into well-named helper functions
2. Replace deep if/else chains with early returns (guard clauses)
3. Replace complex switch/if-elif chains with lookup tables or dispatch dicts
4. Reduce nesting by inverting conditions and returning early
5. Ensure all extracted functions have clear, descriptive names
Preserve all existing behavior exactly. Run tests after each refactor.""",
    retrieval_strategy="full_codebase",
    verification_command="radon cc . -n C || npx complexity-report src/",
    estimated_prs="1 per file",
  ),

  "naming-consistency": BuiltinAgent(
    name="naming-consistency",
    category="quality",
    description="Fix naming convention violations and inconsistencies across the codebase.",
    full_description="""Audits the codebase for naming convention violations -- mixed camelCase/snake_case,
inconsistent naming between similar concepts, single-letter variables outside loops. Fixes all
violations and updates all references.""",
    system_prompt="""You are a code consistency engineer enforcing naming conventions.
First, determine the dominant naming convention in the codebase (camelCase or snake_case).
Then fix violations:
1. Variables and functions: enforce the dominant convention
2. Constants: UPPER_SNAKE_CASE
3. Classes: PascalCase
4. Avoid abbreviations unless they are industry-standard (id, url, api, db)
5. No single-letter variables except loop counters (i, j, k)
6. Consistent naming for the same concept (user_id everywhere, not userId in some places)
Update ALL references when renaming. Run tests after each rename.""",
    retrieval_strategy="full_codebase",
    verification_command="pytest -q || npm test -- --passWithNoTests",
    estimated_prs="1 per file",
  ),

  "test-coverage": BuiltinAgent(
    name="test-coverage",
    category="testing",
    description="Write tests for all uncovered functions. Target: 80% line coverage.",
    full_description="""Analyzes the current test coverage report. For every function, class, and
branch below 80% coverage, writes tests that exercise the uncovered paths. Matches the
existing test framework, fixture patterns, and mocking approach exactly.""",
    system_prompt="""You are a test engineer writing comprehensive tests.
First, identify the test framework (pytest, jest, vitest, etc.) and existing patterns.
For each uncovered function:
1. Write tests covering the happy path
2. Write tests for each error/edge case
3. Match existing fixture patterns and import style exactly
4. Use the same mocking approach as existing tests
5. Ensure tests are deterministic (no time.now(), no random without seed)
Target: 80% line coverage, 70% branch coverage minimum.""",
    retrieval_strategy="test_files",
    verification_command="pytest --cov=. --cov-report=term-missing || npx jest --coverage",
    estimated_prs="1 per module",
  ),

  "integration-test-builder": BuiltinAgent(
    name="integration-test-builder",
    category="testing",
    description="Generate integration tests for all API endpoints.",
    full_description="""Generates integration tests for all API endpoints. Each test: sets up required
state, makes the API call with representative inputs, asserts the response shape and status
code, tears down state. Covers happy path, validation errors, auth failures, and edge cases.""",
    system_prompt="""You are a test engineer writing API integration tests.
For each API endpoint:
1. Write a test for the happy path with valid inputs
2. Write a test for missing required fields (should return 422 or 400)
3. Write a test for invalid auth (should return 401 or 403)
4. Write a test for not-found cases (should return 404)
5. Set up and tear down required database state per test
6. Use the existing test client and fixtures pattern
Assert both the response status code and the response body shape.""",
    retrieval_strategy="routes_only",
    verification_command="pytest tests/integration/ -v || npx jest --testPathPattern=integration",
    estimated_prs="1 per router",
  ),

  "mutation-tester": BuiltinAgent(
    name="mutation-tester",
    category="testing",
    description="Find weak tests using mutation testing. Rewrite tests that don't catch real bugs.",
    full_description="""Runs mutation testing to identify tests that pass even when the code they
test is broken. Rewrites those tests to actually catch the mutations they claim to cover.
Target: improve mutation score by at least 20 percentage points.""",
    system_prompt="""You are a test quality engineer strengthening weak tests.
A weak test passes even when the code it covers is broken.
For each weak test identified:
1. Understand what the test is supposed to verify
2. Add specific assertions that would catch the common mutations (off-by-one, wrong operator, missing condition)
3. Ensure the test would fail if the key logic were slightly changed
4. Do not make tests brittle -- strengthen assertions, not implementation coupling""",
    retrieval_strategy="test_files",
    verification_command="mutmut run || npx stryker run",
    estimated_prs="1 per test file",
  ),

  "api-documenter": BuiltinAgent(
    name="api-documenter",
    category="docs",
    description="Add complete OpenAPI documentation to all route handlers.",
    full_description="""Generates complete OpenAPI/Swagger documentation for every route handler --
request/response schemas, parameter descriptions, auth requirements, error codes, and examples.""",
    system_prompt="""You are a technical writer adding OpenAPI documentation to API routes.
For each route handler:
1. Add a summary (one line) and description (2-3 lines)
2. Document all path, query, and body parameters with types and descriptions
3. Document all response codes (200, 400, 401, 403, 404, 422, 500) with schemas
4. Add a request body example and response example
5. Mark auth-required endpoints with the appropriate security scheme
Follow the existing documentation style exactly.""",
    retrieval_strategy="routes_only",
    verification_command="python -c 'from main import app; assert app.openapi()' || true",
    estimated_prs="1 per router",
  ),

  "readme-architect": BuiltinAgent(
    name="readme-architect",
    category="docs",
    description="Rewrite the README from scratch based on the actual codebase.",
    full_description="""Rewrites the README from scratch based on the actual codebase -- not a template.
Covers: what the project does, installation, configuration, usage examples for every major feature,
API reference summary, architecture overview, contributing guide, license.""",
    system_prompt="""You are a technical writer creating a comprehensive README.
Read the actual codebase to understand what the project does -- do not guess.
Write a README that covers:
1. What it does (derived from the actual code, not assumptions)
2. Quick start (installation + first working example in < 5 steps)
3. Configuration (every env var with description and example)
4. Usage examples for each major feature
5. Architecture overview (which files do what)
6. Contributing guide
Keep it accurate, concise, and useful. No marketing language.""",
    retrieval_strategy="full_codebase",
    verification_command="test -f README.md",
    estimated_prs="1 total",
  ),

  "inline-documenter": BuiltinAgent(
    name="inline-documenter",
    category="docs",
    description="Add specific, accurate docstrings to every public function and class.",
    full_description="""Adds docstrings to every public function, class, and method that doesn't
have one. Docstrings describe what the function actually does, its parameters, return values,
side effects, and anything surprising about its behavior.""",
    system_prompt="""You are a technical writer adding docstrings to code.
For each public function, class, and method without a docstring:
1. Read the actual implementation to understand what it does
2. Write a docstring that explains: what it does, parameters, return value, side effects
3. Call out anything surprising: async behavior, mutations, exceptions raised
4. Be specific, not generic. "Validates and stores the user record" not "Does something with users"
5. Match the existing docstring style (Google, NumPy, or plain)
Do not add docstrings to private functions (prefixed with _).""",
    retrieval_strategy="full_codebase",
    verification_command="python -m pydocstyle . || true",
    estimated_prs="1 per file",
  ),

  "query-optimizer": BuiltinAgent(
    name="query-optimizer",
    category="performance",
    description="Fix N+1 queries, missing indexes, and blocking DB calls in async code.",
    full_description="""Finds N+1 queries, missing database indexes, unoptimized ORM patterns,
and queries running in loops. Adds appropriate indexes, rewrites N+1 queries to use joins
or bulk fetches, replaces synchronous DB calls in async contexts.""",
    system_prompt="""You are a database performance engineer.
Find and fix:
1. N+1 queries: loops that make one DB query per iteration -- replace with bulk fetch
2. Missing indexes: columns used in WHERE, JOIN, or ORDER BY clauses without an index
3. SELECT *: replace with explicit column lists
4. Synchronous DB calls in async functions: replace with async equivalents
5. Queries inside list comprehensions
For each fix, document the before/after query count in the PR.""",
    retrieval_strategy="full_codebase",
    verification_command="pytest -q || npm test -- --passWithNoTests",
    estimated_prs="1 per finding",
  ),

  "async-converter": BuiltinAgent(
    name="async-converter",
    category="performance",
    description="Convert blocking sync operations to async in async codebases.",
    full_description="""Identifies synchronous blocking operations in async codebases and converts
them to async equivalents. Targets: requests -> httpx, open() -> aiofiles, time.sleep() -> asyncio.sleep().""",
    system_prompt="""You are a Python async engineer removing blocking calls from async code.
Find and replace all blocking operations in async functions:
1. requests -> httpx (AsyncClient)
2. open() / file I/O -> aiofiles
3. time.sleep() -> asyncio.sleep()
4. subprocess.run() -> asyncio.create_subprocess_exec()
5. Any other blocking network or I/O call
Ensure the event loop is never blocked. Add 'await' to all async calls.
Run tests after each conversion to confirm behavior is preserved.""",
    retrieval_strategy="full_codebase",
    verification_command="python -m pytest -q || npm test -- --passWithNoTests",
    estimated_prs="1 per file",
  ),

  "ci-builder": BuiltinAgent(
    name="ci-builder",
    category="infra",
    description="Create or update a complete GitHub Actions CI/CD pipeline.",
    full_description="""Creates or updates a complete CI/CD pipeline -- GitHub Actions workflow that
runs: lint, type check, tests with coverage report, security scan, build. Adds Dependabot
configuration for automatic dependency updates.""",
    system_prompt="""You are a DevOps engineer setting up CI/CD.
Create or update .github/workflows/ci.yml to:
1. Trigger on push to main and pull_request
2. Run: lint, type check, tests with coverage, security scan
3. Use the correct language/framework detected from the codebase
4. Cache dependencies for speed
5. Report coverage to PR as a comment
Also create .github/dependabot.yml for weekly dependency updates.
The workflow must pass on the current codebase before submitting the PR.""",
    retrieval_strategy="full_codebase",
    verification_command="yamllint .github/workflows/ci.yml",
    estimated_prs="1 total",
  ),

  "docker-hardener": BuiltinAgent(
    name="docker-hardener",
    category="infra",
    description="Fix Dockerfile security and best practice violations. Minimize image size.",
    full_description="""Audits Dockerfiles for security and best practice violations -- running as root,
using 'latest' tags, missing health checks, oversized images. Fixes each issue and minimizes
the final image size using multi-stage builds.""",
    system_prompt="""You are a Docker security engineer hardening container configurations.
For each Dockerfile found:
1. Add non-root user and run as that user
2. Pin all base image versions (no 'latest' tags)
3. Add .dockerignore to exclude unnecessary files
4. Add HEALTHCHECK instruction
5. Use multi-stage builds to minimize final image size
6. Remove build tools from the final image
7. Run apt-get clean and remove package lists after installing
Verify 'docker build' succeeds after changes.""",
    retrieval_strategy="full_codebase",
    verification_command="docker build -t nimbus-test . && docker run --rm nimbus-test echo ok",
    estimated_prs="1 per Dockerfile",
  ),

  "feature-flags": BuiltinAgent(
    name="feature-flags",
    category="architecture",
    description="Wrap recent features in feature flags for safe rollout and instant rollback.",
    full_description="""Wraps every feature added in the last 30 days of commits in a feature flag.
Uses the existing flag system if one exists, or adds a simple env-var based system.
Adds flag cleanup TODOs with a 90-day expiry.""",
    system_prompt="""You are a release engineer adding feature flags.
First, check if a feature flag system exists (LaunchDarkly, Unleash, env vars, etc.).
If not, create a simple one: flags.py / flags.ts that reads from env vars.
For each new feature (last 30 days of commits):
1. Wrap the feature entry point in a flag check
2. Name the flag: FEATURE_<FEATURE_NAME>_ENABLED
3. Default to True in production (existing behavior), False in tests
4. Add a comment: # TODO: remove flag by <date 90 days from now>
5. Add the flag to .env.example with description
Ensure existing behavior is preserved when the flag is enabled.""",
    retrieval_strategy="changed_files",
    verification_command="pytest -q || npm test -- --passWithNoTests",
    estimated_prs="1 total",
  ),

  "observability-agent": BuiltinAgent(
    name="observability-agent",
    category="architecture",
    description="Add structured logging, metrics, and tracing to the service layer.",
    full_description="""Adds structured logging, metrics, and tracing to the entire service layer --
log entry/exit of every service function with timing, emit a metric for every external call
with latency and success/failure, add trace context propagation through async call chains.""",
    system_prompt="""You are an observability engineer adding monitoring to a service.
For every service function (not routes, not models -- service layer):
1. Add structured logging at entry: logger.info("starting X", extra={params})
2. Add timing: record how long the function takes
3. Add structured logging at exit: logger.info("completed X", extra={duration, result_summary})
4. For external calls (DB, API, cache): log latency and success/failure as a metric
5. If OpenTelemetry is available, add span context
Use the existing logger configuration. Do not add logging to utility functions -- only service functions.""",
    retrieval_strategy="full_codebase",
    verification_command="python -c 'import logging; logging.basicConfig(); print(\"ok\")' || true",
    estimated_prs="1 per service file",
  ),
}


def get_agent(name: str) -> Optional[BuiltinAgent]:
    return BUILTIN_AGENTS.get(name)


def list_agents(category: str = None) -> list[BuiltinAgent]:
    agents = list(BUILTIN_AGENTS.values())
    if category:
        agents = [a for a in agents if a.category == category]
    return agents


CATEGORIES = ["security", "quality", "testing", "docs", "performance", "infra", "architecture"]
