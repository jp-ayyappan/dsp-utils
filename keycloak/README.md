# Keycloak Admin Tools

Comprehensive Python tool for managing Keycloak realms, clients, users, and attributes.

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

## keycloak_admin.py

All-in-one tool for Keycloak administration tasks.

### Client Management

```bash
# List all clients
python keycloak_admin.py list

# Show client details
python keycloak_admin.py show <client-id>

# Find clients with audience mappers
python keycloak_admin.py find
python keycloak_admin.py find --audience "https://ohalo.platform.partner.dsp-prod-green.virtru.com"

# Update audience for specific clients (comma-separated)
python keycloak_admin.py update-audience \
  --client-ids client1,client2,client3 \
  --audience "https://ohalo.platform.partner.dsp-prod-green.virtru.com"

# Interactive mode - find and fix clients with wrong audience
python keycloak_admin.py interactive
```

### User Management

```bash
# List all users
python keycloak_admin.py list-users

# List users with filter
python keycloak_admin.py list-users --filter "test"

# Reset passwords for multiple users (comma-separated)
# By default, passwords are temporary (users must change on first login)
python keycloak_admin.py reset-passwords \
  --usernames user1,user2,user3 \
  --password "NewPassword123!"

# Set permanent passwords
python keycloak_admin.py reset-passwords \
  --usernames user1,user2 \
  --password "NewPassword123!" \
  --permanent
```

### User Attribute Sync

Parse usernames and automatically set attributes based on naming patterns.

**Pattern:** `{classification}-{nationality}-{needToKnow}`

**Examples:**
- `secret-usa-aaa` → Classification: Secret, Nationality: USA, Need To Know: AAA
- `top-secret-gbr-bbb` → Classification: Top Secret, Nationality: GBR, Need To Know: BBB
- `classified-fra-int` → Classification: Classified, Nationality: FRA, Need To Know: INT

```bash
# Dry run - see what would be done without making changes
python keycloak_admin.py sync-user-attributes --dry-run

# Execute - creates user profile attributes and sets user attributes
python keycloak_admin.py sync-user-attributes
```

**What this command does:**
1. Creates user profile attributes (`classification`, `nationality`, `needToKnow`) in Realm Settings if they don't exist
2. Scans all users in the realm
3. Parses usernames matching the pattern
4. Sets the appropriate attributes for each matching user
5. Attributes then appear in the User Details tab (not just the Attributes tab)

## Features

- ✓ Client audience management (fix incorrect audience configurations)
- ✓ Batch user password resets (temporary or permanent)
- ✓ User attribute sync from username patterns
- ✓ User profile attribute creation (appear in User Details tab)
- ✓ Interactive mode for discovering issues
- ✓ Dry-run mode for safe testing
- ✓ Comprehensive error handling and reporting

## Keycloak Instance

- **URL:** https://keycloak-ohalo.dsp-prod-green.virtru.com/admin/dsp-ohalo/console/
- **Realm:** dsp-ohalo
- **Access Level:** realm-admin
