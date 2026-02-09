# Keycloak Management Scripts

Scripts for managing Keycloak client configurations.

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Keycloak credentials:
```bash
KEYCLOAK_URL=https://keycloak-ohalo.dsp-prod-green.virtru.com
KEYCLOAK_REALM=dsp-ohalo
KEYCLOAK_USERNAME=your-username
KEYCLOAK_PASSWORD=your-password
```

**Note:** The `.env` file is gitignored for security.

## Scripts

### manage_clients.py

Tool for bulk updating client configurations, particularly for fixing audience settings.

**Usage:**
```bash
# List all clients
python manage_clients.py list

# Show client details
python manage_clients.py show <client-id>

# Update audience for specific clients
python manage_clients.py update-audience --client-ids client1,client2 --audience your-audience

# Interactive mode - find and fix clients with wrong audience
python manage_clients.py interactive
```

## Keycloak Instance

- **URL:** https://keycloak-ohalo.dsp-prod-green.virtru.com/admin/dsp-ohalo/console/
- **Realm:** dsp-ohalo
- **Access Level:** realm-admin
