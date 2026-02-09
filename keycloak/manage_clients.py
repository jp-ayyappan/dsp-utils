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

    # User commands
    user_list_parser = subparsers.add_parser('list-users', help='List all users')
    user_list_parser.add_argument('--filter', help='Filter users by username (case-insensitive)')

    reset_pw_parser = subparsers.add_parser('reset-passwords', help='Reset passwords for multiple users')
    reset_pw_parser.add_argument('--usernames', required=True, help='Comma-separated usernames')
    reset_pw_parser.add_argument('--password', required=True, help='New password to set')
    reset_pw_parser.add_argument('--permanent', action='store_true', help='Set as permanent password (default: temporary)')

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


if __name__ == '__main__':
    main()
