# Enterprise Returns Audit AI Agent

## Overview
An enterprise-grade multimodal AI Returns Audit system built for reverse logistics automation. The platform ingests return manifests and customer photos to perform itemized identity verification, completeness checks, condition grading, and actionable disposition decisioning (restock, refurbish, liquidate, dispose, pending_review).

## Core Capabilities
- Multimodal Vision Reasoning: Evaluates single or multi-view product images using Gemini 2.5 Flash.
- Ground-Truth Manifest Auto-Loading: Resolves photo references dynamically from data/returns_sample.csv.
- Pydantic Schema Enforcement: Guarantees 100% structured JSON outputs with confidence scoring and check-level breakdowns.
- SQLite Persistent Audit Trail: Logs every inspection attempt, model confidence, and raw evidence payload locally into returns_audit.db.
- Financial Risk Analytics: Calculates restocking fees and estimated revenue recovery rates per return disposition.

## Directory Structure
submissions/jayani1502/
├── config.py           # Infrastructure settings and logging configuration
├── schema.py           # Pydantic evidence contract and response schemas
├── database.py         # SQLite persistence layer and audit trail logging
├── evaluator.py        # Gemini multimodal reasoning engine and multi-view resolver
├── batch_runner.py     # Automated dataset evaluation script
├── app.py              # Streamlit enterprise audit dashboard
├── requirements.txt    # Application dependencies
├── ARCHITECTURE.md     # Architectural design and evidence contract specs
└── README.md           # System documentation and reproduction guide

## Installation & Setup

1. Install Dependencies:
   pip install -r submissions/jayani1502/requirements.txt

2. Environment Configuration:
   Set your Gemini API key in environment variables or enter it directly in the Streamlit UI sidebar:
   $env:GEMINI_API_KEY="your_gemini_api_key_here"

3. Execute Local Dashboard:
   python -m streamlit run submissions/jayani1502/app.py

## Assumptions & Operational Rules
- If image evidence is blurry, dark, or ambiguous, the engine defaults recommended_disposition to pending_review and condition_classification to uncertain.
- Returns manifests are read from data/returns_sample.csv with visual evidence located in fixtures/returns/.