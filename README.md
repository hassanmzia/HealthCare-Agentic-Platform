<p align="center">
  <img src="https://img.shields.io/badge/Platform-Healthcare%20AI-0077B6?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xOSAzSDVjLTEuMSAwLTIgLjktMiAydjE0YzAgMS4xLjkgMiAyIDJoMTRjMS4xIDAgMi0uOSAyLTJWNWMwLTEuMS0uOS0yLTItMnptLTEgMTFoLTR2NGgtMnYtNEg4di0yaDRWOGgydjRoNHYyeiIvPjwvc3ZnPg==&logoColor=white" alt="Healthcare AI Platform"/>
  <img src="https://img.shields.io/badge/Version-1.0.0-success?style=for-the-badge" alt="Version"/>
  <img src="https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge" alt="License"/>
  <img src="https://img.shields.io/badge/FHIR-R4-orange?style=for-the-badge" alt="FHIR R4"/>
  <img src="https://img.shields.io/badge/HIPAA-Compliant-green?style=for-the-badge" alt="HIPAA"/>
</p>

<h1 align="center">HealthCare Agentic Platform</h1>

<p align="center">
  <strong>AI-Powered Multi-Agent Clinical Decision Support System</strong><br/>
  <em>Empowering clinicians with intelligent, evidence-based diagnostic and treatment recommendations</em>
</p>

<p align="center">
  <a href="#-features">Features</a> &bull;
  <a href="#-architecture">Architecture</a> &bull;
  <a href="#-tech-stack">Tech Stack</a> &bull;
  <a href="#-getting-started">Getting Started</a> &bull;
  <a href="#-api-reference">API Reference</a> &bull;
  <a href="#-documentation">Documentation</a>
</p>

---

## Overview

The **HealthCare Agentic Platform** is a production-ready, multi-agent clinical decision support system that integrates AI-powered healthcare analytics with modern **FHIR (Fast Healthcare Interoperability Resources)** standards. The platform orchestrates **7+ specialized AI agents** to deliver comprehensive clinical assessments, enabling physicians to make faster, evidence-based decisions with full audit trails and compliance safeguards.

### The Problem

Clinicians face information overload — reviewing patient histories, lab results, imaging, and drug interactions across fragmented systems consumes valuable time that could be spent on patient care.

### Our Solution

An AI-augmented clinical workflow that aggregates patient data, runs multi-agent analysis across specialties (cardiology, radiology, oncology, pathology, etc.), and presents actionable recommendations through an intuitive clinician dashboard — all with physician-in-the-loop approval workflows.

---

## Key Features

### Clinical Intelligence
- **Multi-Agent Diagnostic Engine** — 7+ specialized AI agents collaborate to generate differential diagnoses with confidence scoring
- **Treatment Planning** — Evidence-based treatment recommendations with dosing guidance
- **Drug Safety Validation** — Automated drug interaction and allergy checking
- **Medical Coding** — Automatic ICD-10 and CPT code assignment
- **Clinical Guidelines RAG** — Retrieval-augmented generation from evidence-based medical literature

### Healthcare Interoperability
- **FHIR R4 Compliant** — Full bidirectional integration with HAPI FHIR server
- **EHR Integration Ready** — RESTful APIs for seamless EHR connectivity
- **HL7/FHIR Resources** — Patient, Observation, Condition, MedicationRequest, and more

### Physician Workflow
- **Clinician Dashboard** — Modern React-based interface with real-time data visualization
- **Physician Review Workflow** — Approve, modify, or reject AI recommendations
- **Clinical Documentation** — Auto-generated SOAP notes, progress notes, and discharge summaries
- **Digital Signatures** — Physician attestation and audit trail

### IoT & Real-Time Monitoring
- **Medical Device Integration** — Simulated IoT device data ingestion
- **Real-Time Vital Signs** — Continuous monitoring with configurable alert thresholds
- **Automated Alerts** — Critical value detection and notification system

### Security & Compliance
- **HIPAA-Ready Architecture** — Patient data segregation, encryption, and audit logging
- **Role-Based Access Control** — Admin, Doctor, Nurse, Technician, Receptionist, Viewer
- **JWT Authentication** — Secure token-based API access
- **SSL/TLS** — HTTPS support for all communications
- **Complete Audit Trail** — Every action logged with before/after state tracking

---

