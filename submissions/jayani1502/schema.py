from pydantic import BaseModel, Field
from typing import List, Literal


class IndividualCheck(BaseModel):
    check_key: Literal["identity_match", "completeness_check", "condition_grade", "fraud_risk"] = Field(
        description="Key identifier for the check."
    )
    verdict: Literal["PASS", "FAIL", "UNCERTAIN"] = Field(
        description="Verdict based strictly on visual evidence."
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Calibrated confidence score between 0.0 and 1.0."
    )
    visual_evidence_summary: str = Field(
        description="Factual summary of visual findings."
    )


class FullReturnsInspectionContract(BaseModel):
    record_id: str
    order_id: str
    ordered_sku: str
    product_identity_verdict: Literal["PASS", "FAIL", "UNCERTAIN"]
    completeness_verdict: Literal["PASS", "FAIL", "UNCERTAIN"]
    observed_components: List[str]
    missing_components: List[str]
    condition_classification: Literal["factory_sealed",
                                      "opened_unused", "signs_of_use", "damaged", "uncertain"]
    recommended_disposition: Literal["restock",
                                     "refurbish", "liquidate", "dispose", "pending_review"]
    overall_confidence: Literal["HIGH", "MEDIUM", "LOW"]
    checks: List[IndividualCheck]
    audit_notes: str
