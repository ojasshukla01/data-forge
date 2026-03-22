#!/usr/bin/env python3
"""Export OpenAPI schema from the Data Forge API for offline use."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data_forge.api.main import app

if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "docs" / "openapi.json"
    schema = app.openapi()
    out.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Exported OpenAPI schema to {out}")
