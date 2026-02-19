#!/bin/bash

################################################################################
# grpcui Launcher with OAuth Authentication
################################################################################
#
# DESCRIPTION:
#   This script automates the process of authenticating with an OAuth/OpenID
#   Connect server (such as Keycloak) and launching grpcui with the obtained
#   access token. It's designed to make testing authenticated gRPC services
#   easier by handling token management automatically.
#
# WHAT IT DOES:
#   1. Prompts for username and password (or accepts via parameters)
#   2. Fetches an OAuth access token from your auth server
#   3. Launches grpcui with the token in the Authorization header
#   4. Provides helpful error messages and connection diagnostics
#
# PREREQUISITES:
#   This script requires the following tools to be installed:
#
#   • grpcui - Interactive web UI for gRPC services
#     Install: go install github.com/fullstorydev/grpcui/cmd/grpcui@latest
#     Or via Homebrew: brew install grpcui
#     GitHub: https://github.com/fullstorydev/grpcui
#
#   • curl - Command-line HTTP client (usually pre-installed)
#     Install: brew install curl  (if needed)
#
#   • jq - Command-line JSON processor
#     Install: brew install jq
#     Or: sudo apt-get install jq  (Linux)
#     Website: https://stedolan.github.io/jq/
#
# QUICK START:
#   # For local development with self-signed certs
#   ./runGRPCUI.sh platform.acme.com --insecure -a 8443 -p 8080
#
#   # For production with separate auth server
#   ./runGRPCUI.sh api.example.com --auth-url auth.example.com
#
#   # See all options
#   ./runGRPCUI.sh --help
#
# FEATURES:
#   • Auto-detects Keycloak version (old vs new path structure)
#   • Pre-flight connectivity checks with clear error messages
#   • Debug mode for troubleshooting
#   • Supports separate auth and gRPC servers
#   • Flexible configuration via command-line options
#
# AUTHOR: Enhanced by Claude Code
# VERSION: 2.0
#
################################################################################

set -euo pipefail

# --- Configuration ---
DEFAULT_AUTH_REALM='opentdf'
DEFAULT_CLIENT_ID='public-client'
DEFAULT_AUTH_PATH='/realms'  # Changed from /auth/realms for Keycloak 17+
DEFAULT_TIMEOUT=10

# --- Color codes for output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Helper functions ---
print_error() {
    echo -e "${RED}Error: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

show_help() {
    cat << EOF
Usage: $(basename "$0") <platform_url> [options]

Launch grpcui with OAuth authentication for gRPC services.

Arguments:
    platform_url          Base URL of the platform (e.g., platform.acme.com)

Options:
    -p, --port PORT       gRPC service port (default: 443)
    --token-url URL       Full token endpoint URL (skips URL construction)
    --auth-url URL        Auth server URL (overrides platform_url for auth)
    -a, --auth-port PORT  Auth service port (default: 443, ignored if --token-url is set)
    --auth-path PATH      Auth endpoint path (auto-detected or default: /realms)
                          Auto-detects: local URLs use /auth/realms, others use /realms
    -r, --realm REALM     Auth realm (default: $DEFAULT_AUTH_REALM, ignored if --token-url is set)
    -c, --client-id ID    OAuth client ID (default: $DEFAULT_CLIENT_ID)
    -u, --username USER   Username (will prompt if not provided)
    -i, --insecure        Allow insecure SSL connections
    -t, --timeout SEC     Request timeout in seconds (default: $DEFAULT_TIMEOUT)
    --debug               Show debug output including curl commands
    --dry-run             Show what would be executed without running
    -h, --help            Show this help message

Examples:
    # Basic usage - auto-detects Keycloak version for local URLs
    $(basename "$0") platform.acme.com --insecure -a 8443 -p 8080

    # Production with separate auth server
    $(basename "$0") api.example.com --auth-url keycloak.example.com -r my-realm

    # Full token URL (most explicit)
    $(basename "$0") platform.acme.com \
      --token-url https://platform.acme.com:8443/auth/realms/opentdf/protocol/openid-connect/token \
      -p 8080 --insecure

    # Override auto-detection with explicit auth path
    $(basename "$0") prod.example.com --auth-path /auth/realms

    # Specify username to avoid prompt
    $(basename "$0") platform.acme.com -u your-username --insecure

    # Debug mode to see what's happening
    $(basename "$0") platform.acme.com --debug --insecure

EOF
}

# --- Parse command line arguments ---
PLATFORM_URL=""
TOKEN_URL=""
AUTH_URL=""
AUTH_PATH=""
GRPC_PORT=443
AUTH_PORT=443
REALM="$DEFAULT_AUTH_REALM"
CLIENT_ID="$DEFAULT_CLIENT_ID"
USERNAME=""
PASSWORD=""
INSECURE=false
TIMEOUT="$DEFAULT_TIMEOUT"
DEBUG=false
DRY_RUN=false

if [[ $# -eq 0 ]]; then
    show_help
    exit 1
fi

PLATFORM_URL="$1"
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            GRPC_PORT="$2"
            shift 2
            ;;
        --token-url)
            TOKEN_URL="$2"
            shift 2
            ;;
        --auth-url)
            AUTH_URL="$2"
            shift 2
            ;;
        -a|--auth-port)
            AUTH_PORT="$2"
            shift 2
            ;;
        --auth-path)
            AUTH_PATH="$2"
            shift 2
            ;;
        -r|--realm)
            REALM="$2"
            shift 2
            ;;
        -c|--client-id)
            CLIENT_ID="$2"
            shift 2
            ;;
        -u|--username)
            USERNAME="$2"
            shift 2
            ;;
        -i|--insecure)
            INSECURE=true
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# --- Validate platform URL ---
if [[ -z "$PLATFORM_URL" ]]; then
    print_error "Platform URL is required"
    show_help
    exit 1
