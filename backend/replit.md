# FinOps Cloud Cost Optimizer

## Overview
A FastAPI-based backend service for AWS cost visibility and optimization. The platform provides manual data fetching from AWS Cost Explorer and CloudWatch, stores historical data in PostgreSQL, and generates AI-powered cost optimization reports using OpenAI.

## Workflow (Manual Two-Step Process)
1. **Step 1: Fetch AWS Data** - `POST /api/sync/all`
   - Fetches Cost Explorer data and CloudWatch metrics from AWS
   - Stores all data in PostgreSQL database

2. **Step 2: Generate AI Report** - `POST /api/reports/generate`
   - OpenAI analyzes the stored cost/metrics data
   - Generates optimization recommendations
   - Stores report in database

## Project Structure
```
├── main.py                 # FastAPI application entry point
├── src/
│   ├── config.py          # Environment configuration
│   ├── database.py        # SQLAlchemy database setup
│   ├── models.py          # Database models (AwsCost, Metric, Resource, Department, Report)
│   ├── schemas.py         # Pydantic schemas for API validation
│   ├── aws_service.py     # AWS Cost Explorer and CloudWatch integration
│   ├── openai_service.py  # OpenAI integration for AI reports
│   └── routers/
│       ├── health.py      # Health check endpoint
│       ├── dashboard.py   # Cost dashboard endpoint
│       ├── services.py    # AWS services endpoints
│       ├── departments.py # Department cost breakdown
│       ├── reports.py     # AI report generation
│       └── sync.py        # Manual data sync endpoints
```

## API Endpoints

### Core Endpoints
- `GET /` - API info with workflow steps
- `GET /health` - Health check with DB and AWS status
- `GET /docs` - Swagger UI documentation

### Step 1: Data Sync (Manual)
- `POST /api/sync/costs` - Fetch and store AWS cost data
- `POST /api/sync/all` - Fetch all data (costs + department breakdown)

### Step 2: AI Reports (Manual)
- `POST /api/reports/generate` - Generate AI optimization report
- `GET /api/reports` - List past AI reports
- `GET /api/reports/{id}` - Report details
- `GET /api/reports/{id}/full` - Full report with raw AI response
- `DELETE /api/reports/{id}` - Delete a report

### Dashboard & Analytics
- `GET /api/dashboard` - Cost summaries, top services, departments
- `GET /api/services` - List all services with costs
- `GET /api/services/{name}` - Service details
- `GET /api/services/{name}/resources` - Resources with cost attribution
- `GET /api/services/{name}/metrics` - CloudWatch metrics (time-series)
- `POST /api/services/{name}/sync-metrics` - Trigger metrics sync

### Departments
- `GET /api/departments` - Department-level cost breakdown
- `GET /api/departments/{name}` - Department details
- `POST /api/departments/sync` - Sync department costs
- `PUT /api/departments/{name}/budget` - Set department budget

## Environment Variables Required
- `DATABASE_URL` - PostgreSQL connection string (auto-configured by Replit)
- `AWS_ACCESS_KEY_ID` - AWS IAM access key (read-only permissions)
- `AWS_SECRET_ACCESS_KEY` - AWS IAM secret key
- `AWS_REGION` - AWS region (default: us-east-1)
- `OPENAI_API_KEY` - OpenAI API key for AI reports

## AWS IAM Permissions Required
The IAM user needs read-only access to:
- Cost Explorer (`ce:GetCostAndUsage`)
- CloudWatch (`cloudwatch:GetMetricStatistics`)
- Resource Groups (optional, for resource discovery)

## Running the Application
```bash
python main.py
```
The server runs on port 5000 with Swagger docs at `/docs`.
