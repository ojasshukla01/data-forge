# Migration and upgrades

Guidance for upgrading Data Forge and handling schema/config changes.

## Version upgrades

1. Check CHANGELOG.md for breaking changes.
2. Back up runs/, scenarios/, custom_schemas/ before upgrading.
3. Run tests after upgrade: make validate-all

## Config schema version

Run configs include config_schema_version. No automatic migration of scenario JSON files.

## Custom schema format

Validation runs on create/update. Lineage preserves snapshot when schema is deleted.

## Storage backend

Switching file to sqlite does not migrate data. Export manually if needed.
