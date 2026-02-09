#!/usr/bin/env python3
"""
Keycloak Client Management Tool

This script helps manage Keycloak clients, particularly for bulk updates
to audience configurations.
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Optional
from dotenv import load_dotenv
from keycloak import KeycloakAdmin, KeycloakOpenIDConnection


def load_config():
    """Load configuration from .env file."""
    load_dotenv()

    config = {
        'url': os.getenv('KEYCLOAK_URL'),
        'realm': os.getenv('KEYCLOAK_REALM'),
        'username': os.getenv('KEYCLOAK_USERNAME'),
        'password': os.getenv('KEYCLOAK_PASSWORD'),
    }

    # Validate required config
    missing = [k for k, v in config.items() if not v]
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        print("Please create a .env file based on .env.example")
        sys.exit(1)

    return config


def get_keycloak_admin(config: Dict) -> KeycloakAdmin:
    """Create and return a KeycloakAdmin instance."""
    try:
        keycloak_connection = KeycloakOpenIDConnection(
            server_url=config['url'],
            username=config['username'],
            password=config['password'],
            realm_name=config['realm'],
            verify=True
        )

        admin = KeycloakAdmin(connection=keycloak_connection)
        return admin
    except Exception as e:
        print(f"Error connecting to Keycloak: {e}")
        sys.exit(1)


def list_clients(admin: KeycloakAdmin):
    """List all clients in the realm."""
    try:
        clients = admin.get_clients()
        print(f"\nFound {len(clients)} clients:\n")
        print(f"{'Client ID':<40} {'Name':<30} {'ID'}")
        print("-" * 100)
        for client in clients:
            client_id = client.get('clientId', 'N/A')
            name = client.get('name', '')
            id_val = client.get('id', '')
            print(f"{client_id:<40} {name:<30} {id_val}")
    except Exception as e:
        print(f"Error listing clients: {e}")


def show_client(admin: KeycloakAdmin, client_id: str):
    """Show detailed information about a specific client."""
    try:
        # Get client by clientId
        clients = admin.get_clients()
        client = next((c for c in clients if c['clientId'] == client_id), None)

        if not client:
            print(f"Client '{client_id}' not found")
            return

        print(f"\nClient Details for '{client_id}':")
        print("-" * 80)
        print(json.dumps(client, indent=2))

        # Get protocol mappers
        internal_id = client['id']
        mappers = admin.get_mappers_from_client(internal_id)

        print(f"\nProtocol Mappers:")
        print("-" * 80)
        for mapper in mappers:
            print(f"  - {mapper.get('name')} ({mapper.get('protocolMapper')})")
            if 'config' in mapper:
                for key, value in mapper['config'].items():
                    print(f"      {key}: {value}")

    except Exception as e:
        print(f"Error showing client: {e}")


def find_clients_with_audience(admin: KeycloakAdmin, audience: Optional[str] = None):
    """Find clients with specific audience configuration."""
    try:
        clients = admin.get_clients()
        matching = []

        for client in clients:
            internal_id = client['id']
            client_id = client.get('clientId', '')

            try:
                mappers = admin.get_mappers_from_client(internal_id)
                for mapper in mappers:
                    if mapper.get('protocolMapper') == 'oidc-audience-mapper':
                        config = mapper.get('config', {})
                        # Check both custom and client audience fields
                        custom_audience = config.get('included.custom.audience', '')
                        client_audience = config.get('included.client.audience', '')
                        current_audience = custom_audience or client_audience

                        if audience is None or current_audience == audience:
                            matching.append({
                                'clientId': client_id,
                                'id': internal_id,
                                'mapper': mapper.get('name'),
                                'audience': current_audience,
                                'audience_type': 'custom' if custom_audience else 'client'
                            })
            except Exception as e:
                # Skip clients we can't read mappers for
                continue

        return matching
    except Exception as e:
        print(f"Error finding clients: {e}")
        return []


def list_clients_with_redirect_uris(admin: KeycloakAdmin, uri_filter: Optional[str] = None):
    """List all clients with their redirect URIs."""
    try:
        clients = admin.get_clients()

        print(f"\nFound {len(clients)} clients:\n")
        print(f"{'Client ID':<40} {'Redirect URIs'}")
        print("-" * 120)

        matching_count = 0
        for client in clients:
            client_id = client.get('clientId', 'N/A')
            redirect_uris = client.get('redirectUris', [])

            # Filter if specified
            if uri_filter:
                if not any(uri_filter in uri for uri in redirect_uris):
                    continue

            matching_count += 1
            if redirect_uris:
                print(f"{client_id:<40} {redirect_uris[0]}")
                for uri in redirect_uris[1:]:
                    print(f"{'':<40} {uri}")
            else:
                print(f"{client_id:<40} (no redirect URIs)")

        if uri_filter:
            print(f"\n{matching_count} clients matched filter '{uri_filter}'")

        return clients
    except Exception as e:
        print(f"Error listing clients: {e}")
        return []


def update_client_redirect_uris(admin: KeycloakAdmin, client_id: str, redirect_uris: List[str],
                                 mode: str = "replace"):
    """
    Update redirect URIs for a specific client.

    Args:
        mode: "replace" (replace all), "add" (append), or "remove" (remove specific URIs)
    """
    try:
        # Get client by clientId
        clients = admin.get_clients()
        client = next((c for c in clients if c['clientId'] == client_id), None)

        if not client:
            print(f"Client '{client_id}' not found")
            return False

        internal_id = client['id']
        current_uris = client.get('redirectUris', [])

        if mode == "replace":
            new_uris = redirect_uris
            print(f"✓ Replaced redirect URIs for '{client_id}'")
            print(f"  Old: {current_uris}")
            print(f"  New: {new_uris}")
        elif mode == "add":
            new_uris = list(set(current_uris + redirect_uris))  # Remove duplicates
            print(f"✓ Added redirect URIs to '{client_id}'")
            print(f"  Added: {redirect_uris}")
            print(f"  Result: {new_uris}")
        elif mode == "remove":
            new_uris = [uri for uri in current_uris if uri not in redirect_uris]
            print(f"✓ Removed redirect URIs from '{client_id}'")
            print(f"  Removed: {redirect_uris}")
            print(f"  Result: {new_uris}")
        else:
            print(f"✗ Invalid mode '{mode}'. Use 'replace', 'add', or 'remove'")
            return False

        # Update client
        admin.update_client(internal_id, {'redirectUris': new_uris})
        return True

    except Exception as e:
        print(f"✗ Error updating client '{client_id}': {e}")
        return False


def batch_update_redirect_uris(admin: KeycloakAdmin, client_ids: List[str],
                               redirect_uris: List[str], mode: str = "replace"):
    """Update redirect URIs for multiple clients."""
    success_count = 0
    failed_count = 0

    print(f"\nUpdating redirect URIs for {len(client_ids)} clients...")
    print(f"Mode: {mode}")
    print(f"URIs: {redirect_uris}\n")

    for client_id in client_ids:
        if update_client_redirect_uris(admin, client_id, redirect_uris, mode):
            success_count += 1
        else:
            failed_count += 1
        print()

    print("=" * 60)
    print(f"Summary: {success_count} succeeded, {failed_count} failed")
    return success_count, failed_count


def find_and_replace_redirect_uri(admin: KeycloakAdmin, old_pattern: str, new_uri: str,
                                   dry_run: bool = False):
    """
    Find all clients with redirect URIs containing a pattern and replace them.

    Args:
        old_pattern: Pattern to search for in redirect URIs
        new_uri: New URI to replace matching URIs with
        dry_run: If True, only show what would be changed
    """
    try:
        clients = admin.get_clients()
        matching_clients = []

        print(f"\nSearching for redirect URIs containing: '{old_pattern}'")
        print(f"Will replace with: '{new_uri}'\n")

        for client in clients:
            client_id = client.get('clientId', '')
            redirect_uris = client.get('redirectUris', [])

            # Check if any redirect URI contains the pattern
            matching_uris = [uri for uri in redirect_uris if old_pattern in uri]

            if matching_uris:
                matching_clients.append({
                    'clientId': client_id,
                    'id': client['id'],
                    'oldUris': redirect_uris,
                    'matchingUris': matching_uris
                })

        if not matching_clients:
            print(f"No clients found with redirect URIs containing '{old_pattern}'")
            return

        print(f"Found {len(matching_clients)} clients:\n")

        for idx, client_info in enumerate(matching_clients, 1):
            print(f"{idx}. {client_info['clientId']}")
            print(f"   Matching URIs: {client_info['matchingUris']}")

            # Calculate new URIs
            new_uris = [new_uri if old_pattern in uri else uri for uri in client_info['oldUris']]
            print(f"   Would become: {new_uris}")
            print()

        if dry_run:
            print("⚠ DRY RUN - No changes made")
            return

        # Confirm
        confirm = input(f"\nUpdate redirect URIs for {len(matching_clients)} clients? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Cancelled.")
            return

        # Execute updates
        success_count = 0
        for client_info in matching_clients:
            try:
                new_uris = [new_uri if old_pattern in uri else uri for uri in client_info['oldUris']]
                admin.update_client(client_info['id'], {'redirectUris': new_uris})
                print(f"✓ Updated {client_info['clientId']}")
                success_count += 1
            except Exception as e:
                print(f"✗ Failed to update {client_info['clientId']}: {e}")

        print(f"\nCompleted: {success_count}/{len(matching_clients)} clients updated")

    except Exception as e:
        print(f"Error: {e}")


def update_client_audience(admin: KeycloakAdmin, client_id: str, new_audience: str, mapper_name: str = "audience-mapper"):
    """Update the audience for a specific client."""
    try:
        # Get client internal ID
        clients = admin.get_clients()
        client = next((c for c in clients if c['clientId'] == client_id), None)

        if not client:
            print(f"Client '{client_id}' not found")
            return False

        internal_id = client['id']

        # Check if audience mapper exists
        mappers = admin.get_mappers_from_client(internal_id)
        audience_mapper = next(
            (m for m in mappers if m.get('protocolMapper') == 'oidc-audience-mapper'),
            None
        )

        if audience_mapper:
            # Update existing mapper - use custom audience field and clear client audience
            mapper_id = audience_mapper['id']
            config = audience_mapper['config']

            # Remove old client audience if present
            config.pop('included.client.audience', None)

            # Set custom audience
            config['included.custom.audience'] = new_audience
            config['access.token.claim'] = 'true'
            config['id.token.claim'] = 'true'
            config['introspection.token.claim'] = 'true'

            admin.update_client_mapper(internal_id, mapper_id, audience_mapper)
            print(f"✓ Updated audience for '{client_id}' to '{new_audience}'")
        else:
            # Create new mapper with custom audience
            mapper_payload = {
                'name': mapper_name,
                'protocol': 'openid-connect',
                'protocolMapper': 'oidc-audience-mapper',
                'config': {
                    'included.custom.audience': new_audience,
                    'access.token.claim': 'true',
                    'id.token.claim': 'true',
                    'introspection.token.claim': 'true'
                }
            }
            admin.add_mapper_to_client(internal_id, mapper_payload)
            print(f"✓ Created audience mapper for '{client_id}' with audience '{new_audience}'")

        return True

    except Exception as e:
        print(f"✗ Error updating client '{client_id}': {e}")
        return False


def interactive_mode(admin: KeycloakAdmin):
    """Interactive mode to find and fix clients."""
    print("\n=== Interactive Client Audience Updater ===\n")

    # Find all clients with audience mappers
    print("Scanning for clients with audience mappers...")
    clients_with_audience = find_clients_with_audience(admin)

    if not clients_with_audience:
        print("No clients found with audience mappers.")
        return

    print(f"\nFound {len(clients_with_audience)} clients with audience configuration:\n")
    print(f"{'#':<4} {'Client ID':<40} {'Type':<10} {'Current Audience':<40}")
    print("-" * 100)
    for idx, client in enumerate(clients_with_audience, 1):
        aud_type = client.get('audience_type', 'unknown')
        marker = "✓" if aud_type == "custom" else "✗"
        print(f"{idx:<4} {client['clientId']:<40} {marker} {aud_type:<8} {client['audience']:<40}")

    print("\nWhat would you like to do?")
    print("1. Update all clients to a new audience")
    print("2. Update specific clients")
    print("3. Exit")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == '1':
        new_audience = input("Enter the new audience value: ").strip()
        if new_audience:
            confirm = input(f"Update ALL {len(clients_with_audience)} clients to '{new_audience}'? (yes/no): ").strip().lower()
            if confirm == 'yes':
                for client in clients_with_audience:
                    update_client_audience(admin, client['clientId'], new_audience)
            else:
                print("Cancelled.")

    elif choice == '2':
        indices = input("Enter client numbers to update (comma-separated): ").strip()
        try:
            selected_indices = [int(i.strip()) - 1 for i in indices.split(',')]
            selected_clients = [clients_with_audience[i] for i in selected_indices]

            new_audience = input("Enter the new audience value: ").strip()
            if new_audience:
                for client in selected_clients:
                    update_client_audience(admin, client['clientId'], new_audience)
        except (ValueError, IndexError):
            print("Invalid selection.")

    else:
        print("Exiting.")


def list_users(admin: KeycloakAdmin, username_filter: Optional[str] = None):
    """List all users in the realm."""
    try:
        users = admin.get_users({})

        # Filter by username if provided
        if username_filter:
            users = [u for u in users if username_filter.lower() in u.get('username', '').lower()]

        print(f"\nFound {len(users)} users:\n")
        print(f"{'Username':<30} {'Email':<40} {'ID'}")
        print("-" * 100)
        for user in users:
            username = user.get('username', 'N/A')
            email = user.get('email', '')
            user_id = user.get('id', '')
            print(f"{username:<30} {email:<40} {user_id}")
    except Exception as e:
        print(f"Error listing users: {e}")


def reset_user_passwords(admin: KeycloakAdmin, usernames: List[str], new_password: str, temporary: bool = True):
    """Reset passwords for multiple users."""
    try:
        # Get all users
        all_users = admin.get_users({})

        # Create username to user_id mapping
        user_map = {u.get('username'): u.get('id') for u in all_users}

        success_count = 0
        failed_count = 0

        for username in usernames:
            if username not in user_map:
                print(f"✗ User '{username}' not found")
                failed_count += 1
                continue

            try:
                user_id = user_map[username]
                admin.set_user_password(user_id, new_password, temporary=temporary)
                temp_str = " (temporary)" if temporary else ""
                print(f"✓ Password reset for '{username}'{temp_str}")
                success_count += 1
            except Exception as e:
                print(f"✗ Error resetting password for '{username}': {e}")
                failed_count += 1

        print(f"\nSummary: {success_count} succeeded, {failed_count} failed")
        return success_count, failed_count

    except Exception as e:
        print(f"Error resetting passwords: {e}")
        return 0, len(usernames)


def get_user_profile_config(admin: KeycloakAdmin):
    """Get the user profile configuration."""
    try:
        # User profile is accessed via the admin REST API
        realm = admin.connection.realm_name
        url = f"{admin.connection.server_url}/admin/realms/{realm}/users/profile"
        response = admin.connection.raw_get(url)
        return response.json() if hasattr(response, 'json') else response
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return None


def create_user_profile_attribute(admin: KeycloakAdmin, attribute_name: str, display_name: str,
                                   multivalued: bool = False, required: bool = False):
    """Create or update a user profile attribute."""
    try:
        realm = admin.connection.realm_name
        profile_url = f"{admin.connection.server_url}/admin/realms/{realm}/users/profile"

        # Get current profile
        profile = get_user_profile_config(admin)
        if not profile:
            print(f"Could not retrieve user profile configuration")
            return False

        # Check if attribute already exists
        attributes = profile.get('attributes', [])
        existing_attr = next((attr for attr in attributes if attr.get('name') == attribute_name), None)

        if existing_attr:
            print(f"  Attribute '{attribute_name}' already exists")
            return True

        # Create new attribute
        new_attribute = {
            "name": attribute_name,
            "displayName": display_name,
            "validations": {},
            "permissions": {
                "view": ["admin", "user"],
                "edit": ["admin"]
            },
            "multivalued": multivalued,
            "required": {
                "roles": [],
                "scopes": []
            } if not required else {
                "roles": ["user"],
                "scopes": []
            }
        }

        # Add to attributes list
        attributes.append(new_attribute)
        profile['attributes'] = attributes

        # Update profile
        admin.connection.raw_put(profile_url, data=json.dumps(profile))
        print(f"✓ Created user profile attribute '{attribute_name}'")
        return True

    except Exception as e:
        print(f"✗ Error creating attribute '{attribute_name}': {e}")
        return False


def parse_username_attributes(username: str) -> Optional[Dict[str, str]]:
    """
    Parse username pattern: {classification}-{nationality}-{needToKnow}

    Examples:
        secret-usa-aaa -> classification: Secret, nationality: USA, needToKnow: AAA
        top-secret-gbr-bbb -> classification: Top Secret, nationality: GBR, needToKnow: BBB
        classified-fra-int -> classification: Classified, nationality: FRA, needToKnow: INT
    """
    import re

    # Pattern: one or more words (with hyphens) - country code - need to know code
    pattern = r'^([\w-]+)-([A-Z]{2,3})-([A-Z]{2,})$'
    match = re.match(pattern, username, re.IGNORECASE)

    if not match:
        return None

    classification_raw = match.group(1)
    nationality = match.group(2).upper()
    need_to_know = match.group(3).upper()

    # Convert classification to proper case
    classification_map = {
        'secret': 'Secret',
        'top-secret': 'Top Secret',
        'classified': 'Classified',
        'unclassified': 'Unclassified',
        'confidential': 'Confidential'
    }

    classification = classification_map.get(classification_raw.lower(),
                                           classification_raw.replace('-', ' ').title())

    return {
        'classification': classification,
        'nationality': nationality,
        'needToKnow': need_to_know
    }


def set_user_attributes_from_username(admin: KeycloakAdmin, user_id: str, username: str,
                                      attributes: Dict[str, str], dry_run: bool = False):
    """Set user attributes based on parsed username."""
    try:
        if dry_run:
            print(f"  Would set attributes for '{username}':")
            for key, value in attributes.items():
                print(f"    {key}: {value}")
            return True

        # Get current user
        user = admin.get_user(user_id)
        current_attributes = user.get('attributes', {})

        # Update attributes (preserve existing ones)
        for key, value in attributes.items():
            current_attributes[key] = [value] if not isinstance(value, list) else value

        # Update user
        admin.update_user(user_id, {'attributes': current_attributes})
        print(f"✓ Updated attributes for '{username}'")
        return True

    except Exception as e:
        print(f"✗ Error updating user '{username}': {e}")
        return False


def sync_user_attributes_from_usernames(admin: KeycloakAdmin, dry_run: bool = False):
    """
    Sync user attributes based on username patterns.

    1. Creates user profile attributes (classification, nationality, needToKnow) if they don't exist
    2. Scans all users and parses usernames matching the pattern
    3. Sets attributes for matching users
    """
    print("\n=== User Attribute Sync from Usernames ===\n")

    # Step 1: Ensure user profile attributes exist
    print("Step 1: Ensuring user profile attributes exist...")

    attributes_to_create = [
        ('classification', 'Classification', False, False),
        ('nationality', 'Nationality', False, False),
        ('needToKnow', 'Need To Know', False, False)
    ]

    for attr_name, display_name, multivalued, required in attributes_to_create:
        if not dry_run:
            create_user_profile_attribute(admin, attr_name, display_name, multivalued, required)
        else:
            print(f"  Would ensure attribute '{attr_name}' exists")

    print()

    # Step 2: Get all users
    print("Step 2: Scanning users...")
    users = admin.get_users({})
    print(f"Found {len(users)} users\n")

    # Step 3: Parse and update
    print("Step 3: Parsing usernames and setting attributes...")
    print()

    matched_count = 0
    updated_count = 0
    skipped_count = 0

    for user in users:
        username = user.get('username', '')
        user_id = user.get('id', '')

        # Parse username
        parsed = parse_username_attributes(username)

        if parsed:
            matched_count += 1
            print(f"✓ Matched: {username}")
            print(f"  → Classification: {parsed['classification']}")
            print(f"  → Nationality: {parsed['nationality']}")
            print(f"  → Need To Know: {parsed['needToKnow']}")

            if set_user_attributes_from_username(admin, user_id, username, parsed, dry_run):
                updated_count += 1
            print()
        else:
            skipped_count += 1
            if dry_run:
                print(f"  Skipped: {username} (doesn't match pattern)")

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Total users: {len(users)}")
    print(f"  Matched pattern: {matched_count}")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")

    if dry_run:
        print("\n⚠ This was a DRY RUN - no changes were made")
        print("Run without --dry-run to apply changes")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Keycloak Client Management Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command
    subparsers.add_parser('list', help='List all clients')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show client details')
    show_parser.add_argument('client_id', help='Client ID to show')

    # Find command
    find_parser = subparsers.add_parser('find', help='Find clients with audience mapper')
    find_parser.add_argument('--audience', help='Filter by specific audience value')

    # Update audience command
    update_parser = subparsers.add_parser('update-audience', help='Update client audience')
    update_parser.add_argument('--client-ids', required=True, help='Comma-separated client IDs')
    update_parser.add_argument('--audience', required=True, help='New audience value')

    # Interactive command
    subparsers.add_parser('interactive', help='Interactive mode to find and fix clients')

    # Redirect URI commands
    list_redirects_parser = subparsers.add_parser('list-redirect-uris', help='List all clients with redirect URIs')
    list_redirects_parser.add_argument('--filter', help='Filter by URI containing text')

    update_redirects_parser = subparsers.add_parser('update-redirect-uris',
                                                     help='Update redirect URIs for specific clients')
    update_redirects_parser.add_argument('--client-ids', required=True, help='Comma-separated client IDs')
    update_redirects_parser.add_argument('--uris', required=True, help='Comma-separated redirect URIs')
    update_redirects_parser.add_argument('--mode', choices=['replace', 'add', 'remove'], default='replace',
                                         help='Update mode: replace (default), add, or remove')

    find_replace_redirects_parser = subparsers.add_parser('find-replace-redirect-uris',
                                                          help='Find and replace redirect URIs containing a pattern')
    find_replace_redirects_parser.add_argument('--old-pattern', required=True,
                                               help='Pattern to search for in redirect URIs')
    find_replace_redirects_parser.add_argument('--new-uri', required=True,
                                               help='New URI to replace matching URIs with')
    find_replace_redirects_parser.add_argument('--dry-run', action='store_true',
                                               help='Show what would be changed without making changes')

    # User commands
    user_list_parser = subparsers.add_parser('list-users', help='List all users')
    user_list_parser.add_argument('--filter', help='Filter users by username (case-insensitive)')

    reset_pw_parser = subparsers.add_parser('reset-passwords', help='Reset passwords for multiple users')
    reset_pw_parser.add_argument('--usernames', required=True, help='Comma-separated usernames')
    reset_pw_parser.add_argument('--password', required=True, help='New password to set')
    reset_pw_parser.add_argument('--permanent', action='store_true', help='Set as permanent password (default: temporary)')

    sync_attrs_parser = subparsers.add_parser('sync-user-attributes',
                                              help='Parse usernames and set attributes (classification, nationality, needToKnow)')
    sync_attrs_parser.add_argument('--dry-run', action='store_true',
                                   help='Show what would be done without making changes')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load config and create admin client
    config = load_config()
    admin = get_keycloak_admin(config)

    # Execute command
    if args.command == 'list':
        list_clients(admin)

    elif args.command == 'show':
        show_client(admin, args.client_id)

    elif args.command == 'find':
        clients = find_clients_with_audience(admin, args.audience)
        print(f"\nFound {len(clients)} clients:\n")
        print(f"{'Client ID':<40} {'Type':<10} {'Audience'}")
        print("-" * 80)
        for client in clients:
            aud_type = client.get('audience_type', 'unknown')
            marker = "✓" if aud_type == "custom" else "✗"
            print(f"{client['clientId']:<40} {marker} {aud_type:<8} {client['audience']}")

    elif args.command == 'update-audience':
        client_ids = [c.strip() for c in args.client_ids.split(',')]
        for client_id in client_ids:
            update_client_audience(admin, client_id, args.audience)

    elif args.command == 'interactive':
        interactive_mode(admin)

    elif args.command == 'list-redirect-uris':
        list_clients_with_redirect_uris(admin, args.filter)

    elif args.command == 'update-redirect-uris':
        client_ids = [c.strip() for c in args.client_ids.split(',')]
        redirect_uris = [u.strip() for u in args.uris.split(',')]

        print(f"\n⚠️  WARNING: About to update redirect URIs for {len(client_ids)} clients")
        print(f"Mode: {args.mode}")
        print(f"URIs: {redirect_uris}")

        confirm = input("\nType 'yes' to confirm: ").strip().lower()
        if confirm == 'yes':
            batch_update_redirect_uris(admin, client_ids, redirect_uris, args.mode)
        else:
            print("Cancelled.")

    elif args.command == 'find-replace-redirect-uris':
        if args.dry_run:
            print("\n⚠ DRY RUN MODE - No changes will be made\n")
        find_and_replace_redirect_uri(admin, args.old_pattern, args.new_uri, dry_run=args.dry_run)

    elif args.command == 'list-users':
        list_users(admin, args.filter)

    elif args.command == 'reset-passwords':
        usernames = [u.strip() for u in args.usernames.split(',')]
        temporary = not args.permanent

        print(f"\n⚠️  WARNING: About to reset passwords for {len(usernames)} users")
        if temporary:
            print("Passwords will be TEMPORARY (users must change on first login)")
        else:
            print("Passwords will be PERMANENT")

        confirm = input("\nType 'yes' to confirm: ").strip().lower()
        if confirm == 'yes':
            reset_user_passwords(admin, usernames, args.password, temporary=temporary)
        else:
            print("Cancelled.")

    elif args.command == 'sync-user-attributes':
        if args.dry_run:
            print("\n⚠ DRY RUN MODE - No changes will be made\n")
        sync_user_attributes_from_usernames(admin, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