## Architecture

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CLINICIAN DASHBOARD (React/TypeScript)               │
│                         Port 3030 (HTTPS) / 2080 (HTTP)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Doctor   │ │ Patient  │ │ Vitals   │ │ Labs     │ │ Alerts &         │ │
│  │ Portal   │ │ List     │ │ Charts   │ │ Dashboard│ │ Analytics        │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ REST API (JWT Auth)
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DJANGO BACKEND (REST API)                               │
│                           Port 8000                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Patients │ │ Clinical │ │ Vitals   │ │ Labs     │ │ Medications      │ │
│  │ API      │ │ API      │ │ API      │ │ API      │ │ API              │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                                   │
│  │ Alerts   │ │ Analytics│ │ Users    │     Celery Workers (Async Tasks)   │
│  │ API      │ │ API      │ │ API      │                                    │
│  └──────────┘ └──────────┘ └──────────┘                                    │
└──────────┬──────────────────────┬───────────────────────────────────────────┘
           │                      │
           ▼                      ▼
┌─────────────────┐   ┌──────────────────────────────────────────────────────┐
│   PostgreSQL    │   │            AI ORCHESTRATOR (FastAPI/LangGraph)        │
│   + pgvector    │   │                     Port 8003                        │
│   Port 5432     │   │                                                      │
│                 │   │  ┌─────────────────────────────────────────────────┐  │
│   Redis         │   │  │           SUPERVISOR AGENT                     │  │
│   Port 6379     │   │  │      (Coordinates All Specialists)            │  │
│                 │   │  └──────────┬──────────────┬──────────────────────┘  │
└─────────────────┘   │            │              │                          │
                      │  ┌─────────▼───┐ ┌───────▼─────┐ ┌──────────────┐  │
                      │  │Diagnostician│ │ Treatment   │ │ Safety       │  │
                      │  │Agent        │ │ Agent       │ │ Agent        │  │
                      │  └─────────────┘ └─────────────┘ └──────────────┘  │
                      │  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │
                      │  │ Cardiology  │ │ Radiology   │ │ Pathology    │  │
                      │  │ Agent       │ │ Agent       │ │ Agent        │  │
                      │  └─────────────┘ └─────────────┘ └──────────────┘  │
                      │  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │
                      │  │ Oncology    │ │ Gastro      │ │ Coding       │  │
                      │  │ Agent       │ │ Agent       │ │ Agent        │  │
                      │  └─────────────┘ └─────────────┘ └──────────────┘  │
                      └──────────┬───────────────────────────────────────────┘
                                 │ Model Context Protocol (MCP)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MCP SERVERS (Tool Layer)                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐  │
│  │ FHIR Server  │ │ Labs Server  │ │ RAG Server   │ │ Pharmacy Server  │  │
│  │ Port 8005    │ │ Port 8006    │ │ Port 8007    │ │ Port 8008        │  │
│  └──────┬───────┘ └──────────────┘ └──────┬───────┘ └──────────────────┘  │
│         │                                  │                               │
│  ┌──────▼───────┐                  ┌───────▼──────┐                        │
│  │ FHIR Adapter │                  │ ChromaDB     │                        │
│  │ Port 8002    │                  │ Port 8009    │                        │
│  └──────┬───────┘                  └──────────────┘                        │
│         │                                                                  │
│  ┌──────▼───────┐                                                          │
│  │ HAPI FHIR   │                                                           │
│  │ Port 18090  │                                                           │
│  └──────────────┘                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      IoT SIMULATOR                                          │
│                      Port 8004                                              │
│  Generates realistic vital signs → Backend → Orchestrator → Alerts          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Data Ingestion     IoT Devices ──→ Backend API ──→ PostgreSQL + FHIR Server
2. AI Analysis        Orchestrator ←── MCP Servers (FHIR, Labs, RAG, Pharmacy)
3. Agent Workflow     Supervisor ──→ Specialists ──→ Consolidated Assessment
4. Physician Review   Dashboard ←── Assessment ──→ Approve / Modify / Reject
5. Order Execution    Approved Orders ──→ EHR Integration ──→ FHIR Writeback
6. Audit & Compliance All Actions ──→ Audit Log ──→ Compliance Reports
```

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| **Django 5.0** | REST API framework |
| **Django REST Framework** | API serialization & views |
| **PostgreSQL 16** | Primary database with pgvector |
| **Celery + Redis** | Async task processing |
| **JWT** | Authentication & authorization |

### AI / ML
| Technology | Purpose |
|---|---|
| **Claude (Anthropic)** | Primary LLM for clinical reasoning |
| **Ollama** | Local LLM alternative (DeepSeek-R1) |
| **LangGraph** | Multi-agent orchestration framework |
| **ChromaDB** | Vector database for RAG |
| **Sentence-Transformers** | Medical text embeddings |

### Frontend
| Technology | Purpose |
|---|---|
| **React 19** | UI component framework |
| **TypeScript 5.9** | Type-safe development |
| **Vite 7** | Build tooling |
| **TanStack Query** | Server state management |
| **Recharts** | Clinical data visualization |

### Infrastructure
| Technology | Purpose |
|---|---|
| **Docker Compose** | Container orchestration |
| **FastAPI** | AI orchestrator API |
| **HAPI FHIR** | FHIR R4 server |
| **Nginx** | Reverse proxy with SSL |
| **Model Context Protocol** | Agent-tool communication |

---

## Getting Started

### Prerequisites

- **Docker** & **Docker Compose** (v2.0+)
- **Anthropic API Key** (for Claude-powered AI agents)
- Minimum **8 GB RAM** recommended
- **Port availability**: 3030, 8000, 8002-8009, 18090

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/hassanmzia/HealthCare-Agentic-Platform.git
cd HealthCare-Agentic-Platform

# 2. Configure environment variables
#    Set your Anthropic API key in the orchestrator environment
#    Edit docker-compose.yml or create .env files as needed

# 3. Launch the entire platform
docker-compose up -d

# 4. Access the application
#    Dashboard:    https://localhost:3030
#    Backend API:  http://localhost:8000/api/v1/
#    FHIR Server:  http://localhost:18090
#    Orchestrator: http://localhost:8003
```

