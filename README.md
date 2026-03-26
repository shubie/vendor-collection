# Vendor Collection Portal

Vendor onboarding fullstack app built with Flask, SQLite, and filesystem uploads.

## Run with Docker (recommended)

```bash
docker compose up -d --build
```

App URLs:

- Vendor form: http://localhost:5000/
- Admin list: http://localhost:5000/admin/applications

## Persistent SQLite and uploads

The container uses named Docker volumes so data is not recreated on restart:

- `vendor_instance` → `/app/instance` (contains `vendor_portal.db`)
- `vendor_uploads` → `/app/uploads` (uploaded files)

As long as these volumes exist, your SQLite data and uploaded files remain persistent across:

- container restarts
- image rebuilds
- `docker compose down` / `up` cycles

## Useful commands

```bash
docker compose logs -f
docker compose stop
docker compose start
docker compose down
```

To remove all persisted data intentionally:

```bash
docker compose down -v
```
