# Repository Guidelines

## Project Structure & Module Organization
- `keycloak/` holds the Python Keycloak admin CLI (`keycloak_admin.py`) and its dependencies (`requirements.txt`).
- `grpcui/` contains launcher scripts for gRPC UI: `runGRPCUI.sh` (bash) and `runGRPCUI.ps1` (PowerShell).
- `postman/` contains the Postman collection (`virtru-data-security-platform-grpc-apis.postman_collection.json`) and documentation. Internal utilities live in `internal/`.
- `README.md` at repo root summarizes the tools and links to each module’s guide.

## Build, Test, and Development Commands
- `python3 -m venv venv && source venv/bin/activate` (in `keycloak/`) creates a local venv for the Keycloak tool.
- `pip install -r keycloak/requirements.txt` installs Keycloak CLI dependencies.
- `python keycloak/keycloak_admin.py list clients` runs the CLI (see `keycloak/README.md` for full verbs).
- `./grpcui/runGRPCUI.sh <platform_url> --insecure -a 8443 -p 8080` launches grpcui with auth (bash).
- `./grpcui/runGRPCUI.ps1 -PlatformUrl <url> -Insecure -AuthPort 8443 -GrpcPort 8080` same for PowerShell.
- `./internal/test_http_support.sh <base_url> <bearer_token>` checks which services are HTTP-enabled (internal use).

## Coding Style & Naming Conventions
- Python uses 4-space indentation, snake_case functions/variables, and docstrings for major functions.
- Scripts are small, self-contained, and favor clear CLI flags (see `grpcui/README.md`).
- No formatter or linter is enforced in-repo; keep changes consistent with existing files.

## Testing Guidelines
- No unit test framework is currently configured.
- Use `internal/test_http_support.sh` to validate HTTP endpoints before updating the Postman collection.
- When changing CLI behavior, update the relevant README examples in the same PR.

## Commit & Pull Request Guidelines
- Commit messages are short, sentence-case summaries (e.g., “Add redirect URI management commands”).
- PRs should include a clear description of the user-facing change, updated docs for any new command/flag/collection change, and notes on manual validation (e.g., Postman run or grpcui invocation).

## Security & Configuration Tips
- Store Keycloak credentials in `keycloak/.env` (gitignored). Never commit secrets.
- If providing sample URLs or realms, use placeholders like `example.com` or `acme-realm`.

## Legal & Trademarks

All trademarks and registered trademarks are the property of their respective owners. No affiliation, sponsorship, or endorsement is implied, and no permissions have been sought for trademark use. Scripts and documents in this repository are provided “as is,” without warranties or guarantees of any kind. Upstream services may change; while reasonable efforts may be made to keep interfaces up to date, compatibility is not guaranteed.
