"""Small management CLI. Run with ``python -m app.cli <command>``."""

import argparse
import getpass

from sqlalchemy import select

from app.auth.security import hash_password
from app.db import SessionLocal
from app.models import Teacher


def create_teacher(username: str, password: str) -> None:
    """Create the single teacher, or reset their password if they already exist."""
    with SessionLocal() as session:
        teacher = session.scalar(select(Teacher).where(Teacher.username == username))
        if teacher is None:
            session.add(Teacher(username=username, password_hash=hash_password(password)))
            action = "Created"
        else:
            teacher.password_hash = hash_password(password)
            action = "Reset password for"
        session.commit()
    print(f"{action} teacher '{username}'.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create-teacher", help="Create or reset the teacher login")
    create.add_argument("--username", required=True)
    args = parser.parse_args()

    if args.command == "create-teacher":
        password = getpass.getpass("Password: ")
        if not password:
            raise SystemExit("Password must not be empty.")
        if password != getpass.getpass("Confirm password: "):
            raise SystemExit("Passwords do not match.")
        create_teacher(args.username, password)


if __name__ == "__main__":
    main()