### Service Ports

| Service | Port | Description |
|---|---|---|
| **Clinician Dashboard** | `3030` (HTTPS) / `2080` (HTTP) | React frontend |
| **Django Backend** | `8000` | REST API |
| **FHIR Writeback Adapter** | `8002` | FHIR write operations |
| **AI Orchestrator** | `8003` | Multi-agent engine |
| **IoT Simulator** | `8004` | Device simulation |
| **MCP FHIR Server** | `8005` | FHIR read access |
| **MCP Labs Server** | `8006` | Lab results |
| **MCP RAG Server** | `8007` | Clinical guidelines |
| **MCP Pharmacy Server** | `8008` | Drug formulary |
| **ChromaDB** | `8009` | Vector database |
| **HAPI FHIR** | `18090` | FHIR R4 server |
| **PostgreSQL** | `5432` | Database |
| **Redis** | `6379` | Message broker |

### Manual Development Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# Orchestrator
cd orchestrator
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8003

# Frontend
cd frontend/clinician-dashboard
npm install
npm run dev
```

---

## API Reference

### Backend API (Port 8000)

#### Patients
```http
GET    /api/v1/patients/              # List all patients
POST   /api/v1/patients/              # Create patient
GET    /api/v1/patients/{id}/         # Get patient details
PUT    /api/v1/patients/{id}/         # Update patient
```

#### Clinical Assessments
```http
GET    /api/v1/clinical/assessments/          # List assessments
POST   /api/v1/clinical/assessments/          # Create assessment
GET    /api/v1/clinical/assessments/{id}/     # Get assessment detail
POST   /api/v1/clinical/assessments/{id}/review/  # Physician review
```

#### Vitals
```http
GET    /api/v1/vitals/                # List vital events
POST   /api/v1/vitals/               # Record vitals
GET    /api/v1/vitals/latest/         # Latest readings
```

#### Labs, Medications & Alerts
```http
GET    /api/v1/labs/                  # Lab results
GET    /api/v1/medications/           # Medications
GET    /api/v1/alerts/                # Clinical alerts
GET    /api/v1/analytics/             # Analytics data
```

#### Authentication
```http
POST   /api/v1/users/register/       # Register user
POST   /api/v1/users/login/          # Login (returns JWT)
POST   /api/v1/users/token/refresh/  # Refresh JWT token
```

### AI Orchestrator API (Port 8003)

```http
POST   /api/v1/assess                # Run comprehensive clinical assessment
GET    /api/v1/assess/{patient_id}   # Get assessment by patient
POST   /analyze-vitals               # Quick vitals analysis
GET    /api/v1/agents                # List available AI agents
GET    /api/v1/llm/status            # LLM provider status
POST   /api/v1/llm/switch            # Switch LLM provider
GET    /api/v1/mcp/status            # MCP server health check
```

---

## AI Agents

The platform orchestrates multiple specialized clinical AI agents:

| Agent | Specialty | Capabilities |
|---|---|---|
| **Supervisor** | Orchestration | Coordinates all specialist agents, manages workflow |
| **Diagnostician** | Diagnosis | Differential diagnoses with confidence scoring |
| **Treatment** | Treatment Planning | Evidence-based treatment recommendations |
| **Safety** | Drug Safety | Drug interactions, allergies, contraindications |
| **Coding** | Medical Coding | ICD-10 diagnosis codes, CPT procedure codes |
| **Cardiology** | Cardiovascular | ECG interpretation, cardiac risk assessment |
| **Radiology** | Medical Imaging | Imaging analysis and interpretation |
| **Pathology** | Laboratory | Lab result interpretation and trending |
| **Oncology** | Cancer Care | Tumor markers, staging, screening protocols |
| **Gastroenterology** | GI Medicine | GI procedure analysis and recommendations |

### Agent Workflow

```
Patient Data Input
       │
       ▼
