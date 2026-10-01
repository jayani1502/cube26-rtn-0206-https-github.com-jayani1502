# Architectural Specification & Evidence Contract

## System Architecture

1. Presentation Layer (app.py)
   - Streamlit multi-tab enterprise interface.
   - Tab 1: Real-time multi-view return inspection and auto-loaded photo gallery.
   - Tab 2: Automated batch evaluation runner and performance metrics.
   - Tab 3: Dataset manifest explorer (data/returns_sample.csv).
   - Tab 4: SQLite persistent audit log viewer.

2. Multimodal AI Engine (evaluator.py)
   - Powered by Gemini 2.5 Flash via google-genai SDK.
   - Multi-view visual synthesis: Combines multiple image angles into a single prompt payload.
   - Schema enforcement using Pydantic structured output constraints (response_schema).

3. Data Persistence & Audit Layer (database.py)
   - SQLite relational database (returns_audit.db).
   - Immutable audit logging for compliance, decision tracking, and model verification.

## Data Flow Pipeline

[Manifest Record CSV] --> [Photo Path Resolver] --> [PIL Image Loader]
                                                         |
                                                         v
[SQLite Audit DB] <-- [Pydantic Contract Parser] <-- [Gemini 2.5 Flash API]

## Evidence Contract Schema
The inspection engine strictly outputs data conforming to FullReturnsInspectionContract:
- record_id (str)
- product_identity_verdict (PASS | FAIL | UNCERTAIN)
- completeness_verdict (PASS | FAIL | UNCERTAIN)
- observed_components (List[str])
- missing_components (List[str])
- condition_classification (factory_sealed | opened_unused | signs_of_use | damaged | uncertain)
- recommended_disposition (restock | refurbish | liquidate | dispose | pending_review)
- overall_confidence (HIGH | MEDIUM | LOW)
- checks (List of individual check verdicts and visual rationale)