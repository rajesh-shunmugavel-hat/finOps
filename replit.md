# FinOps Cloud Cost Optimizer

## Overview
A comprehensive FinOps (Financial Operations) platform prototype for AWS cost optimization. The platform integrates a React frontend, FastAPI backend, PostgreSQL database, and OpenAI-powered AI analysis to provide visibility into AWS costs and actionable optimization recommendations.

### Goals
- Provide real-time visibility into AWS cloud spending
- Generate AI-powered cost optimization recommendations
- Serve three user personas: DevOps engineers, Finance teams, and CTOs
- Display comprehensive CloudWatch metrics for all AWS services

### Current State
Fully functional prototype with:
- Dashboard showing total spend, optimization potential, active services, and departments
- Service drilldown pages with detailed CloudWatch metrics
- AI analysis integration (requires OPENAI_API_KEY for full functionality)
- Reports history and executive summary generation
- Department-level cost tracking

## Architecture

### Backend (FastAPI)
- **Location**: `/backend/`
- **Framework**: FastAPI with SQLAlchemy ORM
- **Port**: 8000
- **Entry Point**: `backend/app/main.py`

#### API Endpoints
- `GET /api/dashboard` - Main dashboard data with cost summaries
- `GET /api/services` - List all AWS services
- `GET /api/services/{name}` - Service details with CloudWatch metrics
- `GET /api/services/{name}/resources` - Resources for a specific service
- `GET /api/services/{name}/metrics` - CloudWatch metrics for a service
- `GET /api/reports` - AI analysis reports history
- `GET /api/reports/{id}` - Single report details
- `POST /api/reports/generate` - Generate new AI analysis
- `GET /api/departments` - Department cost breakdown

#### Key Files
- `backend/app/main.py` - FastAPI application and CORS configuration
- `backend/app/database.py` - PostgreSQL connection setup
- `backend/app/models/models.py` - SQLAlchemy models
- `backend/app/services/ai_service.py` - OpenAI/LangChain integration
- `backend/app/routes/` - API route handlers
- `backend/seed_data.py` - Database seeding script

### Frontend (React + Vite)
- **Location**: `/frontend/`
- **Framework**: React 18 with TypeScript, Vite 7
- **Styling**: Tailwind CSS v3
- **Port**: 5000
- **Charts**: Recharts

#### Key Pages
- `/` - Main dashboard with cost overview
- `/services/:name` - Service drilldown with CloudWatch metrics
- `/reports` - AI analysis reports history
- `/reports/:id` - Individual report details
- `/departments` - Department cost breakdown

#### Key Files
- `frontend/src/pages/Dashboard.tsx` - Main dashboard
- `frontend/src/pages/ServiceDrilldown.tsx` - Service details
- `frontend/src/pages/Reports.tsx` - Reports listing
- `frontend/src/pages/ReportDetail.tsx` - Report details
- `frontend/src/pages/Departments.tsx` - Department breakdown
- `frontend/src/lib/api.ts` - API client

### Database (PostgreSQL)
Uses Replit's built-in PostgreSQL database with the following tables:
- `services` - AWS service definitions (EC2, RDS, S3, Lambda)
- `resources` - Individual AWS resources
- `cloudwatch_metrics` - Time-series CloudWatch metrics
- `monthly_costs` - Historical cost data by month
- `departments` - Cost center definitions
- `ai_reports` - AI-generated analysis reports
- `recommendations` - Individual cost optimization recommendations

### CloudWatch Metrics by Service
- **EC2**: CPUUtilization, NetworkIn, NetworkOut, DiskReadOps, DiskWriteOps
- **RDS**: CPUUtilization, DatabaseConnections, FreeStorageSpace, ReadLatency, WriteLatency
- **S3**: NumberOfObjects, BucketSizeBytes, GetRequests, PutRequests
- **Lambda**: Invocations, Duration, Errors, Throttles

## Recent Changes
- December 2024: Initial prototype built with React + FastAPI architecture
- Fixed Tailwind CSS v4 compatibility issues by downgrading to v3
- Implemented comprehensive CloudWatch metrics for all AWS services
- Added AI-powered cost justification analysis with OpenAI/LangChain

## User Preferences
- FastAPI backend (not Express.js)
- No authentication required
- Comprehensive CloudWatch metrics for each service type
- Multi-persona reporting (DevOps, Finance, CTO views)