fi

# Remove protocol if provided
PLATFORM_URL="${PLATFORM_URL#https://}"
PLATFORM_URL="${PLATFORM_URL#http://}"
PLATFORM_URL="${PLATFORM_URL%/}"

# --- Build URLs ---
GRPCUI_TARGET="${PLATFORM_URL}:${GRPC_PORT}"

# Build token URL
if [[ -n "$TOKEN_URL" ]]; then
    # Full token URL provided, use as-is
    print_info "Using provided token URL"
else
    # Auto-detect auth path if not specified
    if [[ -z "$AUTH_PATH" ]]; then
        # Check if URL contains "local" or "localhost" - use old Keycloak path
        if [[ "$PLATFORM_URL" =~ local ]] || [[ "$AUTH_URL" =~ local ]] || \
           [[ "$PLATFORM_URL" =~ localhost ]] || [[ "$AUTH_URL" =~ localhost ]]; then
            AUTH_PATH="/auth/realms"
            if [[ "$DEBUG" == true ]]; then
                print_info "Auto-detected local environment, using Keycloak < 17 path: /auth/realms"
            fi
        else
            AUTH_PATH="$DEFAULT_AUTH_PATH"
            if [[ "$DEBUG" == true ]]; then
                print_info "Using Keycloak 17+ path: $DEFAULT_AUTH_PATH"
            fi
        fi
    fi

    # Clean auth path (remove leading/trailing slashes, we'll add them back)
    AUTH_PATH="${AUTH_PATH#/}"
    AUTH_PATH="${AUTH_PATH%/}"

    # Build auth URL
    if [[ -n "$AUTH_URL" ]]; then
        # Custom auth URL provided - clean it up
        AUTH_URL="${AUTH_URL#https://}"
        AUTH_URL="${AUTH_URL#http://}"
        AUTH_URL="${AUTH_URL%/}"

        # Check if it already has a port
        if [[ "$AUTH_URL" =~ :[0-9]+$ ]]; then
            # Port already specified, use as-is
            TOKEN_URL="https://${AUTH_URL}/${AUTH_PATH}/${REALM}/protocol/openid-connect/token"
        else
            # Add port
            TOKEN_URL="https://${AUTH_URL}:${AUTH_PORT}/${AUTH_PATH}/${REALM}/protocol/openid-connect/token"
        fi
    else
        # Use platform URL for auth
        TOKEN_URL="https://${PLATFORM_URL}:${AUTH_PORT}/${AUTH_PATH}/${REALM}/protocol/openid-connect/token"
    fi
fi

# --- Check dependencies ---
for cmd in curl jq grpcui; do
    if ! command -v "$cmd" &> /dev/null; then
        print_error "Required command '$cmd' not found. Please install it first."
        exit 1
    fi
done

# --- Prompt for credentials ---
if [[ -z "$USERNAME" ]]; then
    read -p "Username: " USERNAME
fi

if [[ -z "$USERNAME" ]]; then
    print_error "Username is required"
    exit 1
fi

if [[ -z "$PASSWORD" ]]; then
    read -s -p "Password: " PASSWORD
    echo
fi

