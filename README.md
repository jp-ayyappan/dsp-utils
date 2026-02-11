# DSP Utils

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Utility scripts and tools for Data Security Platform (DSP) infrastructure management, including Keycloak administration, gRPC UI tools, and comprehensive Postman API collections.

## Contents

### grpcui/
Scripts for running gRPC UI tools:
- `runGRPCUI.sh` - Bash script for running gRPC UI
- `runGRPCUI.ps1` - PowerShell script for running gRPC UI

### keycloak/
Tools for managing Keycloak instances:
- `keycloak_admin.py` - Comprehensive admin tool for clients, users, and attributes
- `requirements.txt` - Python dependencies

### postman/
Postman collections for DSP APIs:
- `DSP-gRPC-APIs.postman_collection.json` - Comprehensive gRPC API collection
- Includes Tagging PDP, Policy Artifact, and NanoTDF Rewrap services

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

See individual directories for specific usage instructions:
- **[Postman Collection Guide](postman/README.md)** - 151 endpoints across 16 services
- **[Keycloak Admin Guide](keycloak/README.md)** - CLI for managing Keycloak
- **[gRPC UI Guide](grpcui/README.md)** - Interactive gRPC service exploration

## License

MIT License - see [LICENSE](LICENSE) file for details.
