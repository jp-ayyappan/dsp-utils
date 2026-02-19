# Test Framework Plan (Draft)

## Goals
- Provide repeatable, minimal-friction tests for scripts and assets.
- Keep local runs fast; allow optional integration tests against real services.
- Avoid adding heavy tooling unless it materially improves confidence.

## Scope Options
- Keycloak CLI (`keycloak/keycloak_admin.py`): unit and smoke tests.
- grpcui launchers (`grpcui/runGRPCUI.sh`, `grpcui/runGRPCUI.ps1`): argument parsing and dry-run behavior.
- Postman collection (`postman/virtru-data-security-platform-grpc-apis.postman_collection.json`): schema validation and optional smoke runs.
- Internal scripts (`internal/test_http_support.sh`): basic usage and error handling.

## Proposed Stack
- Python: `pytest` for unit tests, `pytest-dotenv` optional for env loading.
- Shell: `bats-core` for bash script tests (or a lightweight `bash` test harness).
- Postman: `newman` for CLI-driven smoke tests (optional, gated).
- CI: GitHub Actions with matrix to run unit tests by default and integration tests on-demand.

## Test Levels
- Unit: pure logic (no network). Use mocks for Keycloak client.
- Smoke: CLI runs with `--dry-run` or mocked endpoints.
- Integration (optional): runs against real Keycloak / platform URLs; require env vars.

## Directory Layout
- `tests/python/` for pytest suites.
- `tests/shell/` for bats or bash tests.
- `tests/postman/` for newman config and sample env files.

## Environment Variables
- `KEYCLOAK_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_USERNAME`, `KEYCLOAK_PASSWORD` for integration.
- `PLATFORM_URL`, `AUTH_URL`, `CLIENT_ID`, `USERNAME` for grpcui smoke tests.
- `POSTMAN_ENV_FILE` or `BASE_URL` for newman.

## CI Sketch
- Lint: optional `ruff` for Python.
- Unit tests: always on PR.
- Integration tests: manual trigger or scheduled, with secrets.

## Open Questions
- Should integration tests run by default or be gated?
- Are we OK adding Node as a toolchain for `newman`?
- Should Windows PowerShell tests run in CI?