┌──────────────┐
│  Supervisor  │ ── Determines which specialists to invoke
└──────┬───────┘
       │
       ├──→ Diagnostician ──→ Differential Diagnoses
       ├──→ Treatment     ──→ Treatment Plans
       ├──→ Safety        ──→ Drug/Allergy Checks
       ├──→ Coding        ──→ ICD-10 / CPT Codes
       ├──→ Cardiology    ──→ Cardiac Analysis (if applicable)
       ├──→ Radiology     ──→ Imaging Review (if applicable)
       ├──→ Pathology     ──→ Lab Interpretation (if applicable)
       └──→ Oncology      ──→ Cancer Screening (if applicable)
              │
              ▼
    Consolidated Assessment
       │
       ▼
    Physician Review & Approval
```

---

## Database Schema

### Core Entities

```
Patient ─────── Encounter ─────── ClinicalAssessment
   │                │                      │
   ├── VitalsEvent  ├── Diagnosis          ├── PhysicianReview
   ├── LabResult    ├── ClinicalNote       ├── AssessmentAuditLog
   ├── Medication   ├── CarePlan           └── ClinicalDocument
   └── Alert        └── EHROrder
```

### Key Models
- **Patient**: MRN, demographics, blood type, emergency contact
- **ClinicalAssessment**: AI-generated findings, diagnoses, treatments, confidence scores
- **PhysicianReview**: Approval workflow with digital signature
- **AssessmentAuditLog**: Before/after state with compliance tracking

---

## Project Structure

```
HealthCare-Agentic-Platform/
├── backend/                    # Django REST API + EHR core
│   ├── alerts/                 # Clinical alerts & notifications
│   ├── analytics/              # Health analytics & reporting
│   ├── clinical/               # AI assessments, diagnoses, care plans
│   ├── devices/                # IoT device management
│   ├── labs/                   # Laboratory results
│   ├── medications/            # Pharmacy & medication orders
│   ├── patients/               # Patient demographics & records
│   ├── recommendations/        # AI recommendation storage
│   ├── users/                  # Authentication & user management
│   ├── vitals/                 # Vital signs & monitoring
│   └── config/                 # Django settings & routing
├── orchestrator/               # Multi-agent clinical AI system
│   ├── agents/                 # 10 specialized AI agents
│   ├── graph/                  # LangGraph workflow orchestration
│   ├── llm/                    # LLM abstraction (Claude/Ollama)
│   ├── fhir/                   # FHIR data utilities
│   └── tools/                  # MCP client integration
├── mcp/                        # Model Context Protocol servers
│   ├── servers/                # FHIR, Labs, RAG, Pharmacy servers
│   └── tool_adapters/          # FHIR writeback adapter
├── frontend/
│   └── clinician-dashboard/    # React + TypeScript UI
│       ├── src/components/     # 20+ React components
│       ├── src/context/        # Auth & state management
│       └── src/lib/            # API clients & utilities
├── iot-simulator/              # Medical device simulator
├── docker/                     # Database initialization
├── ssl/                        # SSL certificates
└── docker-compose.yml          # Full stack orchestration
```

---

## Environment Configuration

### Required Environment Variables

| Variable | Service | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Orchestrator | Claude API key |
| `LLM_PROVIDER` | Orchestrator | `claude` or `ollama` |
| `CLAUDE_MODEL` | Orchestrator | Model ID (e.g., `claude-sonnet-4-20250514`) |
| `DB_HOST` | Backend | PostgreSQL host |
| `DB_PORT` | Backend | PostgreSQL port |
| `DB_NAME` | Backend | Database name |
| `CELERY_BROKER_URL` | Backend | Redis broker URL |

---

## Security & Compliance

| Feature | Description |
|---|---|
| **Authentication** | JWT-based with token refresh |
| **Authorization** | Role-based access control (6 roles) |
| **Audit Trail** | Complete action logging with before/after states |
| **Data Encryption** | SSL/TLS for data in transit |
| **HIPAA Readiness** | Patient data segregation and audit compliance |
| **Digital Signatures** | Physician attestation for assessments |

---

## Documentation

Additional documentation is available in the `docs/` directory:

| Document | Description |
|---|---|
| [`docs/ARCHITECTURE.drawio`](docs/ARCHITECTURE.drawio) | Interactive architecture diagram (open with draw.io) |
| [`docs/MARKETING.md`](docs/MARKETING.md) | Product overview and marketing materials |
| [`docs/PROJECT_OVERVIEW.html`](docs/PROJECT_OVERVIEW.html) | Single-page project overview (printable to PDF) |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is proprietary software. All rights reserved.

---

<p align="center">
  <strong>Built with advanced AI for better healthcare outcomes</strong><br/>
  <em>HealthCare Agentic Platform &copy; 2025</em>
</p>
