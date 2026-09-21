import os
import json
import base64
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

# Target machine Hardware ID
TARGET_HW_HASH = "1BB72884116F64DBA54DE303C2F6315AAC5E9444830E6387690D2AF0568BB82E"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_PATH = os.path.join(BASE_DIR, "keys", "private_key.pem")
OUTPUT_PATH = os.path.join(BASE_DIR, "..", "desktop", "license.json")

if not os.path.exists(KEY_PATH):
    raise FileNotFoundError(f"Server private key not found at: {KEY_PATH}")

payload = {
    "hardware_hash": TARGET_HW_HASH.strip(),
    "client_name": "Store-Branch-01",
    "expires_at": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
}

with open(KEY_PATH, "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
signature = private_key.sign(
    payload_bytes,
    padding.PKCS1v15(),
    hashes.SHA256()
)

license_data = {
    "payload": payload,
    "signature": base64.b64encode(signature).decode("utf-8")
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(license_data, f, indent=4)

print(f"License file created successfully at: {OUTPUT_PATH}")
