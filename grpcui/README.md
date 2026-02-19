# gRPC UI Launcher Scripts

Automated scripts for launching [grpcui](https://github.com/fullstorydev/grpcui) with OAuth/OpenID Connect authentication. These scripts handle token management automatically, making it easy to test authenticated gRPC services.

## What These Scripts Do

1. **Authenticate** - Fetch OAuth access tokens from your auth server (e.g., Keycloak)
2. **Launch grpcui** - Start the interactive web UI with the token in the Authorization header
3. **Diagnose Issues** - Provide helpful error messages and connectivity checks

## Features

- ✓ Auto-detects Keycloak version (old `/auth/realms` vs new `/realms` path structure)
- ✓ Pre-flight connectivity checks with clear error messages
- ✓ Debug mode for troubleshooting
- ✓ Supports separate auth and gRPC servers
- ✓ Flexible configuration via command-line options
- ✓ Secure password input (hidden)

## Prerequisites

### Both Scripts Require

**grpcui** - Interactive web UI for gRPC services
```bash
# Via Go
go install github.com/fullstorydev/grpcui/cmd/grpcui@latest

# Via Homebrew (macOS/Linux)
brew install grpcui

# Via Scoop (Windows)
scoop install grpcui
```

### Bash Script (`runGRPCUI.sh`) Additional Requirements

- **curl** - Command-line HTTP client (usually pre-installed)
- **jq** - Command-line JSON processor
  ```bash
  # macOS
  brew install jq

  # Linux
  sudo apt-get install jq
  ```

### PowerShell Script (`runGRPCUI.ps1`)

- **PowerShell 5.1+** (pre-installed on Windows 10+)
- No additional dependencies required

## Quick Start

### Local Development (Self-Signed Certificates)

**Bash:**
```bash
./runGRPCUI.sh platform.acme.com --insecure -a 8443 -p 8080
```

**PowerShell:**
```powershell
.\runGRPCUI.ps1 -PlatformUrl "platform.acme.com" -Insecure -AuthPort 8443 -GrpcPort 8080
```

### Production Environment

**Bash:**
```bash
./runGRPCUI.sh api.example.com --auth-url auth.example.com
```

**PowerShell:**
```powershell
.\runGRPCUI.ps1 -PlatformUrl "api.example.com" -AuthUrl "auth.example.com"
```

## Usage

### Bash Script Options

```bash
./runGRPCUI.sh <platform_url> [options]

Options:
  -p, --port PORT           gRPC service port (default: 443)
  --token-url URL          Full token endpoint URL (skips auto-detection)
  --auth-url URL           Auth server URL (if different from platform)
  -a, --auth-port PORT     Auth service port (default: 443)
  --auth-path PATH         Auth endpoint path (auto-detected: /realms or /auth/realms)
  -r, --realm REALM        Auth realm (default: opentdf)
  -c, --client-id ID       OAuth client ID (default: public-client)
  -u, --username USER      Username (will prompt if not provided)
  -i, --insecure          Allow insecure SSL connections
  -t, --timeout SEC        Request timeout in seconds (default: 10)
  --debug                  Show debug output
  --dry-run               Show what would be executed without running
  -h, --help              Show help message
```

### PowerShell Script Parameters

```powershell
.\runGRPCUI.ps1 -PlatformUrl <url> [parameters]

Parameters:
  -PlatformUrl             Base URL of the platform (required)
  -GrpcPort                gRPC service port (default: 443)
  -TokenUrl                Full token endpoint URL
  -AuthUrl                 Auth server URL (if different from platform)
  -AuthPort                Auth service port (default: 443)
  -AuthPath                Auth endpoint path (auto-detected)
  -Realm                   Auth realm (default: opentdf)
  -ClientId                OAuth client ID (default: public-client)
  -Username                Username (will prompt if not provided)
  -Insecure               Allow insecure SSL connections
  -Timeout                 Request timeout in seconds (default: 10)
  -Debug                   Show debug output
  -DryRun                  Show what would be executed without running
```

## Common Scenarios

### 1. Platform Local Development

**Bash:**
```bash
./runGRPCUI.sh platform.acme.com \
  --insecure \
  -a 8443 \
  -p 8080 \
  -u your-username
```

**PowerShell:**
```powershell
.\runGRPCUI.ps1 `
  -PlatformUrl "platform.acme.com" `
  -Insecure `
  -AuthPort 8443 `
  -GrpcPort 8080 `
  -Username "your-username"
```

### 2. Separate Auth and gRPC Servers

**Bash:**
```bash
./runGRPCUI.sh api.example.com \
  --auth-url keycloak.example.com \
  -r my-realm \
  -p 9090
```

**PowerShell:**
```powershell
.\runGRPCUI.ps1 `
  -PlatformUrl "api.example.com" `
  -AuthUrl "keycloak.example.com" `
  -Realm "my-realm" `
  -GrpcPort 9090
```

### 3. Explicit Token URL (Bypass Auto-Detection)

**Bash:**
```bash
./runGRPCUI.sh platform.acme.com \
  --token-url "https://platform.acme.com:8443/auth/realms/opentdf/protocol/openid-connect/token" \
  -p 8080 \
  --insecure
```

**PowerShell:**
```powershell
.\runGRPCUI.ps1 `
  -PlatformUrl "platform.acme.com" `
  -TokenUrl "https://platform.acme.com:8443/auth/realms/opentdf/protocol/openid-connect/token" `
  -GrpcPort 8080 `
  -Insecure
```

### 4. Debug Mode (Troubleshooting)

**Bash:**
```bash
./runGRPCUI.sh platform.acme.com --debug --insecure
```

**PowerShell:**
```powershell
.\runGRPCUI.ps1 -PlatformUrl "platform.acme.com" -Debug -Insecure
```

## Keycloak Version Auto-Detection

The scripts automatically detect the correct Keycloak path structure:

- **Local/Localhost URLs** → Uses `/auth/realms` (Keycloak < 17)
- **Other URLs** → Uses `/realms` (Keycloak 17+)

You can override this with `--auth-path` (bash) or `-AuthPath` (PowerShell).

## Troubleshooting

### "Connection refused" Error

**Problem:** No server is listening on the specified port.

**Solutions:**
- Check if the auth server is running
- Verify the port with `-a PORT` (bash) or `-AuthPort PORT` (PowerShell)
- For local development, common auth ports are 8443 or 8080

### "SSL certificate verification failed"

**Problem:** Self-signed or invalid SSL certificate.

**Solution:**
- Use `--insecure` (bash) or `-Insecure` (PowerShell) for self-signed certificates
- **Note:** Only use this for local development, never in production

### "Cannot connect to gRPC server"

**Problem:** Wrong gRPC port or server not running.

**Solutions:**
- Verify the gRPC port with `-p PORT` (bash) or `-GrpcPort PORT` (PowerShell)
- Check if the gRPC server is running
- For local platform runs, common gRPC ports are 8080 or 8443

### "Connection timed out"

**Problem:** Server is slow or not responding.

**Solutions:**
- Increase timeout: `-t SECONDS` (bash) or `-Timeout SECONDS` (PowerShell)
- Check network connectivity
- Verify firewall settings

### "Invalid user credentials"

**Problem:** Wrong username or password.

**Solutions:**
- Verify credentials with your Keycloak admin
- Check if the user exists in the specified realm
- Ensure the realm name is correct with `-r REALM` (bash) or `-Realm REALM` (PowerShell)

### Getting More Information

Use **debug mode** to see detailed connection information:

**Bash:**
```bash
./runGRPCUI.sh platform.acme.com --debug --insecure
```

**PowerShell:**
```powershell
.\runGRPCUI.ps1 -PlatformUrl "platform.acme.com" -Debug -Insecure
```

## Configuration Defaults

| Setting | Default Value | Description |
|---------|---------------|-------------|
| gRPC Port | 443 | Port where gRPC service runs |
| Auth Port | 443 | Port where auth server runs |
| Auth Path | `/realms` or `/auth/realms` | Auto-detected based on URL |
| Realm | `opentdf` | OAuth realm name |
| Client ID | `public-client` | OAuth client identifier |
| Timeout | 10 seconds | Request timeout |

## Environment-Specific Examples

### Platform Production (Green)

**Bash:**
```bash
./runGRPCUI.sh platform.acme.com \
  --auth-url keycloak.acme.com \
  -r acme-realm
```

**PowerShell:**
```powershell
.\runGRPCUI.ps1 `
  -PlatformUrl "platform.acme.com" `
  -AuthUrl "keycloak.acme.com" `
  -Realm "acme-realm"
```

### Local Development

**Bash:**
```bash
./runGRPCUI.sh platform.acme.com \
  --insecure \
  -a 8443 \
  -p 8080
```

**PowerShell:**
```powershell
.\runGRPCUI.ps1 `
  -PlatformUrl "platform.acme.com" `
  -Insecure `
  -AuthPort 8443 `
  -GrpcPort 8080
```

## Tips

1. **Save Common Commands**: Create aliases or shortcuts for frequently used configurations
2. **Use Debug Mode**: When troubleshooting, always start with `--debug` or `-Debug`
3. **Specify Username**: Add `-u username` or `-Username "username"` to skip the prompt
4. **Dry Run**: Test your configuration with `--dry-run` or `-DryRun` before executing

## Additional Resources

- [grpcui GitHub](https://github.com/fullstorydev/grpcui)
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OpenID Connect Specification](https://openid.net/connect/)

## Version

Current Version: **2.0**

Enhanced by Claude Code
