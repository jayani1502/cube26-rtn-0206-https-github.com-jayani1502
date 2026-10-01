import os
import json
import streamlit as st
from PIL import Image
from pydantic import BaseModel, Field
from typing import List, Literal
from google import genai
from google.genai import types

# Page setup
st.set_page_config(page_title="Returns Audit Portal",
                   page_icon="📦", layout="wide")

# Structured schema for return evaluation


class ReturnInspectionResult(BaseModel):
    product_match: Literal["PASS", "FAIL", "UNCERTAIN"] = Field(
        description="PASS if item matches expected manifest, FAIL if incorrect item, UNCERTAIN if unclear."
    )
    completeness_check: Literal["PASS", "FAIL", "UNCERTAIN"] = Field(
        description="PASS if all accessories present, FAIL if missing components."
    )
    accessory_details: List[str] = Field(
        description="Status breakdown of expected accessories."
    )
    missing_items: List[str] = Field(
        description="List of any missing accessories or parts."
    )
    condition_grade: Literal[
        "New / Like New", "Used - Good", "Used - Fair", "Damaged", "Heavily Damaged", "UNCERTAIN"
    ] = Field(description="Item physical condition.")
    disposition_action: Literal["RESTOCK", "REFURBISH", "LIQUIDATE", "DISPOSE", "MANUAL_REVIEW"] = Field(
        description="Actionable disposition path."
    )
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Model decision confidence.")
    reasoning: str = Field(
        description="Brief explanation based on visual evidence.")


# Sample order manifest catalog
ORDERS_DB = {
    "ORD-101: Wireless Headphones": {
        "item_name": "ProSound Wireless Headphones",
        "accessories": ["Carrying Case", "USB-C Cable", "Audio Cable", "User Manual"]
    },
    "ORD-102: Smartwatch": {
        "item_name": "Aura Fit Smartwatch v2",
        "accessories": ["Charging Dock", "Silicone Band", "Quick Start Guide"]
    }
}

# Sidebar configuration
st.sidebar.title("Returns Audit System")
user_api_key = st.sidebar.text_input(
    "API Key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))
selected_order_id = st.sidebar.selectbox(
    "Select Order ID", list(ORDERS_DB.keys()))
current_order = ORDERS_DB[selected_order_id]

st.title("Automated Returns Disposition Agent")
st.caption(
    "Multimodal visual evaluation for order verification and disposition routing.")

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("Image Upload")
    uploaded_img = st.file_uploader("Upload returned product image", type=[
                                    "jpg", "jpeg", "png", "webp"])
    if uploaded_img:
        img_obj = Image.open(uploaded_img)
        st.image(img_obj, use_container_width=True)

with col_right:
    st.subheader("Evaluation Results")
    if uploaded_img and st.button("Evaluate Return", type="primary"):
        if not user_api_key:
            st.error("Please enter an API Key in the sidebar.")
        else:
            with st.spinner("Processing visual data against manifest..."):
                try:
                    client = genai.Client(api_key=user_api_key)
                    prompt_text = f"""
                    Evaluate this returned item against the expected order manifest.
                    Expected Product: {current_order['item_name']}
                    Expected Accessories: {', '.join(current_order['accessories'])}
                    
                    Instructions:
                    1. Check if the visual evidence matches the expected product.
                    2. Check for missing accessories listed in the manifest.
                    3. Grade the physical condition.
                    4. Select disposition: RESTOCK, REFURBISH, LIQUIDATE, DISPOSE, or MANUAL_REVIEW.
                    """

                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[prompt_text, img_obj],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=ReturnInspectionResult,
                            temperature=0.1,
                        ),
                    )

                    res = json.loads(response.text)

                    st.markdown(
                        f"### Recommended Action: **{res.get('disposition_action')}**")
                    st.write(f"**Confidence:** {res.get('confidence')}")
                    st.write(
                        f"**Match:** {res.get('product_match')} | **Completeness:** {res.get('completeness_check')} | **Condition:** {res.get('condition_grade')}")

                    st.write("**Accessories Status:**")
                    for item in res.get("accessory_details", []):
                        st.write(f"- {item}")

                    st.info(f"**Notes:** {res.get('reasoning')}")

                except Exception as ex:
                    st.error(f"Execution Error: {str(ex)}")
