from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from data_forge.api.main import app


client = TestClient(app)


def _example_schema() -> dict[str, Any]:
  return {
      "name": "example",
      "tables": [
          {
              "name": "customers",
              "columns": [
                  {"name": "id", "data_type": "uuid", "primary_key": True},
                  {"name": "email", "data_type": "email", "nullable": False},
              ],
              "primary_key": ["id"],
          }
      ],
      "relationships": [],
  }


def test_create_and_get_custom_schema() -> None:
  payload = {
      "name": "Customer schema",
      "description": "Custom customer model",
      "tags": ["custom", "test"],
      "schema": _example_schema(),
  }
  resp = client.post("/api/custom-schemas", json=payload)
  assert resp.status_code == 200, resp.text
  created = resp.json()
  assert created["name"] == "Customer schema"
  assert created["schema"]["tables"][0]["name"] == "customers"

  schema_id = created["id"]

  get_resp = client.get(f"/api/custom-schemas/{schema_id}")
  assert get_resp.status_code == 200
  got = get_resp.json()
  assert got["id"] == schema_id
  assert got["version"] == 1


def test_versions_and_diff() -> None:
  base = {
      "name": "Diff schema",
      "schema": _example_schema(),
  }
  resp = client.post("/api/custom-schemas", json=base)
  assert resp.status_code == 200
  created = resp.json()
  schema_id = created["id"]

  # Update schema with an extra column to create a new version
  updated = _example_schema()
  updated["tables"][0]["columns"].append(
      {"name": "country", "data_type": "string", "nullable": True}
  )
  upd_resp = client.put(
      f"/api/custom-schemas/{schema_id}",
      json={"schema": updated, "description": "With country column"},
  )
  assert upd_resp.status_code == 200
  updated_rec = upd_resp.json()
  assert updated_rec["version"] == 2

  versions_resp = client.get(f"/api/custom-schemas/{schema_id}/versions")
  assert versions_resp.status_code == 200
  versions = versions_resp.json()
  assert versions["current_version"] == 2
  assert len(versions["versions"]) == 2

  diff_resp = client.get(
      f"/api/custom-schemas/{schema_id}/diff", params={"left": 1, "right": 2}
  )
  assert diff_resp.status_code == 200
  diff = diff_resp.json()
  assert diff["left_version"] == 1
  assert diff["right_version"] == 2
  assert isinstance(diff["changed"], list)

