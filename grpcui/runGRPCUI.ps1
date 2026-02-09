<#
################################################################################
# grpcui Launcher with OAuth Authentication (PowerShell Version)
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
#     Or via Scoop: scoop install grpcui
#     GitHub: https://github.com/fullstorydev/grpcui
#
#   • PowerShell 5.1+ (pre-installed on Windows 10+)
#
# QUICK START:
#   # For local development with self-signed certs
#   .\runGRPCUI.ps1 -PlatformUrl "local-dsp.virtru.com" -Insecure -AuthPort 8443 -GrpcPort 8080
#
#   # For production with separate auth server
#   .\runGRPCUI.ps1 -PlatformUrl "api.example.com" -AuthUrl "auth.example.com"
#
#   # See all options
#   Get-Help .\runGRPCUI.ps1 -Detailed
#
# FEATURES:
#   • Auto-detects Keycloak version (old vs new path structure)
#   • Pre-flight connectivity checks with clear error messages
#   • Debug mode for troubleshooting
#   • Supports separate auth and gRPC servers
#   • Secure password input (hidden)
#   • Flexible configuration via parameters
#
# AUTHOR: Enhanced by Claude Code
# VERSION: 2.0
#
################################################################################

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0, HelpMessage="Base URL of the platform (e.g., local-dsp.virtru.com)")]
    [string]$PlatformUrl,

    [Parameter(HelpMessage="gRPC service port (default: 443)")]
    [int]$GrpcPort = 443,

    [Parameter(HelpMessage="Full token endpoint URL (skips URL construction)")]
    [string]$TokenUrl,

    [Parameter(HelpMessage="Auth server URL (overrides platform URL for auth)")]
    [string]$AuthUrl,

    [Parameter(HelpMessage="Auth service port (default: 443)")]
    [int]$AuthPort = 443,

    [Parameter(HelpMessage="Auth endpoint path (auto-detected or default: /realms)")]
    [string]$AuthPath,

    [Parameter(HelpMessage="Auth realm (default: opentdf)")]
    [string]$Realm = "opentdf",

    [Parameter(HelpMessage="OAuth client ID (default: dsp-outlook-auth)")]
    [string]$ClientId = "dsp-outlook-auth",

    [Parameter(HelpMessage="Username (will prompt if not provided)")]
    [string]$Username,

    [Parameter(HelpMessage="Allow insecure SSL connections")]
    [switch]$Insecure,

    [Parameter(HelpMessage="Request timeout in seconds (default: 10)")]
    [int]$Timeout = 10,

    [Parameter(HelpMessage="Show debug output including request details")]
    [switch]$Debug,

    [Parameter(HelpMessage="Show what would be executed without running")]
    [switch]$DryRun
)

# Configuration
$DEFAULT_AUTH_PATH = "/realms"

# Disable certificate validation if -Insecure is specified
if ($Insecure) {
    if ($PSVersionTable.PSVersion.Major -ge 6) {
        # PowerShell Core 6+
        $PSDefaultParameterValues['Invoke-RestMethod:SkipCertificateCheck'] = $true
    } else {
        # Windows PowerShell 5.1
        add-type @"
            using System.Net;
            using System.Security.Cryptography.X509Certificates;
            public class TrustAllCertsPolicy : ICertificatePolicy {
                public bool CheckValidationResult(
                    ServicePoint srvPoint, X509Certificate certificate,
                    WebRequest request, int certificateProblem) {
                    return true;
                }
            }
"@
        [System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
    }
}

# Helper Functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )

    $color = switch ($Type) {
        "Error"   { "Red" }
        "Success" { "Green" }
        "Warning" { "Yellow" }
        "Info"    { "Cyan" }
        default   { "White" }
    }

    $prefix = switch ($Type) {
        "Error"   { "✗ Error: " }
        "Success" { "✓ " }
        "Warning" { "⚠ " }
        "Info"    { "ℹ " }
        default   { "" }
    }

    Write-Host "$prefix$Message" -ForegroundColor $color
}

function Test-TcpConnection {
    param(
        [string]$Hostname,
        [int]$Port,
        [int]$TimeoutMs = 3000
    )

    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $async = $client.BeginConnect($Hostname, $Port, $null, $null)
        $wait = $async.AsyncWaitHandle.WaitOne($TimeoutMs, $false)

        if ($wait) {
            $client.EndConnect($async)
            $client.Close()
            return $true
        } else {
            $client.Close()
            return $false
        }
    } catch {
        return $false
    }
}

# Clean platform URL
$PlatformUrl = $PlatformUrl -replace '^https?://', '' -replace '/$', ''

