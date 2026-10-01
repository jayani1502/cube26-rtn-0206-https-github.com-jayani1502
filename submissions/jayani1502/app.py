import os
import json
import pandas as pd
import streamlit as st
from PIL import Image

from database import init_db, fetch_audit_logs
from evaluator import load_ground_truth_dataset, resolve_photo_paths, inspect_return_item

st.set_page_config(
    page_title="Enterprise Returns Audit AI Agent | CUBE",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()
df_manifest = load_ground_truth_dataset()

st.sidebar.title("🛡️ Enterprise Audit Portal")
st.sidebar.caption("CUBE Round 2 - Track 04: Returns Manager")
api_key = st.sidebar.text_input(
    "Gemini API Key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))

st.sidebar.markdown("---")
st.sidebar.subheader("System Infrastructure")
st.sidebar.success("Database: SQLite Connected (`returns_audit.db`)")
st.sidebar.info(f"Manifest Benchmark Records: {len(df_manifest)}")

tab_audit, tab_batch, tab_dataset, tab_db = st.tabs([
    "🔍 Real-Time Unit Audit",
    "📈 Automated Batch Benchmark",
    "📊 Dataset Explorer",
    "📜 SQLite Audit Trail"
])

with tab_audit:
    st.title("Automated Returns Inspection Engine")
    st.caption(
        "Auto-fetching local dataset images, multimodal multi-view synthesis, and automated disposition decisioning.")

    if not df_manifest.empty:
        col_select, col_info = st.columns([1, 2])
        with col_select:
            selected_record_id = st.selectbox(
                "Select Record ID from `data/returns_sample.csv`:",
                df_manifest["record_id"].unique()
            )

        record_row = df_manifest[df_manifest["record_id"]
                                 == selected_record_id].iloc[0].to_dict()

        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            st.subheader("📋 Manifest Reference Metadata")
            st.json({
                "record_id": record_row.get("record_id"),
                "order_id": record_row.get("order_id"),
                "ordered_sku": record_row.get("ordered_sku"),
                "ordered_asin": record_row.get("ordered_asin"),
                "expected_parts": record_row.get("parts_list"),
                "operator_ground_truth": record_row.get("operator_disposition")
            })

            st.subheader("🖼️ Visual Evidence (Auto-Loaded from CSV)")
            photo_refs = str(record_row.get("photo_refs", ""))
            resolved_paths = resolve_photo_paths(photo_refs)
            loaded_images = []

            if resolved_paths:
                st.success(
                    f"Found {len(resolved_paths)} image(s) from `photo_refs`")
                img_cols = st.columns(min(len(resolved_paths), 3))
                for idx, path in enumerate(resolved_paths):
                    try:
                        img = Image.open(path)
                        loaded_images.append(img)
                        with img_cols[idx % 3]:
                            st.image(img, caption=os.path.basename(
                                path), use_container_width=True)
                    except Exception as e:
                        st.warning(f"Could not load image {path}: {str(e)}")
            else:
                st.info(
                    "No local images found in `photo_refs`. Upload manual image below:")
                uploaded_file = st.file_uploader("Upload return image", type=[
                                                 "jpg", "jpeg", "png", "webp"])
                if uploaded_file:
                    img = Image.open(uploaded_file)
                    loaded_images.append(img)
                    st.image(img, caption="Manual Upload", width=300)

        with col_right:
            st.subheader("⚡ Automated Inspection Decision")
            if st.button("Run Multi-View Pipeline Inspection", type="primary", use_container_width=True):
                if not api_key:
                    st.error(
                        "Please enter a valid Gemini API Key in the sidebar.")
                else:
                    with st.spinner("Analyzing multi-view visual evidence against manifest..."):
                        try:
                            output = inspect_return_item(
                                api_key, record_row, loaded_images)

                            disp = str(output.get(
                                "recommended_disposition", "")).upper()
                            gt = str(record_row.get(
                                "operator_disposition", "")).upper()

                            c1, c2, c3 = st.columns(3)
                            c1.metric("Predicted Disposition", disp)
                            c2.metric("Ground Truth Label", gt)
                            c3.metric("Status", "✅ MATCH" if disp ==
                                      gt else "⚠️ DEVIATION")

                            st.markdown("---")
                            st.write(
                                f"**Overall Confidence:** `{output.get('overall_confidence')}`")
                            st.write(
                                f"**Identity Verdict:** `{output.get('product_identity_verdict')}` | **Completeness:** `{output.get('completeness_verdict')}`")
                            st.write(
                                f"**Condition Grade:** `{output.get('condition_classification')}`")

                            st.subheader(
                                "📦 Components & Accessories Breakdown")
                            st.write(
                                "**Observed Parts:**", ", ".join(output.get("observed_components", [])))
                            if output.get("missing_components"):
                                st.warning(
                                    f"**Missing Parts:** {', '.join(output.get('missing_components'))}")
                            else:
                                st.success(
                                    "All expected components accounted for.")

                            st.subheader("💰 Financial Risk & Recovery Metrics")
                            f_impact = output.get("financial_impact", {})
                            fc1, fc2 = st.columns(2)
                            fc1.metric("Restocking / Depreciation Fee",
                                       f"{f_impact.get('fee_percent')}%")
                            fc2.metric("Estimated Revenue Recovery Rate",
                                       f"{int(f_impact.get('recovery_rate', 0) * 100)}%")

                            with st.expander("Downloadable Audit JSON Payload"):
                                st.json(output)
                                st.download_button(
                                    label="📥 Download JSON Audit Certificate",
                                    data=json.dumps(output, indent=2),
                                    file_name=f"audit_{selected_record_id}.json",
                                    mime="application/json"
                                )

                        except Exception as ex:
                            st.error(f"Execution Error: {str(ex)}")

with tab_batch:
    st.title("Automated Batch Evaluation Matrix")
    st.caption("Executes automated evaluation loops across the full benchmark dataset and evaluates precision against ground truth.")

    batch_size = st.slider("Select sample size for batch execution:",
                           min_value=1, max_value=min(25, len(df_manifest)), value=5)

    if st.button(f"Run Batch Evaluation on First {batch_size} Records", type="secondary"):
        if not api_key:
            st.error("Please enter a valid Gemini API Key in the sidebar.")
        else:
            progress_bar = st.progress(0)
            batch_results = []

            for idx, row in df_manifest.head(batch_size).iterrows():
                rec = row.to_dict()
                paths = resolve_photo_paths(str(rec.get("photo_refs", "")))
                imgs = [Image.open(p) for p in paths if os.path.exists(p)]

                try:
                    res = inspect_return_item(api_key, rec, imgs)
                    pred = str(res.get("recommended_disposition", "")).lower()
                    gt_val = str(rec.get("operator_disposition", "")).lower()

                    batch_results.append({
                        "record_id": rec.get("record_id"),
                        "ordered_sku": rec.get("ordered_sku"),
                        "predicted_disposition": pred,
                        "ground_truth": gt_val,
                        "match": "MATCH" if pred == gt_val else "DEVIATION",
                        "confidence": res.get("overall_confidence")
                    })
                except Exception as e:
                    batch_results.append({
                        "record_id": rec.get("record_id"),
                        "ordered_sku": rec.get("ordered_sku"),
                        "predicted_disposition": "ERROR",
                        "ground_truth": str(rec.get("operator_disposition", "")).lower(),
                        "match": "ERROR",
                        "confidence": "NONE"
                    })

                progress_bar.progress((idx + 1) / batch_size)

            df_batch = pd.DataFrame(batch_results)
            st.subheader("Batch Evaluation Results")
            st.dataframe(df_batch, use_container_width=True)

            matches = len(df_batch[df_batch["match"] == "MATCH"])
            accuracy = (matches / len(df_batch)) * \
                100 if len(df_batch) > 0 else 0
            st.metric("Batch Accuracy Score", f"{accuracy:.1f}%")

with tab_dataset:
    st.title("Ground-Truth Dataset Explorer (`data/returns_sample.csv`)")
    if not df_manifest.empty:
        st.dataframe(df_manifest, use_container_width=True)

with tab_db:
    st.title("SQLite Audit Trail (`returns_audit.db`)")
    logs = fetch_audit_logs()
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True)
    else:
        st.info("No audit entries logged yet. Execute an inspection in Tab 1 or Tab 2.")
