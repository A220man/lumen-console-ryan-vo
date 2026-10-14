# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

skill-install

## Roadmap

### project-skeleton — Project skeleton with FastAPI backend and React frontend

Status: done

Acceptance:
- Backend FastAPI app runs with health endpoint
- Frontend Vite+React+TS builds successfully
- Docker compose starts backend, frontend, Keycloak, PostgreSQL
- Preflight passes all required file checks

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/security.py`, `backend/app/core/auth.py`, `backend/app/models/__init__.py`, `backend/app/schemas.py`, `backend/app/api/__init__.py`, `backend/app/api/health.py`, `backend/app/api/auth.py`, `backend/app/api/skills.py`, `backend/app/api/lock.py`, `backend/app/services/skill_service.py`, `backend/app/cli.py`, `backend/requirements.txt`, `backend/Dockerfile`, `backend/tests/conftest.py`, `backend/tests/test_health.py`, `backend/tests/test_auth.py`, `backend/tests/test_skills.py`, `frontend/package.json`, `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/index.css`, `frontend/src/types/index.ts`, `frontend/src/api/client.ts`, `frontend/src/hooks/useAuth.tsx`, `frontend/src/components/Navbar.tsx`, `frontend/src/components/LoadingSpinner.tsx`, `frontend/src/components/ProtectedRoute.tsx`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/CallbackPage.tsx`, `frontend/src/pages/DashboardPage.tsx`, `frontend/src/pages/SkillsPage.tsx`, `frontend/src/pages/SkillDetailPage.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/test-setup.ts`, `frontend/src/vite-env.d.ts`, `frontend/src/App.test.tsx`, `compose.yaml`, `.env.example`, `README.md`, `LICENSE`, `CHANGELOG.md`, `pyproject.toml`, `.gitignore`, `portfolio.json`, `.github/workflows/ci.yml`

Tests: `backend/tests/test_health.py`, `backend/tests/test_auth.py`, `backend/tests/test_skills.py`, `frontend/src/App.test.tsx`

### skill-install — Skill installation from GitHub repositories

Status: in_progress

Acceptance:
- CLI command to install skill from GitHub URL
- Shallow clone with sparse checkout for large repos
- Skill metadata parsed from SKILL.md frontmatter
- Skills stored in SQLite with version tracking

Implementation: `backend/app/services/skill_service.py`, `backend/app/api/skills.py`

Tests: `backend/tests/test_skills.py`

### skill-search — Skill search and discovery

Status: planned

Acceptance:
- Search skills by name, owner, keywords
- List installed skills
- API endpoints for search and listing

Implementation: `backend/app/api/skills.py`

### skill-lock — Lock file and reproducible install (skills install/ci)

Status: planned

Acceptance:
- skills-lock.json generated on install
- skills install restores from lock file
- skills ci strict mode for CI pipelines
- Idempotent installs with --force option

Implementation: `backend/app/api/lock.py`, `backend/app/services/skill_service.py`

### auth-oidc — OIDC authentication with Keycloak

Status: planned

Acceptance:
- Keycloak realm import for development
- Backend validates JWT tokens with PKCE
- Frontend login/logout flow
- Role-based access (viewer, operator, admin)

Implementation: `backend/app/core/auth.py`, `backend/app/api/auth.py`, `frontend/src/hooks/useAuth.tsx`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/CallbackPage.tsx`

Tests: `backend/tests/test_auth.py`

### skill-update — Skill update and cache invalidation

Status: planned

Acceptance:
- Check for skill updates from source
- Update installed skills
- Cache busting on source change detection

Implementation: `backend/app/services/skill_service.py`, `backend/app/api/skills.py`

