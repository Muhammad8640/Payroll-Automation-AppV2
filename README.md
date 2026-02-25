# Payroll Automation & Analytics MVP

FastAPI + SQLAlchemy backend implementing payroll automation requirements:
- JWT admin auth
- Rep and lead CRUD
- Timestamped lead status history
- Configurable default bonus rules and rep overrides
- Pay period management
- Payroll run engine (`POST /payroll/run/{pay_period_id}`)
- Payroll summary and CSV export
- Conversion analytics report

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Core endpoints
- `POST /auth/register`
- `POST /auth/login`
- `POST/GET/PUT/DELETE /reps`
- `POST/GET /leads`
- `POST /statuses`
- `POST /leads/status`
- `POST /bonus-rules`
- `POST /bonus-overrides`
- `POST /pay-periods`
- `POST /payroll/run/{pay_period_id}`
- `GET /payroll/{pay_period_id}`
- `GET /payroll/{pay_period_id}/export`
- `GET /reports/conversion`

## AWS Deployment Notes
- Use RDS Postgres and set `DATABASE_URL`
- Deploy API container to EC2 via Docker/Nginx reverse proxy
- Terminate TLS with Let's Encrypt certificates on Nginx
- CI/CD can build/push image and trigger EC2 deploy via GitHub Actions SSH
