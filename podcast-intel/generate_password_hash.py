#!/usr/bin/env python3
"""
Generate password hash for Streamlit authentication.

Usage:
    python generate_password_hash.py
"""

import bcrypt
import getpass


def generate_hash(password: str) -> str:
    """Generate bcrypt hash for password."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def main():
    print("=" * 60)
    print("Password Hash Generator for Streamlit Authentication")
    print("=" * 60)
    print()

    password = getpass.getpass("Enter password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("\n❌ Passwords don't match!")
        return

    if len(password) < 8:
        print("\n⚠️  Warning: Password is less than 8 characters")

    hashed = generate_hash(password)

    print("\n✅ Password hash generated successfully!")
    print("\nCopy this hash to your .streamlit/secrets.toml file:")
    print("-" * 60)
    print(hashed)
    print("-" * 60)
    print()
    print("Example secrets.toml entry:")
    print(f'''
[credentials.usernames.yourusername]
email = "your-email@example.com"
name = "Your Name"
password = "{hashed}"
''')
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
