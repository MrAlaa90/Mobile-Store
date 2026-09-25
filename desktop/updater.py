import os
import sys
import tempfile
import subprocess
import webbrowser
import requests
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QMessageBox,
    QWidget,
    QFrame,
)

CURRENT_APP_VERSION = "1.1.0"


class DownloadWorker(QThread):
    progress = pyqtSignal(int, int)  # bytes_downloaded, total_bytes
    finished = pyqtSignal(str)       # saved_file_path
    error = pyqtSignal(str)          # error_message

    def __init__(self, download_url, filename="MobileStore-Setup.exe", parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.filename = filename
        self._is_cancelled = False

    def run(self):
        try:
            target_dir = tempfile.gettempdir()
            target_path = os.path.join(target_dir, self.filename)

            resp = requests.get(self.download_url, stream=True, timeout=15)
            if resp.status_code != 200:
                self.error.emit(f"Server responded with status {resp.status_code}")
                return

            total_size = int(resp.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 65536  # 64 KB

            with open(target_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if self._is_cancelled:
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total_size)

            self.finished.emit(target_path)
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self._is_cancelled = True


class UpdateDialog(QDialog):
    """
    Modern In-App Updater Dialog for Mobile-Store Desktop.
    Shows release notes, streams download with live progress, and launches silent/standard installer.
    """
    def __init__(self, update_info, current_version=CURRENT_APP_VERSION, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.current_version = current_version
        self.download_worker = None
        self.downloaded_installer_path = None

        self.setWindowTitle("تحديث برنامج Mobile-Store (Software Update)")
        self.resize(520, 440)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: 'Segoe UI', Tahoma, sans-serif;
            }
            QLabel {
                color: #f8fafc;
            }
            QTextEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                line-height: 1.5;
            }
            QProgressBar {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                height: 22px;
            }
            QProgressBar::chunk {
                background: linear-gradient(135deg, #0284c7, #38bdf8);
                border-radius: 5px;
            }
        """)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header with Logo & Title
        header_layout = QHBoxLayout()
        icon_badge = QLabel("🚀")
        icon_badge.setStyleSheet("""
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            border-radius: 12px;
            font-size: 26px;
            min-width: 48px;
            max-width: 48px;
            min-height: 48px;
            max-height: 48px;
            qproperty-alignment: AlignCenter;
        """)
        header_layout.addWidget(icon_badge)

        info_layout = QVBoxLayout()
        latest_ver = self.update_info.get("latest_version", "1.1.0")
        title_label = QLabel(f"يتوفر تحديث جديد: الإصدار {latest_ver}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        info_layout.addWidget(title_label)

        ver_sub = QLabel(f"الإصدار الحالي مثبت لديك: v{self.current_version}  |  حجم التحديث: ~{self.update_info.get('download_size_mb', 32)} MB")
        ver_sub.setStyleSheet("font-size: 11px; color: #94a3b8;")
        info_layout.addWidget(ver_sub)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Release Notes Section
        notes_title = QLabel("سجل التغييرات والمميزات الجديدة (What's New):")
        notes_title.setStyleSheet("font-weight: 600; font-size: 12px; color: #cbd5e1;")
        layout.addWidget(notes_title)

        notes_edit = QTextEdit()
        notes_edit.setReadOnly(True)
        raw_notes = self.update_info.get("release_notes", [])
        if isinstance(raw_notes, list):
            formatted_notes = "\n\n".join(f"• {note}" for note in raw_notes)
        else:
            formatted_notes = str(raw_notes)

        safety_note = (
            "\n\n--------------------------------------------------\n"
            "🔒 حماية البيانات مضمونة 100%:\n"
            "عملية التحديث تحافظ على كافة الفواتير، الأصناف، أوامر الصيانة،\n"
            "ورخص التشغيل دون أي مساس ببيانات محلك المسجلة."
        )
        notes_edit.setPlainText(formatted_notes + safety_note)
        layout.addWidget(notes_edit)

        # Progress bar (Hidden until download starts)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 500;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.browser_btn = QPushButton("🌐 التحميل عبر المتصفح")
        self.browser_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                padding: 8px 14px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
        """)
        self.browser_btn.clicked.connect(self.open_browser_download)
        btn_layout.addWidget(self.browser_btn)

        btn_layout.addStretch()

        self.cancel_btn = QPushButton("تذكيري لاحقاً")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #cbd5e1;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.update_btn = QPushButton("⚡ تحديث وتثبيت الآن")
        self.update_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(135deg, #0284c7, #0369a1);
                color: #ffffff;
                border: none;
                padding: 8px 22px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #0369a1, #075985);
            }
            QPushButton:disabled {
                background: #475569;
                color: #94a3b8;
            }
        """)
        self.update_btn.clicked.connect(self.start_download)
        btn_layout.addWidget(self.update_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def open_browser_download(self):
        url = self.update_info.get("download_url", "http://34.175.186.221/downloads/MobileStore-Setup.exe")
        webbrowser.open(url)
        self.accept()

    def start_download(self):
        self.update_btn.setEnabled(False)
        self.cancel_btn.setText("إلغاء التحميل")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.cancel_download)

        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.status_label.setText("جاري الاتصال بالخادم وبدء تحميل التحديث...")

        download_url = self.update_info.get("download_url", "http://34.175.186.221/downloads/MobileStore-Setup.exe")
        filename = self.update_info.get("filename", "MobileStore-Setup.exe")

        self.download_worker = DownloadWorker(download_url, filename)
        self.download_worker.progress.connect(self.on_download_progress)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.error.connect(self.on_download_error)
        self.download_worker.start()

    def on_download_progress(self, downloaded, total):
        if total > 0:
            percent = int((downloaded / total) * 100)
            self.progress_bar.setValue(percent)
            mb_down = downloaded / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            self.status_label.setText(f"جاري التحميل: {mb_down:.1f} MB من أصل {mb_tot:.1f} MB ({percent}%)")
        else:
            mb_down = downloaded / (1024 * 1024)
            self.status_label.setText(f"جاري التحميل: {mb_down:.1f} MB...")

    def on_download_finished(self, file_path):
        self.downloaded_installer_path = file_path
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ اكتمل التحميل بنجاح! جاري تشغيل المثبت...")

        # Ask user or launch automatically
        reply = QMessageBox.information(
            self,
            "جاهز للتثبيت",
            "تم تحميل التحديث بنجاح!\n\nسيتم الآن إغلاق البرنامج لتطبيق التحديث الجديد تلقائياً دون فقدان أي بيانات.",
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

        try:
            # Launch installer
            subprocess.Popen([file_path], shell=True)
            # Exit current application so installer can replace binaries
            import PyQt6.QtWidgets
            app = PyQt6.QtWidgets.QApplication.instance()
            if app:
                app.quit()
            else:
                sys.exit(0)
        except Exception as e:
            QMessageBox.critical(self, "خطأ في تشغيل المثبت", f"تعذر تشغيل ملف التثبيت تلقائياً:\n{e}\n\nيمكنك تشغيله يدوياً من المسار:\n{file_path}")

    def on_download_error(self, err_msg):
        self.status_label.setText(f"❌ حدث خطأ أثناء التحميل: {err_msg}")
        self.update_btn.setEnabled(True)
        self.cancel_btn.setText("إغلاق")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.reject)

        reply = QMessageBox.question(
            self,
            "تعذر التحميل المباشر",
            f"حدث خطأ أثناء تحميل التحديث:\n{err_msg}\n\nهل ترغب في فتح رابط التحميل المباشر في المتصفح؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.open_browser_download()

    def cancel_download(self):
        if self.download_worker:
            self.download_worker.cancel()
        self.reject()


def check_updates_async(api_base_url, current_version=CURRENT_APP_VERSION, on_result=None, manual=False, parent=None):
    """
    Checks for updates against MobileStore backend API.
    Can be called silently on startup or manually when clicking 'Check for Updates'.
    """
    class UpdateCheckThread(QThread):
        result_signal = pyqtSignal(dict, bool, str)

        def run(self):
            try:
                url = f"{api_base_url.rstrip('/')}/app/check-update/"
                resp = requests.get(
                    url,
                    params={"current_version": current_version, "platform": "windows"},
                    timeout=5
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.result_signal.emit(data, manual, "")
                else:
                    self.result_signal.emit({}, manual, f"HTTP Error {resp.status_code}")
            except Exception as e:
                self.result_signal.emit({}, manual, str(e))

    def handle_result(data, was_manual, error_msg):
        if error_msg:
            if was_manual and parent:
                QMessageBox.warning(
                    parent,
                    "فحص التحديثات",
                    f"تعذر الاتصال بخادم التحديثات حالياً:\n{error_msg}\n\nيرجى التأكد من اتصال الإنترنت أو المحاولة لاحقاً."
                )
            return

        is_avail = data.get("is_update_available", False)
        latest_ver = data.get("latest_version", current_version)

        if is_avail:
            dialog = UpdateDialog(data, current_version=current_version, parent=parent)
            dialog.exec()
        else:
            if was_manual and parent:
                QMessageBox.information(
                    parent,
                    "أنت تستخدم أحدث إصدار",
                    f"برنامجك محدث بالفعل إلى أحدث إصدار متاح (v{current_version})!\n\nلا توجد تحديثات جديدة حالياً."
                )

    thread = UpdateCheckThread(parent)
    thread.result_signal.connect(on_result if on_result else handle_result)
    thread.start()
    return thread
