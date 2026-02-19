# Keycloak Admin Tools

Comprehensive Python tool for managing Keycloak realms, clients, users, and attributes.

Follows OpenCLI/kubectl command patterns for intuitive hierarchical commands.

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
KEYCLOAK_URL=https://keycloak.acme.com
KEYCLOAK_REALM=acme-realm
KEYCLOAK_USERNAME=your-username
KEYCLOAK_PASSWORD=your-password
```

**Note:** The `.env` file is gitignored for security.

## Command Structure

The CLI follows kubectl-style hierarchical commands:
```
keycloak_admin.py <verb> <resource> [options]
```

**Verbs:** `list`, `show`, `find`, `update`, `sync`
**Resources:** `clients`, `users`, `redirect-uris`, `audience`, `passwords`, `user-attributes`

## Commands

### List Resources

```bash
# List all clients
python keycloak_admin.py list clients

# List all users
python keycloak_admin.py list users

# List users with filter
python keycloak_admin.py list users --filter "test"

# List all clients with their redirect URIs
python keycloak_admin.py list redirect-uris

# List clients with redirect URIs containing a pattern
python keycloak_admin.py list redirect-uris --filter "localhost"
```

### Show Details

```bash
# Show client details
python keycloak_admin.py show client <client-id>
```

### Find Resources

```bash
# Find clients with audience mappers
python keycloak_admin.py find clients

# Find clients with specific audience
python keycloak_admin.py find clients --audience "https://platform.acme.com"

# Find and replace redirect URIs (dry run)
python keycloak_admin.py find redirect-uris \
  --pattern "http://localhost:8080" \
  --new-uri "https://production.example.com" \
  --dry-run

# Execute the replacement
python keycloak_admin.py find redirect-uris \
  --pattern "http://localhost:8080" \
  --new-uri "https://production.example.com"
```

### Update Resources

**Update Client Audience:**
```bash
# Update audience for specific clients (comma-separated)
python keycloak_admin.py update audience \
  --client-ids client1,client2,client3 \
  --audience "https://platform.acme.com"
```

**Update Redirect URIs:**
```bash
# Replace redirect URIs (default mode)
python keycloak_admin.py update redirect-uris \
  --client-ids "admin-client,viewer-client" \
  --uris "https://new.example.com/*,https://new.example.com:8080/*" \
  --mode replace

# Add redirect URIs (append to existing)
python keycloak_admin.py update redirect-uris \
  --client-ids "client1,client2" \
  --uris "https://additional.example.com/*" \
  --mode add

# Remove specific redirect URIs
python keycloak_admin.py update redirect-uris \
  --client-ids "client1,client2" \
  --uris "https://old.example.com/*" \
  --mode remove
```

**Update User Passwords:**
```bash
# Reset passwords (temporary by default)
python keycloak_admin.py update passwords \
  --usernames user1,user2,user3 \
  --password "NewPassword123!"

# Set permanent passwords
python keycloak_admin.py update passwords \
  --usernames user1,user2 \
  --password "NewPassword123!" \
  --permanent
```

### Sync Resources

**Sync User Attributes from Usernames:**

Parse usernames and automatically set attributes based on naming patterns.

**Pattern:** `{classification}-{nationality}-{needToKnow}`

**Examples:**
- `secret-usa-aaa` → Classification: Secret, Nationality: USA, Need To Know: AAA
- `top-secret-gbr-bbb` → Classification: Top Secret, Nationality: GBR, Need To Know: BBB
- `classified-fra-int` → Classification: Classified, Nationality: FRA, Need To Know: INT

```bash
# Dry run - see what would be done
python keycloak_admin.py sync user-attributes --dry-run

# Execute - creates user profile attributes and sets user attributes
python keycloak_admin.py sync user-attributes
```

**What this does:**
1. Creates user profile attributes (`classification`, `nationality`, `needToKnow`) in Realm Settings if they don't exist
2. Scans all users in the realm
3. Parses usernames matching the pattern
4. Sets the appropriate attributes for each matching user
5. Attributes then appear in the User Details tab (not just the Attributes tab)

### Interactive Mode

```bash
# Interactive mode - find and fix client issues
python keycloak_admin.py interactive
```

## Common Workflows

### Migrate from Localhost to Production

1. **Find what needs updating:**
   ```bash
   python keycloak_admin.py list redirect-uris --filter "localhost"
   ```

2. **Test the replacement:**
   ```bash
   python keycloak_admin.py find redirect-uris \
     --pattern "localhost:8080" \
     --new-uri "https://production.virtru.com" \
     --dry-run
   ```

3. **Execute:**
   ```bash
   python keycloak_admin.py find redirect-uris \
     --pattern "localhost:8080" \
     --new-uri "https://production.virtru.com"
   ```

### Fix Client Audience Configuration

1. **Find misconfigured clients:**
   ```bash
   python keycloak_admin.py find clients
   ```

2. **Update specific clients:**
   ```bash
   python keycloak_admin.py update audience \
     --client-ids "client1,client2" \
     --audience "https://correct.audience.com"
   ```

### Bulk User Setup

1. **Sync attributes from usernames:**
   ```bash
   python keycloak_admin.py sync user-attributes --dry-run
   python keycloak_admin.py sync user-attributes
   ```

2. **Reset passwords:**
   ```bash
   python keycloak_admin.py update passwords \
     --usernames "user1,user2,user3" \
     --password "TempPass123!"
   ```

## Features

- ✓ Client audience management (fix incorrect audience configurations)
- ✓ Redirect URI management (list, update, find and replace)
- ✓ Batch user password resets (temporary or permanent)
- ✓ User attribute sync from username patterns
- ✓ User profile attribute creation (appear in User Details tab)
- ✓ Interactive mode for discovering issues
- ✓ Dry-run mode for safe testing
- ✓ Comprehensive error handling and reporting
- ✓ kubectl-style hierarchical commands

## Keycloak Instance

- **URL:** https://keycloak.acme.com/admin/acme-realm/console/
- **Realm:** acme-realm
- **Access Level:** realm-admin

## Legal & Trademarks

All trademarks and registered trademarks are the property of their respective owners. No affiliation, sponsorship, or endorsement is implied, and no permissions have been sought for trademark use. Scripts and documents in this repository are provided “as is,” without warranties or guarantees of any kind. Upstream services may change; while reasonable efforts may be made to keep interfaces up to date, compatibility is not guaranteed.
