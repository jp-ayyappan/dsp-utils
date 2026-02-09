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

Tool for bulk updating client configurations and managing users.

**Client Management:**
```bash
# List all clients
python manage_clients.py list

# Show client details
python manage_clients.py show <client-id>

# Find clients with audience mappers
python manage_clients.py find
python manage_clients.py find --audience "https://ohalo.platform.partner.dsp-prod-green.virtru.com"

# Update audience for specific clients (comma-separated)
python manage_clients.py update-audience \
  --client-ids client1,client2,client3 \
  --audience "https://ohalo.platform.partner.dsp-prod-green.virtru.com"

# Interactive mode - find and fix clients with wrong audience
python manage_clients.py interactive
```

**User Management:**
```bash
# List all users
python manage_clients.py list-users

# List users with filter
python manage_clients.py list-users --filter "test"

# Reset passwords for multiple users (comma-separated)
# By default, passwords are temporary (users must change on first login)
python manage_clients.py reset-passwords \
  --usernames user1,user2,user3 \
  --password "NewPassword123!"

# Set permanent passwords
python manage_clients.py reset-passwords \
  --usernames user1,user2 \
  --password "NewPassword123!" \
  --permanent
```

## Keycloak Instance

- **URL:** https://keycloak-ohalo.dsp-prod-green.virtru.com/admin/dsp-ohalo/console/
- **Realm:** dsp-ohalo
- **Access Level:** realm-admin
