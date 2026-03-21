# Pack authoring guide

Create and register a new domain pack so it appears in the UI and can be used with `--pack <id>`.

## Scaffold a new pack

From the project root:

```bash
python -m data_forge.cli scaffold-pack my_domain
```

This creates:

- `schemas/my_domain.sql` — DDL (tables, columns)
- `rules/my_domain.yaml` — rules (uniqueness, ranges, etc.)
- `examples/scenarios/my_domain_quick_start.json` — sample scenario
- `docs/pack_my_domain.md` — stub doc

## Implement the pack

1. **Schema** (`schemas/<pack_id>.sql` or `.json`): Define tables, primary keys, foreign keys. Use types your engine supports (e.g. BIGINT, VARCHAR, TIMESTAMP).
2. **Rules** (`rules/<pack_id>.yaml`): Add validation/generation rules. See existing packs in `rules/` for format.
3. **Test**: Run `data-forge generate --pack <pack_id> --scale 100` (or use the UI).

## Register the pack

Edit `src/data_forge/domain_packs/__init__.py`:

1. In `list_packs()`, add a tuple: `("<pack_id>", "Short description"),`
2. In `PACK_METADATA`, add an entry with `name`, `category`, `key_entities`, `recommended_use_cases`, `supported_features`, and optionally `supports_event_streams`, `simulation_event_types`, `benchmark_relevance`.

## Surface in the frontend

Packs are listed via `GET /api/domain-packs`. The Templates page uses `GET /api/templates`, which merges built-in packs (excluding hidden) with user templates (custom schemas promoted as templates). Users can add templates from packs or Schema Studio, edit user templates in Schema Studio, and hide built-in packs they don't need. No extra frontend registration is needed once the pack is in `list_packs()` and loadable via `get_pack(pack_id)`.

## Example

See `saas_billing` or `ecommerce` in `schemas/`, `rules/`, and `domain_packs/__init__.py` for a full example.