# Prompt for credentials
if ([string]::IsNullOrEmpty($Username)) {
    $Username = Read-Host "Username"
}

if ([string]::IsNullOrEmpty($Username)) {
    Write-ColorOutput "Username is required" -Type Error
    exit 1
}

$SecurePassword = Read-Host "Password" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
$Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

if ([string]::IsNullOrEmpty($Password)) {
    Write-ColorOutput "Password is required" -Type Error
    exit 1
}

# Build token URL
$GrpcTarget = "${PlatformUrl}:${GrpcPort}"

if ([string]::IsNullOrEmpty($TokenUrl)) {
    # Auto-detect auth path if not specified
    if ([string]::IsNullOrEmpty($AuthPath)) {
        if ($PlatformUrl -match "local" -or $AuthUrl -match "local" -or
            $PlatformUrl -match "localhost" -or $AuthUrl -match "localhost") {
            $AuthPath = "/auth/realms"
            if ($Debug) {
                Write-ColorOutput "Auto-detected local environment, using Keycloak < 17 path: /auth/realms" -Type Info
            }
        } else {
            $AuthPath = $DEFAULT_AUTH_PATH
            if ($Debug) {
                Write-ColorOutput "Using Keycloak 17+ path: $DEFAULT_AUTH_PATH" -Type Info
            }
        }
    }

    # Clean auth path
    $AuthPath = $AuthPath.Trim('/')

    # Build token URL
    if (![string]::IsNullOrEmpty($AuthUrl)) {
        $AuthUrl = $AuthUrl -replace '^https?://', '' -replace '/$', ''

        if ($AuthUrl -match ':\d+$') {
            $TokenUrl = "https://${AuthUrl}/${AuthPath}/${Realm}/protocol/openid-connect/token"
        } else {
            $TokenUrl = "https://${AuthUrl}:${AuthPort}/${AuthPath}/${Realm}/protocol/openid-connect/token"
        }
    } else {
        $TokenUrl = "https://${PlatformUrl}:${AuthPort}/${AuthPath}/${Realm}/protocol/openid-connect/token"
    }
} else {
    Write-ColorOutput "Using provided token URL" -Type Info
}

# Debug output
if ($Debug) {
    Write-ColorOutput "Configuration:" -Type Info
    Write-Host "  Platform URL: $PlatformUrl"
    if (![string]::IsNullOrEmpty($AuthUrl)) {
        Write-Host "  Auth URL: $AuthUrl"
    }
    if (![string]::IsNullOrEmpty($AuthPath)) {
        Write-Host "  Auth Path: /$AuthPath"
    }
    Write-Host "  Token URL: $TokenUrl"
    Write-Host "  gRPC Target: $GrpcTarget"
    Write-Host "  Client ID: $ClientId"
    Write-Host "  Username: $Username"
    Write-Host "  Realm: $Realm"
    Write-Host "  Timeout: ${Timeout}s"
    Write-Host "  Insecure: $Insecure"
}

# Check dependencies
$dependencies = @("grpcui")
foreach ($dep in $dependencies) {
    if (!(Get-Command $dep -ErrorAction SilentlyContinue)) {
        Write-ColorOutput "Required command '$dep' not found. Please install it first." -Type Error
        Write-Host "  Install via: go install github.com/fullstorydev/grpcui/cmd/grpcui@latest"
        Write-Host "  Or via Scoop: scoop install grpcui"
        exit 1
    }
}

# Extract host and port for connectivity check
if ($TokenUrl -match 'https://([^:/]+)(?::(\d+))?') {
    $AuthHost = $Matches[1]
    $AuthPortCheck = if ($Matches[2]) { [int]$Matches[2] } else { 443 }

    if ($Debug) {
        Write-ColorOutput "Testing connectivity to auth server..." -Type Info
    }

    if (!(Test-TcpConnection -Hostname $AuthHost -Port $AuthPortCheck)) {
        Write-ColorOutput "Cannot connect to auth server at ${AuthHost}:${AuthPortCheck}" -Type Error
        Write-ColorOutput "Possible issues:" -Type Warning
        Write-Host "  • No server is running on port $AuthPortCheck"
        Write-Host "  • Firewall is blocking the connection"
        Write-Host "  • Wrong hostname or port number"
        Write-Host ""
        Write-Host "  Did you mean to specify a different port? Use -AuthPort PORT"
        exit 1
    }

    if ($Debug) {
        Write-ColorOutput "Successfully connected to ${AuthHost}:${AuthPortCheck}" -Type Success
    }
}

