
# Phase 0 — Infrastructure & Schemas

This bundle contains:
- `src/config/` — settings loader and YAML configs
- `src/infra/` — event bus, serializer, logging, secrets, scheduler
- `src/schemas/` — event/signal/order/risk dataclasses
- `tests/` — three quick self-tests
- `run_phase0_tests.py` — runner script

## How to run tests
```bash
python /mnt/data/run_phase0_tests.py
```

Expected output:
```
schema_roundtrip_ok
event_bus_ok
config_load_ok
ALL_PHASE0_OK
```
