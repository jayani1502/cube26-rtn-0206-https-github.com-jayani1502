import os
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from PIL import Image
from google import genai
from google.genai import types

from config import CSV_PATH, MODEL_NAME, TEMPERATURE, logger
from schema import FullReturnsInspectionContract
from database import save_audit_entry


def load_ground_truth_dataset() -> pd.DataFrame:
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    return pd.DataFrame()


def resolve_photo_paths(photo_refs_str: str) -> List[str]:
    """Parses semicolon-separated photo paths and resolves absolute local paths."""
    if not isinstance(photo_refs_str, str) or not photo_refs_str.strip():
        return []

    resolved_paths = []
    relative_paths = [p.strip()
                      for p in photo_refs_str.split(";") if p.strip()]

    for rel_path in relative_paths:
        possible_locations = [
            rel_path,
            os.path.join("data", rel_path),
            os.path.join(os.getcwd(), rel_path)
        ]
        for loc in possible_locations:
            if os.path.exists(loc):
                resolved_paths.append(loc)
                break
    return resolved_paths


def inspect_return_item(
    api_key: str,
    manifest_record: Dict[str, Any],
    images: Optional[List[Image.Image]] = None
) -> Dict[str, Any]:

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an enterprise AI Returns Inspection Agent evaluating returned merchandise against operational manifests.

    EXPECTED MANIFEST DATA:
    - Record ID: {manifest_record.get('record_id', 'N/A')}
    - Order ID: {manifest_record.get('order_id', 'N/A')}
    - Expected SKU: {manifest_record.get('ordered_sku', 'N/A')}
    - Expected ASIN: {manifest_record.get('ordered_asin', 'N/A')}
    - Expected Parts List: {manifest_record.get('parts_list', 'N/A')}

    RULES & TAXONOMY:
    1. Product Identity: PASS (matches SKU), FAIL (wrong item), UNCERTAIN (ambiguous).
    2. Completeness: Cross-check observed parts against expected parts list. Identify missing components explicitly.
    3. Condition Classification: strictly one of [factory_sealed, opened_unused, signs_of_use, damaged, uncertain].
    4. Recommended Disposition: strictly one of [restock, refurbish, liquidate, dispose, pending_review].
    5. UNCERTAINTY HANDLING: If visual evidence across all images is blurry, dark, obstructed, or ambiguous, default disposition to 'pending_review' and condition to 'uncertain'. NEVER GUESS.
    """

    content_payload = [prompt]
    if images:
        content_payload.extend(images)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=content_payload,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FullReturnsInspectionContract,
            temperature=TEMPERATURE,
        ),
    )

    result = json.loads(response.text)

    # Financial risk estimation logic
    disposition = result.get("recommended_disposition", "pending_review")
    financial_impact = {
        "restock": {"fee_percent": 0, "recovery_rate": 1.0},
        "refurbish": {"fee_percent": 15, "recovery_rate": 0.8},
        "liquidate": {"fee_percent": 50, "recovery_rate": 0.3},
        "dispose": {"fee_percent": 100, "recovery_rate": 0.0},
        "pending_review": {"fee_percent": 0, "recovery_rate": 0.0}
    }.get(disposition, {"fee_percent": 0, "recovery_rate": 0.0})

    result["financial_impact"] = financial_impact

    save_audit_entry(
        record_id=manifest_record.get('record_id', 'UNKNOWN'),
        order_id=manifest_record.get('order_id', 'UNKNOWN'),
        sku=manifest_record.get('ordered_sku', 'UNKNOWN'),
        predicted_disposition=result.get('recommended_disposition'),
        ground_truth=str(manifest_record.get('operator_disposition', 'N/A')),
        confidence=result.get('overall_confidence'),
        identity_verdict=result.get('product_identity_verdict'),
        completeness_verdict=result.get('completeness_verdict'),
        raw_payload=result
    )

    return result
