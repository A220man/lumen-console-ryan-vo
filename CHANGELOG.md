# Changelog

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

### Added
- Full CLI implementation with all skill management commands:
  - `lumen login` — Authenticate via OIDC (Keycloak)
  - `lumen add` — Install skill from GitHub repository
  - `lumen find` — Search skills by query and owner
  - `lumen install` — Restore skills from lock file (npm ci equivalent)
  - `lumen update` — Update installed skills
  - `lumen list` — List installed skills
  - `lumen logout` — Clear stored credentials
  - `lumen status` — Show authentication status
- CLI stores tokens securely in ~/.config/lumen/config.json
- Added httpx dependency for CLI HTTP client

### Fixed
- Fixed pytest-asyncio compatibility in test configuration
- Updated pyproject.toml to properly configure pytest-asyncio

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-14

### Added
- Initial project scaffold with FastAPI backend and React+TypeScript frontend
- Docker Compose with PostgreSQL, Keycloak, backend, frontend
- Project skeleton passes preflight checks
