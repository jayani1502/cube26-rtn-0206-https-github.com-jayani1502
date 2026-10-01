import os
import pandas as pd
from evaluator import load_ground_truth_dataset, inspect_return_item


def run_batch_evaluation(api_key: str, max_samples: int = 5):
    df = load_ground_truth_dataset()
    if df.empty:
        print("Dataset not found.")
        return

    results = []
    print(f"Running batch evaluation on first {max_samples} records...")

    for idx, row in df.head(max_samples).iterrows():
        record = row.to_dict()
        try:
            res = inspect_return_item(api_key, record, image_input=None)
            results.append({
                "record_id": record.get("record_id"),
                "predicted": res.get("recommended_disposition"),
                "ground_truth": record.get("operator_disposition")
            })
            print(f"[{record.get('record_id')}] Pred: {res.get('recommended_disposition')} | GT: {record.get('operator_disposition')}")
        except Exception as e:
            print(f"[{record.get('record_id')}] Failed: {str(e)}")

    return pd.DataFrame(results)


if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        run_batch_evaluation(key)
    else:
        print("GEMINI_API_KEY environment variable not set.")