if [[ -z "$PASSWORD" ]]; then
    print_error "Password is required"
    exit 1
fi

# --- Debug output ---
if [[ "$DEBUG" == true ]]; then
    print_info "Configuration:"
    echo "  Platform URL: $PLATFORM_URL"
    if [[ -n "$AUTH_URL" ]]; then
        echo "  Auth URL: $AUTH_URL"
    fi
    if [[ -n "$AUTH_PATH" ]]; then
        echo "  Auth Path: /$AUTH_PATH"
    fi
    echo "  Token URL: $TOKEN_URL"
    echo "  gRPC Target: $GRPCUI_TARGET"
    echo "  Client ID: $CLIENT_ID"
    echo "  Username: $USERNAME"
    echo "  Realm: $REALM"
    echo "  Timeout: ${TIMEOUT}s"
    echo "  Insecure: $INSECURE"
fi

# --- Build curl command ---
CURL_CMD=(
    curl
    --silent
    --show-error
    --location
    --max-time "$TIMEOUT"
    --header 'Content-Type: application/x-www-form-urlencoded'
    --data-urlencode 'grant_type=password'
    --data-urlencode "client_id=$CLIENT_ID"
    --data-urlencode "username=$USERNAME"
    --data-urlencode "password=$PASSWORD"
)

if [[ "$INSECURE" == true ]]; then
    CURL_CMD+=(--insecure)
fi

CURL_CMD+=("$TOKEN_URL")

# --- Dry run mode ---
if [[ "$DRY_RUN" == true ]]; then
    print_info "Would execute:"
    echo "  ${CURL_CMD[*]} | jq -r .access_token"
    echo "  grpcui -H \"Authorization: Bearer [ACCESS_TOKEN]\" \"$GRPCUI_TARGET\""
    exit 0
fi

# --- Fetch access token ---
print_info "Fetching access token from $PLATFORM_URL..."

# Quick connectivity check
if [[ "$DEBUG" == true ]]; then
    print_info "Testing connectivity to auth server..."
fi

