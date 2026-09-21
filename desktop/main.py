import base64
import hashlib
import json
import os
import sqlite3
import sys
import uuid
import webbrowser
from datetime import datetime

import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from app_window import StoreMainWindow

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000/api")
WEB_URL = os.environ.get("WEB_URL", "http://localhost:5173/")
DB_FILE = os.path.join(BASE_DIR, "local_storage.db")
PUBLIC_KEY_PATH = os.path.join(BASE_DIR, "keys", "public_key.pem")
LICENSE_FILE = os.path.join(BASE_DIR, "license.json")


def get_hardware_id():
    """Generates a consistent unique hardware ID based on the machine's MAC address."""
    mac = uuid.getnode()
    return hashlib.sha256(str(mac).encode()).hexdigest()


def get_machine_cipher():
    """Derives a deterministic AES encryption key bound to this physical machine."""
    salt = b"mobilestore_desktop_machine_salt_2026"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(get_hardware_id().encode()))
    return Fernet(key)


cipher = get_machine_cipher()


def verify_rsa_signature(payload_dict, signature_b64):
    """Verifies RSA SHA-256 signature using the embedded public key."""
    if not os.path.exists(PUBLIC_KEY_PATH):
        return False, "Public key not found"
    try:
        with open(PUBLIC_KEY_PATH, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
        payload_bytes = json.dumps(payload_dict, sort_keys=True).encode("utf-8")
        signature = base64.b64decode(signature_b64)
        public_key.verify(
            signature,
            payload_bytes,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True, "Valid signature"
    except Exception as e:
        return False, str(e)





class MobileStoreApp(QWidget):
    def __init__(self):
        super().__init__()
        self.hardware_id = get_hardware_id()
        self.init_db()
        self.init_ui()

    def init_db(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS session (key TEXT PRIMARY KEY, value TEXT)"
        )
        self.conn.commit()

    def save_session(self, key, value):
        encrypted_value = cipher.encrypt(value.encode()).decode()
        self.cursor.execute(
            "INSERT OR REPLACE INTO session (key, value) VALUES (?, ?)",
            (key, encrypted_value),
        )
        self.conn.commit()

    def get_session(self, key):
        self.cursor.execute("SELECT value FROM session WHERE key = ?", (key,))
        row = self.cursor.fetchone()
        if row:
            try:
                return cipher.decrypt(row[0].encode()).decode()
            except Exception:
                return None
        return None

    def init_ui(self):
        self.setWindowTitle("Mobile Store - Login & Verification")
        self.setMinimumWidth(420)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        header = QLabel("Mobile-Store Management System")
        header.setStyleSheet("font-size: 16px; font-weight: bold; text-align: center;")
        layout.addWidget(header)

        hw_display = QLabel(f"Machine Hardware ID: {self.hardware_id[:16]}...")
        hw_display.setStyleSheet("color: #777; font-size: 11px;")
        layout.addWidget(hw_display)

        form_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.username_input.setText("admin")
        self.username_input.setPlaceholderText("Username")
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setText("admin123")
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)
        layout.addLayout(form_layout)

        self.login_button = QPushButton("Login & Verify License")
        self.login_button.setStyleSheet("padding: 8px; font-weight: bold; background-color: #0d6efd; color: white;")
        self.login_button.clicked.connect(self.login_and_verify)
        layout.addWidget(self.login_button)

        self.verify_status = QLabel("Status: Ready")
        layout.addWidget(self.verify_status)

        self.setLayout(layout)

    def verify_offline_token(self):
        """Attempts to validate an offline token or license.json locally."""
        # Check local DB session first
        cached_payload_str = self.get_session("offline_token_payload")
        cached_sig = self.get_session("offline_token_signature")

        if cached_payload_str and cached_sig:
            try:
                payload = json.loads(cached_payload_str)
                is_valid, _ = verify_rsa_signature(payload, cached_sig)
                if is_valid and payload.get("hardware_id") == self.hardware_id:
                    exp_date = datetime.fromisoformat(payload["expires_at"])
                    if exp_date > datetime.now():
                        return True, payload
            except Exception:
                pass

        # Check license.json fallback
        if os.path.exists(LICENSE_FILE):
            try:
                with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                payload = data.get("payload", {})
                sig = data.get("signature", "")
                is_valid, _ = verify_rsa_signature(payload, sig)
                if is_valid:
                    # check hw hash if specified
                    target_hw = payload.get("hardware_hash", "")
                    if not target_hw or target_hw.upper() == self.hardware_id.upper():
                        exp_date_str = payload.get("expires_at", "")
                        if exp_date_str:
                            exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d")
                            if exp_date > datetime.now():
                                return True, payload
            except Exception:
                pass

        return False, None

    def login_and_verify(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Validation Error", "Please enter username and password")
            return

        self.verify_status.setText("Connecting to server...")
        try:
            # 1. Online Login
            response = requests.post(
                f"{API_BASE_URL}/auth/login/",
                json={"username": username, "password": password},
                timeout=4,
            )

            if response.status_code != 200:
                self.verify_status.setText("Status: Invalid credentials")
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
                return

            data = response.json()
            access_token = data.get("access")
            refresh_token = data.get("refresh")
            self.save_session("access_token", access_token)
            self.save_session("username", username)

            # 2. Online License Check
            headers = {"Authorization": f"Bearer {access_token}"}
            verify_response = requests.get(
                f"{API_BASE_URL}/license/check/",
                params={"hardware_id": self.hardware_id},
                headers=headers,
                timeout=4,
            )

            if verify_response.status_code == 200:
                licenses = verify_response.json()
                if licenses:
                    lic = licenses[0]
                    # 3. Request signed offline token for 7-day Grace Period
                    try:
                        token_resp = requests.post(
                            f"{API_BASE_URL}/license/offline-token/",
                            json={"hardware_id": self.hardware_id},
                            headers=headers,
                            timeout=4,
                        )
                        if token_resp.status_code == 200:
                            token_data = token_resp.json()
                            self.save_session("offline_token_payload", json.dumps(token_data["payload"]))
                            self.save_session("offline_token_signature", token_data["signature"])
                    except Exception as token_err:
                        print("Could not update offline token:", token_err)

                    self.save_session("license_key", lic["license_key"])
                    self.save_session("expires_at", lic["end_date"])

                    self.verify_status.setText("Status: License Active (Online)")
                    self.main_window = StoreMainWindow(
                        username=username,
                        access_token=access_token,
                        license_info={
                            "license_key": lic["license_key"],
                            "expires_at": lic["end_date"],
                            "hardware_id": self.hardware_id,
                        },
                        is_offline=False,
                        api_base_url=API_BASE_URL,
                        db_path=DB_FILE
                    )
                    self.main_window.show()
                    self.main_window.raise_()
                    self.main_window.activateWindow()
                    self.hide()
                    return
                else:
                    self.verify_status.setText("Status: No active license found")
                    QMessageBox.warning(self, "Unauthorized", "No active license associated with this account or machine.")
            else:
                self.verify_status.setText("Status: License Check Error")

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as net_err:
            # Network error -> Trigger Offline Mode Validation
            self.verify_status.setText("Server offline. Checking local license...")
            valid_offline, payload = self.verify_offline_token()

            if valid_offline and payload:
                QMessageBox.information(
                    self,
                    "Offline Mode",
                    "Server unreachable. Valid offline license token found! Starting in Offline Mode (Grace Period Active).",
                )
                self.main_window = StoreMainWindow(
                    username=username,
                    access_token=None,
                    license_info={
                        "license_key": payload.get("license_key", "Offline License"),
                        "expires_at": payload.get("expires_at", "2027-09-18"),
                        "hardware_id": self.hardware_id,
                    },
                    is_offline=True,
                    api_base_url=API_BASE_URL,
                    db_path=DB_FILE
                )
                self.main_window.show()
                self.main_window.raise_()
                self.main_window.activateWindow()
                self.hide()
            else:
                self.verify_status.setText("Status: Offline check failed")
                QMessageBox.critical(
                    self,
                    "License Check Failed",
                    f"Could not reach server and no valid offline license was found on this machine.\n\nError: {net_err}",
                )

        except Exception as e:
            self.verify_status.setText(f"Status: Error - {str(e)}")
            QMessageBox.critical(self, "Unexpected Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MobileStoreApp()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())

