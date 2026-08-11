"""Emit the FastAPI OpenAPI schema to a file (no database needed).

Kept in sync with the frontend's committed contract:

    uv run python scripts/export_openapi.py ../frontend/openapi.json
"""

import json
import sys
from pathlib import Path

from app.main import app


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("openapi.json")
    out.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
    print(f"Wrote OpenAPI schema to {out}")


if __name__ == "__main__":
    main()
