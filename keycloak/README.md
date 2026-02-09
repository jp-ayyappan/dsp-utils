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

**User Attribute Sync:**
```bash
# Parse usernames and automatically set attributes based on naming pattern
# Pattern: {classification}-{nationality}-{needToKnow}
# Examples:
#   secret-usa-aaa     → Classification: Secret, Nationality: USA, Need To Know: AAA
#   top-secret-gbr-bbb → Classification: Top Secret, Nationality: GBR, Need To Know: BBB
#   classified-fra-int → Classification: Classified, Nationality: FRA, Need To Know: INT

# Dry run - see what would be done without making changes
python manage_clients.py sync-user-attributes --dry-run

# Execute - creates user profile attributes and sets user attributes
python manage_clients.py sync-user-attributes
```

This command will:
1. Create user profile attributes (`classification`, `nationality`, `needToKnow`) in Realm Settings if they don't exist
2. Scan all users in the realm
3. Parse usernames matching the pattern `{classification}-{nationality}-{needToKnow}`
4. Set the appropriate attributes for each matching user
5. Attributes will then appear in the User Details tab (not just the Attributes tab)
```

## Keycloak Instance

- **URL:** https://keycloak-ohalo.dsp-prod-green.virtru.com/admin/dsp-ohalo/console/
- **Realm:** dsp-ohalo
- **Access Level:** realm-admin