# Dry run
if ($DryRun) {
    Write-ColorOutput "Would execute:" -Type Info
    Write-Host "  Invoke-RestMethod to: $TokenUrl"
    Write-Host "  grpcui -H `"Authorization: Bearer [ACCESS_TOKEN]`" `"$GrpcTarget`""
    exit 0
}

# Fetch access token
Write-ColorOutput "Fetching access token from $PlatformUrl..." -Type Info

try {
    $body = @{
        grant_type = "password"
        client_id = $ClientId
        username = $Username
        password = $Password
    }

    if ($Debug) {
        Write-ColorOutput "Executing: Invoke-RestMethod -Uri $TokenUrl -Method POST" -Type Info
    }

    $response = Invoke-RestMethod -Uri $TokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded" -TimeoutSec $Timeout

    if ($Debug) {
        Write-ColorOutput "Response received" -Type Info
        if ($response.access_token) {
            Write-Host "  Token received (first 20 chars): $($response.access_token.Substring(0, [Math]::Min(20, $response.access_token.Length)))..."
        }
    }

    if ([string]::IsNullOrEmpty($response.access_token)) {
        Write-ColorOutput "Failed to retrieve access token" -Type Error

        if (![string]::IsNullOrEmpty($response.error)) {
            Write-ColorOutput "Error type: $($response.error)" -Type Error
        }
        if (![string]::IsNullOrEmpty($response.error_description)) {
            Write-ColorOutput "Error: $($response.error_description)" -Type Error

            if ($response.error_description -match "Invalid user credentials|invalid_grant") {
                Write-ColorOutput "Authentication failed. Please check your username and password." -Type Warning
            }
        } else {
            Write-ColorOutput "No error description provided by server" -Type Warning
            Write-Host ($response | ConvertTo-Json)
        }
        exit 1
    }

    $AccessToken = $response.access_token
    Write-ColorOutput "Access token retrieved successfully" -Type Success

} catch {
    Write-ColorOutput "Failed to connect to auth server" -Type Error

    if ($_.Exception.Message -match "Unable to connect|Connection refused") {
        Write-ColorOutput "Connection refused - no server is listening on this port" -Type Error
        Write-Host "  Auth server: $TokenUrl"
        Write-ColorOutput "Check if the auth server is running and the port is correct" -Type Warning
    } elseif ($_.Exception.Message -match "timeout|timed out") {
        Write-ColorOutput "Connection timed out after ${Timeout}s" -Type Error
        Write-ColorOutput "The server is not responding. Possible causes:" -Type Warning
        Write-Host "  • Server is not running"
        Write-Host "  • Server is too slow to respond"
        Write-Host "  • Network connectivity issues"
        Write-Host "  • Firewall blocking the connection"
    } elseif ($_.Exception.Message -match "SSL|certificate") {
        Write-ColorOutput "SSL certificate verification failed" -Type Error
        Write-Host $_.Exception.Message
        Write-ColorOutput "For self-signed certificates, use: -Insecure" -Type Warning
    } else {
        Write-Host $_.Exception.Message
    }

    if ($PlatformUrl -match "local" -or $AuthUrl -match "local") {
        Write-Host ""
        Write-ColorOutput "Tip: For local development, you might need: -Insecure -AuthPort 8443" -Type Info
    }

    exit 1
}

# Check gRPC target connectivity
if ($GrpcTarget -match '^([^:]+):(\d+)$') {
    $GrpcHost = $Matches[1]
    $GrpcPortCheck = [int]$Matches[2]

    if ($Debug) {
        Write-ColorOutput "Testing connectivity to gRPC server..." -Type Info
    }

    if (!(Test-TcpConnection -Hostname $GrpcHost -Port $GrpcPortCheck)) {
        Write-ColorOutput "Cannot connect to gRPC server at ${GrpcHost}:${GrpcPortCheck}" -Type Warning
        Write-ColorOutput "The server might not be running on port $GrpcPortCheck" -Type Warning
        Write-Host "  Use -GrpcPort PORT to specify the correct gRPC port"
        Write-Host ""
        Write-ColorOutput "Attempting to launch grpcui anyway (it may provide its own error message)..." -Type Info
    } elseif ($Debug) {
        Write-ColorOutput "Successfully connected to ${GrpcHost}:${GrpcPortCheck}" -Type Success
    }
}

# Launch grpcui
Write-ColorOutput "Launching grpcui for $GrpcTarget..." -Type Info

& grpcui -H "Authorization: Bearer $AccessToken" $GrpcTarget

Write-ColorOutput "grpcui session ended" -Type Success
