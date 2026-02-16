# Artist Portfolio — FastAPI

Portfolio website with public gallery and admin panel for managing works.

## Stack

- **Backend**: FastAPI + Jinja2 templates
- **DB**: PostgreSQL + SQLAlchemy 2.0 (async) + Alembic
- **Auth**: Signed cookie sessions (itsdangerous)
- **Storage**: S3-compatible bucket (presigned uploads)
- **CDN**: Public URLs via `cdn.<domain>`

## Quick Start (Local Dev)

```bash
# 1. Start Postgres (and optional MinIO for local S3)
docker compose up -d

# 2. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Copy env file and adjust
cp .env.example .env

# 4. Run migrations
alembic upgrade head

# 5. Seed demo data (optional)
python -m scripts.seed

# 6. Start server
uvicorn app.main:app --reload
```

Open:
- Portfolio: http://localhost:8000
- Admin: http://localhost:8000/admin/login
- API docs: http://localhost:8000/docs

Default admin credentials (from `.env`):
- Email: `admin@example.com`
- Password: `changeme123`

## Project Structure

```
portfolio/
├── app/
│   ├── api/            # API routes (public works, admin CRUD)
│   ├── admin/          # Admin HTML page routes
│   ├── core/           # Config, DB, security
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # S3 presign service
│   ├── static/
│   │   ├── css/        # main.css (portfolio), admin.css
│   │   └── js/         # portfolio.js, admin_upload.js
│   └── templates/
│       ├── public/     # Portfolio Jinja2 templates
│       └── admin/      # Admin Jinja2 templates
├── alembic/            # Database migrations
├── scripts/            # Seed script
├── docker-compose.yml  # Local Postgres + MinIO
├── Dockerfile          # Production image
└── requirements.txt
```

## API Endpoints

### Public
- `GET /api/works` — list works (filter: `?tag=...`)
- `GET /api/works/{slug}` — work detail

### Admin (auth required)
- `POST /api/admin/works` — create work
- `PATCH /api/admin/works/{id}` — update work
- `DELETE /api/admin/works/{id}` — delete work
- `POST /api/admin/uploads/presign` — get presigned upload URL

### Pages
- `GET /` — portfolio home
- `GET /work/{slug}` — work detail page
- `GET /admin/login` — admin login
- `GET /admin/` — admin dashboard

## Upload Flow

1. Admin frontend calls `POST /api/admin/uploads/presign` with filename & content_type
2. Gets back `upload_url` (presigned S3 PUT) + `public_url` (CDN link)
3. Frontend uploads file directly to S3 via PUT
4. Saves `public_url` as `cover_url` or in `gallery_urls` via CRUD API

## Deploy

3 components:
1. **FastAPI** — Railway / Fly.io / any Docker host
2. **PostgreSQL** — Railway Postgres / Supabase / RDS
3. **Bucket + CDN** — Backblaze B2 + Cloudflare CDN / AWS S3 + CloudFront

Set all env vars from `.env.example` in your deployment platform.
