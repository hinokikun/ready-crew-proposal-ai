# OSS License Inventory

## Scope

This document lists direct dependencies used by Ready Crew Proposal AI. It is intended for production release preparation and should be reviewed against the installed package metadata before external distribution.

## Backend Dependencies

| Package | Version Constraint | License | Usage |
|---|---|---|---|
| FastAPI | `0.115.12` | MIT | Backend API framework |
| Uvicorn | `0.34.0` | BSD-3-Clause | ASGI server |
| OpenAI Python SDK | `>=1.99.0,<2.0.0` | Apache-2.0 | OpenAI API client |
| python-dotenv | `>=1.0.1,<2.0.0` | BSD-3-Clause | Local environment loading |
| Pydantic | `1.10.24` | MIT | Request and response models |
| python-pptx | `>=1.0.2,<2.0.0` | MIT | PowerPoint generation |
| ReportLab | `>=4.2.5,<5.0.0` | BSD-style | PDF generation |
| SQLAlchemy | `>=2.0.36,<3.0.0` | MIT | Database ORM |
| Alembic | `>=1.13.3,<2.0.0` | MIT | Database migration tooling |
| psycopg[binary] | `>=3.2.3,<4.0.0` | LGPL-3.0-only | PostgreSQL driver |
| pytest | `>=8.3.5,<9.0.0` | MIT | Backend test runner |
| httpx | `>=0.28.1,<1.0.0` | BSD-3-Clause | HTTP client and test client support |

## Frontend Dependencies

| Package | Version Constraint | License | Usage |
|---|---|---|---|
| Next.js | `^15.1.3` | MIT | Frontend framework |
| React | `^19.0.0` | MIT | UI rendering |
| React DOM | `^19.0.0` | MIT | Browser DOM renderer |
| lucide-react | `^0.468.0` | ISC | Icons |

## Frontend Development Dependencies

| Package | Version Constraint | License | Usage |
|---|---|---|---|
| @playwright/test | `^1.51.1` | Apache-2.0 | E2E tests |
| @types/node | `^22.10.5` | MIT | TypeScript Node types |
| @types/react | `^19.0.2` | MIT | TypeScript React types |
| @types/react-dom | `^19.0.2` | MIT | TypeScript React DOM types |
| TypeScript | `^5.7.2` | Apache-2.0 | Type checking |

## Operational Notes

- This inventory covers direct dependencies in `backend/requirements.txt` and `frontend/package.json`.
- Transitive dependencies should be reviewed with the package manager lock file and production artifact before commercial distribution.
- The project license is stored in [../../LICENSE](../../LICENSE).
- Do not include third-party API keys, generated customer data, or private deployment settings in license materials.