# Extract host and port from TOKEN_URL for connectivity check
if [[ "$TOKEN_URL" =~ https://([^:/]+)(:([0-9]+))? ]]; then
    AUTH_HOST="${BASH_REMATCH[1]}"
    AUTH_PORT_CHECK="${BASH_REMATCH[3]:-443}"

    # Quick connection test with 3 second timeout
    if ! timeout 3 bash -c "cat < /dev/null > /dev/tcp/$AUTH_HOST/$AUTH_PORT_CHECK" 2>/dev/null; then
        print_error "Cannot connect to auth server at $AUTH_HOST:$AUTH_PORT_CHECK"
        print_warning "Possible issues:"
        echo "  • No server is running on port $AUTH_PORT_CHECK"
        echo "  • Firewall is blocking the connection"
        echo "  • Wrong hostname or port number"
        echo ""
        echo "  Did you mean to specify a different port? Use -a PORT or --auth-port PORT"
        exit 1
    fi

    if [[ "$DEBUG" == true ]]; then
        print_success "Successfully connected to $AUTH_HOST:$AUTH_PORT_CHECK"
    fi
fi

if [[ "$DEBUG" == true ]]; then
    print_info "Executing: ${CURL_CMD[*]}"
fi

TOKEN_RESPONSE=$("${CURL_CMD[@]}" 2>&1)
CURL_EXIT_CODE=$?

if [[ "$DEBUG" == true ]]; then
    print_info "curl exit code: $CURL_EXIT_CODE"
    print_info "Response received (first 500 chars):"
    echo "${TOKEN_RESPONSE:0:500}"
    echo ""
fi

if [[ $CURL_EXIT_CODE -ne 0 ]]; then
    print_error "Failed to connect to auth server (curl exit code: $CURL_EXIT_CODE)"

    # Analyze the specific error
    if [[ "$TOKEN_RESPONSE" =~ "Connection refused" ]]; then
        print_error "Connection refused - no server is listening on this port"
        if [[ -n "$AUTH_URL" ]]; then
            echo "  Auth server: $AUTH_URL:$AUTH_PORT"
        else
            echo "  Auth server: $PLATFORM_URL:$AUTH_PORT"
        fi
        print_warning "Check if the auth server is running and the port is correct"
        echo "  Use -a PORT or --auth-port PORT to specify a different port"
    elif [[ "$TOKEN_RESPONSE" =~ "timed out" ]] || [[ "$TOKEN_RESPONSE" =~ "Timeout" ]] || [[ $CURL_EXIT_CODE -eq 28 ]]; then
        print_error "Connection timed out after ${TIMEOUT}s"
        print_warning "The server is not responding. Possible causes:"
        echo "  • Server is not running"
        echo "  • Server is too slow to respond"
        echo "  • Network connectivity issues"
        echo "  • Firewall blocking the connection"
        echo ""
        echo "  Try increasing timeout: -t SECONDS (current: ${TIMEOUT}s)"
    elif [[ "$TOKEN_RESPONSE" =~ "Could not resolve host" ]]; then
        print_error "DNS lookup failed - hostname cannot be resolved"
        if [[ -n "$AUTH_URL" ]]; then
            echo "  Invalid hostname: $AUTH_URL"
        else
            echo "  Invalid hostname: $PLATFORM_URL"
        fi
    elif [[ "$TOKEN_RESPONSE" =~ "SSL" ]] || [[ "$TOKEN_RESPONSE" =~ "certificate" ]]; then
        print_error "SSL certificate verification failed"
        echo "$TOKEN_RESPONSE"
        print_warning "For self-signed certificates, use: --insecure"
    else
        # Generic error
        echo "$TOKEN_RESPONSE"
    fi

    # Hint for local development
    if [[ "$PLATFORM_URL" =~ "local" ]] || [[ "$AUTH_URL" =~ "local" ]]; then
        echo ""
        print_info "Tip: For local development, you might need: --insecure -a 8443"
    fi

    exit 1
fi

# Check if response is valid JSON
if ! echo "$TOKEN_RESPONSE" | jq empty 2>/dev/null; then
    print_error "Received invalid JSON response from auth server"
    echo "Raw response:"
    echo "$TOKEN_RESPONSE"
    exit 1
fi

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token // empty' 2>/dev/null)

if [[ -z "$ACCESS_TOKEN" ]]; then
    print_error "Failed to retrieve access token"

    # Try to extract error information
    ERROR_TYPE=$(echo "$TOKEN_RESPONSE" | jq -r '.error // empty' 2>/dev/null)
    ERROR_DESC=$(echo "$TOKEN_RESPONSE" | jq -r '.error_description // empty' 2>/dev/null)

    if [[ -n "$ERROR_TYPE" ]]; then
        print_error "Error type: $ERROR_TYPE"
    fi

    if [[ -n "$ERROR_DESC" ]]; then
        print_error "Error: $ERROR_DESC"

        # Provide helpful hints based on error type
        if [[ "$ERROR_DESC" =~ "Invalid user credentials" ]] || [[ "$ERROR_DESC" =~ "invalid_grant" ]]; then
            print_warning "Authentication failed. Please check your username and password."
        fi
    else
        # No error description, show raw response
        print_warning "No error description provided by server. Raw response:"
        echo "$TOKEN_RESPONSE" | jq . 2>/dev/null || echo "$TOKEN_RESPONSE"
    fi

    exit 1
fi

print_success "Access token retrieved successfully"

# --- Launch grpcui ---
print_info "Launching grpcui for $GRPCUI_TARGET..."

# Check gRPC target connectivity
if [[ "$GRPCUI_TARGET" =~ ^([^:]+):([0-9]+)$ ]]; then
    GRPC_HOST="${BASH_REMATCH[1]}"
    GRPC_PORT_CHECK="${BASH_REMATCH[2]}"

    if [[ "$DEBUG" == true ]]; then
        print_info "Testing connectivity to gRPC server..."
    fi

    if ! timeout 3 bash -c "cat < /dev/null > /dev/tcp/$GRPC_HOST/$GRPC_PORT_CHECK" 2>/dev/null; then
        print_warning "Cannot connect to gRPC server at $GRPC_HOST:$GRPC_PORT_CHECK"
        print_warning "The server might not be running on port $GRPC_PORT_CHECK"
        echo "  Use -p PORT or --port PORT to specify the correct gRPC port"
        echo ""
        print_info "Attempting to launch grpcui anyway (it may provide its own error message)..."
    elif [[ "$DEBUG" == true ]]; then
        print_success "Successfully connected to $GRPC_HOST:$GRPC_PORT_CHECK"
    fi
fi

if [[ "$DEBUG" == true ]]; then
    echo "Token (first 20 chars): ${ACCESS_TOKEN:0:20}..."
fi

grpcui -H "Authorization: Bearer $ACCESS_TOKEN" "$GRPCUI_TARGET"

print_success "grpcui session ended"
