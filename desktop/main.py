import base64
import hashlib
import json
import os
import platform
import sqlite3
import subprocess
import sys
import uuid
import webbrowser
from datetime import datetime

import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
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

if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS
    DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA', os.path.dirname(sys.executable))), 'MobileStore')
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = BUNDLE_DIR

os.makedirs(DATA_DIR, exist_ok=True)

if BUNDLE_DIR not in sys.path:
    sys.path.insert(0, BUNDLE_DIR)
from app_window import StoreMainWindow
from updater import check_updates_async, CURRENT_APP_VERSION

API_BASE_URL = os.environ.get("API_BASE_URL", "http://34.175.186.221/api")
WEB_URL = os.environ.get("WEB_URL", "http://34.175.186.221/")
DB_FILE = os.path.join(DATA_DIR, "local_storage.db")
PUBLIC_KEY_PATH = os.path.join(BUNDLE_DIR, "keys", "public_key.pem")
LICENSE_FILE = os.path.join(DATA_DIR, "license.json")

_cached_hwid = None


def get_hardware_id():
    """
    Generates an immutable hardware fingerprint bound to this physical machine:
    Combines (Motherboard Serial + CPU Processor ID + System UUID + MAC Address).
    """
    global _cached_hwid
    if _cached_hwid:
        return _cached_hwid

    parts = []
    if platform.system() == "Windows":
        try:
            ps_cmd = "(Get-CimInstance Win32_BaseBoard).SerialNumber; (Get-CimInstance Win32_Processor).ProcessorId; (Get-CimInstance Win32_ComputerSystemProduct).UUID"
            result = subprocess.check_output(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                timeout=4
            ).strip().splitlines()
            for line in result:
                line_clean = line.strip()
                if line_clean and line_clean.lower() != "none" and "to be filled" not in line_clean.lower():
                    parts.append(line_clean)
        except Exception:
            pass

    parts.append(str(uuid.getnode()))
    combined = "|".join(parts)
    _cached_hwid = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return _cached_hwid


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

        # Set Window Icon
        icon_path = os.path.join(BUNDLE_DIR, "app_icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(BUNDLE_DIR, "app_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout()
        layout.setSpacing(12)

        header = QLabel("Mobile-Store Management System")
        header.setStyleSheet("font-size: 16px; font-weight: bold; text-align: center;")
        layout.addWidget(header)

        hw_display = QLabel(f"Machine Hardware ID: {self.hardware_id[:16]}...")
        hw_display.setStyleSheet("color: #777; font-size: 11px;")
        layout.addWidget(hw_display)

        server_display = QLabel(f"Connected Server: {API_BASE_URL}")
        server_display.setStyleSheet("color: #0ea5e9; font-size: 11px; font-weight: 500;")
        layout.addWidget(server_display)

        form_layout = QFormLayout()
        self.username_input = QLineEdit()
        saved_username = self.get_session("username") or ""
        self.username_input.setText(saved_username)
        self.username_input.setPlaceholderText("Username")
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setText("")
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)
        layout.addLayout(form_layout)

        self.login_button = QPushButton("Login & Verify License")
        self.login_button.setStyleSheet("padding: 8px; font-weight: bold; background-color: #0d6efd; color: white;")
        self.login_button.clicked.connect(self.login_and_verify)
        layout.addWidget(self.login_button)

        # Bottom Bar: Status + Check for Updates
        bottom_bar = QHBoxLayout()
        self.verify_status = QLabel("Status: Ready")
        bottom_bar.addWidget(self.verify_status)
        bottom_bar.addStretch()

        self.update_btn = QPushButton("🚀 Check Updates")
        self.update_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #0284c7;
                border: 1px solid #38bdf8;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #e0f2fe;
            }
        """)
        self.update_btn.clicked.connect(lambda: check_updates_async(
            api_base_url=API_BASE_URL,
            current_version=CURRENT_APP_VERSION,
            manual=True,
            parent=self
        ))
        bottom_bar.addWidget(self.update_btn)
        layout.addLayout(bottom_bar)

        self.setLayout(layout)

        # Silent update check 2 seconds after login window opens
        QTimer.singleShot(2500, lambda: check_updates_async(
            api_base_url=API_BASE_URL,
            current_version=CURRENT_APP_VERSION,
            manual=False,
            parent=self
        ))

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
                err_msg = "Invalid username or password."
                try:
                    err_data = response.json()
                    if isinstance(err_data, dict) and "detail" in err_data:
                        err_msg = err_data["detail"]
                except Exception:
                    pass

                self.verify_status.setText(f"Status: {err_msg}")
                QMessageBox.warning(
                    self,
                    "Login Failed",
                    f"{err_msg}\n\nServer: {API_BASE_URL}\n(Make sure your account exists on this specific server)"
                )
                return

            data = response.json()
            access_token = data.get("access")
            refresh_token = data.get("refresh")
            self.save_session("access_token", access_token)
            self.save_session("refresh_token", refresh_token)
            self.save_session("username", username)
            self.save_session("password", password)

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
                        db_path=DB_FILE,
                        refresh_token=refresh_token
                    )
                    self.main_window.show()
                    self.main_window.raise_()
                    self.main_window.activateWindow()
                    self.hide()
                    return
                else:
                    self.verify_status.setText("الحالة: لا توجد رخصة نشطة")
                    QMessageBox.warning(self, "غير مصرح", "لا توجد رخصة سارية مرتبطة بهذا الحساب أو الجهاز.")
            else:
                try:
                    err_payload = verify_response.json()
                    err_msg = err_payload.get("detail") or err_payload.get("error") or "فشل التحقق من صلاحية الترخيص."
                except Exception:
                    err_msg = f"خطأ من السيرفر: رمز الاستجابة {verify_response.status_code}"
                self.verify_status.setText(f"الحالة: {err_msg}")
                QMessageBox.critical(self, "فشل التحقق من الترخيص", err_msg)
                return

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
                    access_token=self.get_session("access_token"),
                    license_info={
                        "license_key": payload.get("license_key", "Offline License"),
                        "expires_at": payload.get("expires_at", "2027-09-18"),
                        "hardware_id": self.hardware_id,
                    },
                    is_offline=True,
                    api_base_url=API_BASE_URL,
                    db_path=DB_FILE,
                    refresh_token=self.get_session("refresh_token")
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
    if platform.system() == "Windows":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mobilestore.pos.desktop.1.0")
        except Exception:
            pass

    app = QApplication(sys.argv)

    icon_path = os.path.join(BUNDLE_DIR, "app_icon.png")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(BUNDLE_DIR, "app_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MobileStoreApp()
    window.show()
    window.raise_()
    window.activateWindow()
    sys.exit(app.exec())

