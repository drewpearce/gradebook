"""Small management CLI. Run with ``python -m app.cli <command>``."""

import argparse
import getpass
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import MAX_PASSWORD_BYTES, hash_password
from app.db import SessionLocal
from app.models import Teacher

MIN_PASSWORD_CHARS = 8


def create_teacher(
    username: str,
    password: str,
    *,
    session_factory: Callable[[], Session] = SessionLocal,
    allow_second_teacher: bool = False,
) -> None:
    """Create the teacher, or reset their password if the username already exists.

    Refuses a new username when a Teacher already exists (a typo during a reset would
    otherwise create a second full-access account) unless ``allow_second_teacher``.
    """
    if len(password) < MIN_PASSWORD_CHARS:
        raise SystemExit(f"Password must be at least {MIN_PASSWORD_CHARS} characters.")
    if len(password.encode()) > MAX_PASSWORD_BYTES:
        raise SystemExit(f"Password must be at most {MAX_PASSWORD_BYTES} bytes.")
    with session_factory() as session:
        teacher = session.scalar(select(Teacher).where(Teacher.username == username))
        if teacher is None:
            existing = session.scalar(select(Teacher.username).limit(1))
            if existing is not None and not allow_second_teacher:
                raise SystemExit(
                    f"A teacher already exists: '{existing}'. To reset their password, "
                    f"use that username; to add another teacher, pass --allow-second-teacher."
                )
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
    create.add_argument("--allow-second-teacher", action="store_true")
    args = parser.parse_args()

    if args.command == "create-teacher":
        password = getpass.getpass("Password: ")
        if not password:
            raise SystemExit("Password must not be empty.")
        if password != getpass.getpass("Confirm password: "):
            raise SystemExit("Passwords do not match.")
        create_teacher(args.username, password, allow_second_teacher=args.allow_second_teacher)


if __name__ == "__main__":
    main()
