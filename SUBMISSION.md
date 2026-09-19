# Darukaa.Earth Submission

## 1. Project Overview

Darukaa.Earth is an environmental intelligence workspace for managing carbon and biodiversity projects, mapping monitoring sites, and reviewing performance trends. It provides a practical path from synthetic demonstration data to future remote-sensing and field-data integrations.

The application is delivered as a monorepo:

- `frontend/`: React, TypeScript, and Vite user interface.
- `backend/`: FastAPI API, Pydantic contracts, SQLAlchemy persistence, authorization, and spatial calculations.
- PostgreSQL/PostGIS: persistent identity, project, site, geometry, and analytics data.

## 2. Implemented Requirements

### Authentication and users

- User registration and login with JWT authentication.
- Passwords stored as bcrypt hashes rather than plaintext.
- Persistent browser session with authenticated API requests.
- Protected administrator routes.
- User identity is returned by the backend and refreshed through `GET /api/auth/me`.
- The dashboard displays the authenticated user's actual name rather than a hardcoded role label.

### Project management

- Create, list, search, filter, view, and delete projects.
- Project status, project type, description, location, and date metadata.
- Empty, loading, and API error states in the frontend.

### Spatial monitoring

- Site polygons stored as PostGIS `POLYGON` geometry in EPSG:4326.
- GeoJSON API response for map rendering.
- Shapely validation for closed, non-empty, and non-self-intersecting polygons.
- Backend area calculation using EPSG:6933 before conversion to hectares.
- Mapbox rendering and polygon drawing when a Mapbox token is configured.
- Token-free fallback canvas for local demonstrations.

### Analytics

- Site-level carbon stock and sequestration metrics.
- Biodiversity index, vegetation cover, and project health metrics.
- Dated analytics records and trend visualizations.
- Dashboard aggregates for projects, sites, area, carbon, and biodiversity.

### Quality and usability

- Responsive layout for desktop and mobile screens.
- Accessible form controls and clear navigation.
- API data is used for user identity, projects, sites, and analytics; frontend area values are not trusted for calculations.
- Database schema migrations and a synthetic seed dataset are included.

## 3. Architecture

```text
React + TypeScript + Vite
          |
       REST / JWT
          v
FastAPI + Pydantic + SQLAlchemy
          |
          v
PostgreSQL + PostGIS

React --> Mapbox GL JS + Mapbox Draw
React --> Chart.js
```

The main API resources are:

- Auth: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- Projects: `GET/POST /api/projects`, `GET/PUT/DELETE /api/projects/{id}`
- Sites: `GET/POST /api/projects/{id}/sites`, `GET/PUT/DELETE /api/sites/{id}`, `GET /api/sites/geojson`
- Analytics: `GET/POST /api/sites/{id}/analytics`
- Dashboard: `GET /api/dashboard/summary`

FastAPI Swagger documentation is available at `/docs` when the backend is running.

## 4. Local Setup

### Prerequisites

- Node.js 20 or newer
- Python 3.12 or newer
- PostgreSQL with the PostGIS extension

### Installation and startup

```powershell
Copy-Item .env.example .env
psql -d darukaa -c "CREATE EXTENSION IF NOT EXISTS postgis;"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m alembic -c backend\alembic.ini upgrade head
python backend\seed.py
npm install --prefix frontend
npm run dev --prefix frontend
uvicorn app.main:app --app-dir backend --reload
```

Configure `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `CORS_ORIGINS` in the environment. Configure `VITE_API_URL` and, optionally, `VITE_MAPBOX_TOKEN` for the frontend.

## 5. Demonstration Walkthrough

1. Open the frontend and register a new account with a full name, email, and password.
2. Confirm that the overview greeting and account profile show the registered name.
3. Open **Projects** and create a project with its type and location.
4. Open the project detail view and draw a site polygon on the map.
5. Save the site and confirm that its area and coordinates are calculated by the backend.
6. Open the site analytics view to review metric history and trends.
7. Return to the overview to review portfolio totals and spatial coverage.

A seeded demonstration account is available for local use:

- Email: `admin@darukaa.earth`
- Password: `demo-password-2026`

Change this password before using the application in a shared environment.

## 6. Validation

Frontend validation commands:

```powershell
npm run lint --prefix frontend
npm run typecheck --prefix frontend
npm run build --prefix frontend
npm run test --prefix frontend
```

Backend validation commands:

```powershell
python -m ruff check backend
python -m black --check backend
pytest backend
```

The frontend typecheck, lint, test suite, and production build were run successfully after the user identity display fix. The production build completes with a non-blocking bundle-size warning caused by the current Mapbox and Chart.js dependency bundle.

## 7. Deployment

The repository includes deployment configuration for both application layers:

- `vercel.json` builds and serves the frontend from `frontend/dist`.
- `render.yaml` runs the FastAPI backend, applies Alembic migrations at service startup, and exposes `/health` for health checks.

For a one-time low-cost demonstration, use a Render free web service with a free external PostgreSQL provider that supports PostGIS, such as a suitable Supabase project. Configure the database URL, backend secrets, CORS origins, and frontend API URL. The Render configuration avoids the paid pre-deploy hook by running migrations at startup. Mapbox tiles and polygon editing require `VITE_MAPBOX_TOKEN`; the application remains usable with the fallback spatial canvas when no token is supplied.

## 8. Data and Limitations

The included dataset is synthetic and fictional. It is intended for demonstration and does not represent verified environmental measurements or real project claims. A production implementation should add audited permissions, multi-tenancy, verified satellite or field ingestion, background processing, export workflows, object storage, and field-data synchronization.

## 9. Submission Checklist

- [x] Frontend application included.
- [x] Backend API included.
- [x] PostgreSQL/PostGIS schema and migration included.
- [x] Seed data and local setup instructions included.
- [x] Authentication and protected routes included.
- [x] Project, site, map, and analytics workflows included.
- [x] API documentation available through FastAPI Swagger.
- [x] Frontend lint, typecheck, build, and tests configured.
- [x] Backend lint, formatting, and tests configured.
- [x] Vercel and Render deployment descriptors included.
