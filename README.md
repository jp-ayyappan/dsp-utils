# DSP Utils

Utility scripts for DSP infrastructure management.

## Contents

### grpcui/
Scripts for running gRPC UI tools:
- `runGRPCUI.sh` - Bash script for running gRPC UI
- `runGRPCUI.ps1` - PowerShell script for running gRPC UI

### keycloak/
Tools for managing Keycloak instances:
- `keycloak_admin.py` - Comprehensive admin tool for clients, users, and attributes
- `requirements.txt` - Python dependencies

## Setup

### Keycloak Python Scripts

1. Create and activate a virtual environment:
```bash
cd keycloak
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your Keycloak connection (see keycloak/README.md)

## Usage

See individual directories for specific usage instructions.
