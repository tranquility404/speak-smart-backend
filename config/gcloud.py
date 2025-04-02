import base64
import json
import os
from google.cloud import storage

service_account_b64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_SECRET")
service_account_path = "service-account-file.json"

if service_account_b64:
    decoded_bytes = base64.b64decode(service_account_b64)
    json_data = json.loads(decoded_bytes.decode("utf-8"))

    with open(service_account_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4)
    print(f"✅ Service account file saved: {service_account_path}")
else:
    print("❌ ERROR: GOOGLE_APPLICATION_CREDENTIALS_SECRET is not set.")

client = storage.Client()
bucket_name = "speak-smart"
bucket = client.get_bucket(bucket_name)
print("gcloud storage connection done")

def upload_to_gcs(file_path: str, file_name: str) -> str:
    blob = bucket.blob(file_name)
    blob.upload_from_filename(file_path)
    gcs_path = f"gs://{bucket_name}/{file_name}"
    return gcs_path

def upload_base64_to_gcs(base64_data: str, id: str, file_name: str) -> str:
    # decoded_data = base64.b64decode(base64_data)
    file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    temp_file_path = os.path.join(file, f"{file_name}-{id}.txt")
    try:
        with open(temp_file_path, "w") as f:
            f.write(base64_data)

        gcs_path = upload_to_gcs(temp_file_path, f"voice-analysis/{file_name}-{id}.txt")
    finally:
        print("analysis saved uploaded to cloud")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return gcs_path

def clean_up(id: str, file_path: str, data: str):
    analysis_report_url = upload_base64_to_gcs(data, id, "analysis_report")

    if os.path.exists(file_path):
        os.remove(file_path)
        print("Analysis complete. File deleted.")

    return analysis_report_url

def parse_gcs_url(gcs_url: str):
    if not gcs_url.startswith("gs://"):
        raise ValueError("Invalid GCS URL format")

    parts = gcs_url.replace("gs://", "").split("/", 1)
    if len(parts) != 2:
        raise ValueError("Invalid GCS URL format")

    return parts[0], parts[1]  # (bucket_name, file_path)

def read_gcs_file_as_string(gcs_url: str) -> str:
    bucket_name, file_path = parse_gcs_url(gcs_url)

    try:
        # bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        return blob.download_as_text()  # Read as text
    except Exception as e:
        raise RuntimeError(f"Error reading file from GCS: {str(e)}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # service_account_b64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_SECRET")
    # service_account_path = "service-account-file.json"
    #
    # if service_account_b64:
    #     decoded_bytes = base64.b64decode(service_account_b64)
    #     json_data = json.loads(decoded_bytes.decode("utf-8"))
    #
    #     with open(service_account_path, "w", encoding="utf-8") as f:
    #         json.dump(json_data, f, indent=4)
    #         print(f"✅ Service account file saved: {service_account_path}")
    # else:
    #     print("❌ ERROR: GOOGLE_APPLICATION_CREDENTIALS_SECRET is not set.")
    file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    file = os.path.join(file, "aman.wav")
    print(file)
    upload_to_gcs(file, "audio")

