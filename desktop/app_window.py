import json
import os
import sqlite3
import uuid
from datetime import datetime

import requests
from PyQt6.QtCore import Qt, QKeyCombination, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut, QFont, QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sync_worker import SyncWorker


REPAIR_STATUS_CHOICES = [
    ("diagnosing", "قيد الفحص والتشخيص (Diagnosing)"),
    ("waiting_parts", "في انتظار قطع الغيار (Waiting Parts)"),
    ("in_progress", "قيد الصيانة والإصلاح (In Progress)"),
    ("ready", "جاهز للاستلام (Ready for Pickup)"),
    ("delivered", "تم التسليم ومكتمل (Delivered)"),
    ("cancelled", "مرفوض / تعذر الإصلاح (Cancelled)"),
]

STATUS_COLORS = {
    "diagnosing": "#38bdf8",     # Sky blue
    "waiting_parts": "#fb923c",  # Orange
    "in_progress": "#facc15",    # Yellow
    "ready": "#34d399",          # Mint green
    "delivered": "#22c55e",      # Strong green
    "cancelled": "#ef4444",      # Red
}

STATUS_MAP_LEGACY = {
    "pending": "diagnosing",
    "completed": "delivered",
}


class ReceiptDialog(QDialog):
    """Monospace Sales Invoice Receipt Popup matching image media_1789838350417.png"""
    def __init__(self, receipt_no, items, total_paid, date_str=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sale Recorded - Receipt Generated")
        self.setFixedSize(500, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #1f1f1f;
                color: #ffffff;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QPushButton {
                background-color: #1f1f1f;
                color: #ffffff;
                border: 2px solid #0078d4;
                border-radius: 4px;
                padding: 6px 30px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #0078d4;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 20, 25, 20)

        # Header icon + text
        content_layout = QHBoxLayout()

        # Blue info badge
        icon_label = QLabel("ℹ")
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #0078d4;
                color: #ffffff;
                border-radius: 20px;
                font-size: 26px;
                font-weight: bold;
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
                qproperty-alignment: AlignCenter;
            }
        """)
        content_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignTop)

        # Formatted receipt text
        date_str = date_str or datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = []
        lines.append("          MOBILE STORE POS")
        lines.append("           SALES INVOICE")
        lines.append("======================================")
        lines.append(f"Receipt No:              #{receipt_no.upper()}")
        lines.append(f"Date:              {date_str}")
        lines.append("--------------------------------------")
        lines.append(f"{'Item Description':<25} {'Amount':>10}")
        lines.append("--------------------------------------")

        for item in items:
            desc = item['description']
            if item['qty'] > 1 and not desc.endswith(f"x{item['qty']}"):
                desc = f"{desc} x{item['qty']}"
            lines.append(f"{desc:<25} {item['total']:>10.2f}")

        lines.append("======================================")
        lines.append(f"TOTAL PAID:             {total_paid:.2f} EGP")
        lines.append("======================================")
        lines.append("     Goods received in good condition")
        lines.append("       Thank you for your business!")

        receipt_text = "\n".join(lines)
        receipt_label = QLabel(receipt_text)
        receipt_label.setStyleSheet("color: #ffffff; font-size: 13px; line-height: 1.4;")
        receipt_label.setFont(QFont("Consolas", 10))
        content_layout.addWidget(receipt_label)

        layout.addLayout(content_layout)
        layout.addStretch()

        # OK button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)


class StoreMainWindow(QWidget):
    """
    Dark-themed POS Window precisely matching media_1789838350422.png & media_1789838350452.png
    Fully synced with Django Web API (Sales POS & Repairs Management)
    """
    def __init__(self, username, access_token, license_info, is_offline=False, api_base_url="http://localhost:8000/api", db_path="local_storage.db", refresh_token=None, parent=None):
        super().__init__(parent)
        self.username = username
        self.access_token = access_token
        self.license_info = license_info or {}
        self.is_offline = is_offline
        self.api_base_url = api_base_url
        self.db_path = db_path
        self.refresh_token = refresh_token

        self.current_invoice_items = []
        self.available_stock = []
        self.completed_invoices = []
        self.sync_worker = None

        self.init_db()
        self.init_ui()
        self.load_data()

        # 30-Second Auto-Reconnect & Heartbeat Timer
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.setInterval(30_000)
        self.heartbeat_timer.timeout.connect(self.check_server_heartbeat)
        self.heartbeat_timer.start()

        # Initial background sync / reachability check
        QTimer.singleShot(1000, lambda: self.start_async_sync(silent=True))

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stock_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                stock INTEGER DEFAULT 1,
                cost REAL DEFAULT 0.0,
                sale_price REAL DEFAULT 0.0,
                server_id INTEGER
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                summary TEXT,
                items_qty INTEGER,
                total_amount REAL,
                net_profit REAL,
                date TEXT,
                items_json TEXT,
                is_synced INTEGER DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS repairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT,
                device_info TEXT,
                issue TEXT,
                cost REAL,
                payment REAL,
                deposit REAL DEFAULT 0.0,
                profit REAL,
                status TEXT,
                date TEXT,
                server_id INTEGER,
                is_synced INTEGER DEFAULT 0
            )
        """)

        # Migration: Ensure new columns exist in legacy databases
        cur.execute("PRAGMA table_info(repairs)")
        rep_cols = [col[1] for col in cur.fetchall()]
        if "deposit" not in rep_cols:
            cur.execute("ALTER TABLE repairs ADD COLUMN deposit REAL DEFAULT 0.0")
        if "server_id" not in rep_cols:
            cur.execute("ALTER TABLE repairs ADD COLUMN server_id INTEGER")

        cur.execute("PRAGMA table_info(stock_items)")
        stock_cols = [col[1] for col in cur.fetchall()]
        if "server_id" not in stock_cols:
            cur.execute("ALTER TABLE stock_items ADD COLUMN server_id INTEGER")

        # Insert sample stock if empty
        cur.execute("SELECT COUNT(*) FROM stock_items")
        if cur.fetchone()[0] == 0:
            cur.executemany("""
                INSERT INTO stock_items (description, stock, cost, sale_price) VALUES (?, ?, ?, ?)
            """, [
                ("oppo (oppo reno 14)", 3, 28500.0, 27000.0),
                ("phone", 5, 7000.0, 8500.0),
                ("oppo", 2, 24000.0, 28000.0),
                ("oppo reno 6 5g", 1, 5600.0, 7000.0),
                ("iPhone 15 Pro Max", 2, 55000.0, 62000.0),
                ("Samsung Galaxy S24 Ultra", 3, 48000.0, 54000.0),
            ])

        # Insert recent completed invoices if empty
        cur.execute("SELECT COUNT(*) FROM invoices")
        if cur.fetchone()[0] == 0:
            cur.executemany("""
                INSERT INTO invoices (id, summary, items_qty, total_amount, net_profit, date, is_synced)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, [
                ("aefffeb1", "oppo (oppo reno 14) (+1 items)", 3, 45500.0, 45500.0, "2026-09-18 22:50",),
                ("b50b5550", "phone", 2, 17000.0, 17000.0, "2026-09-18 22:57",),
                ("8c59b9b8", "oppo", 1, 28000.0, 28000.0, "2026-09-18 23:01",),
                ("824bca0c", "oppo reno 6 5g", 1, 7000.0, 1400.0, "2026-09-18 23:15",),
            ])

        conn.commit()
        conn.close()

    def init_ui(self):
        mode_str = "Offline Mode" if self.is_offline else "Online Mode"
        self.setWindowTitle(f"Mobile Store POS & Repairs - {mode_str}")
        self.resize(1180, 750)

        # Global Dark Theme stylesheet matching screenshots
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Segoe UI', Tahoma, sans-serif;
                font-size: 12px;
            }
            QTabWidget::pane {
                border: 1px solid #333333;
                background-color: #1e1e1e;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #252526;
                color: #999999;
                padding: 7px 18px;
                border: 1px solid #333333;
                border-bottom: none;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #2d2d30;
                color: #ffffff;
                font-weight: bold;
                border-color: #444444;
            }
            QLineEdit, QComboBox {
                background-color: #2b2b2b;
                border: 1px solid #3f3f46;
                border-radius: 3px;
                padding: 5px 8px;
                color: #ffffff;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #0078d4;
            }
            QComboBox QAbstractItemView {
                background-color: #252526;
                color: #ffffff;
                selection-background-color: #094771;
            }
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252526;
                gridline-color: #2e2e2e;
                border: 1px solid #333333;
                color: #ffffff;
                selection-background-color: #094771;
                selection-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #252526;
                color: #aaaaaa;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #383838;
                font-weight: bold;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3f3f46;
                border-radius: 3px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #383838;
                color: #ffffff;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #555555;
                background: #2b2b2b;
                border-radius: 2px;
            }
            QCheckBox::indicator:checked {
                background: #0078d4;
                border-color: #0078d4;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(10)

        # Top status bar: License left, Sync & Connectivity center, Hardware right
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        exp_date = self.license_info.get("expires_at", "2027-09-18")
        lic_label = QLabel(f"License: Active until {exp_date}")
        lic_label.setStyleSheet("color: #a1a1aa; font-size: 11px; font-weight: bold;")
        top_bar.addWidget(lic_label)

        top_bar.addStretch()

        # Live Connection Badge
        self.top_conn_badge = QLabel("Checking..." if not self.is_offline else "🟠 Offline (Local)")
        self.top_conn_badge.setStyleSheet(
            "background-color: #27272a; color: #facc15; font-size: 11px; font-weight: bold; "
            "padding: 3px 10px; border-radius: 12px; border: 1px solid #3f3f46;"
        )
        top_bar.addWidget(self.top_conn_badge)

        # Pending Queue Badge
        self.top_pending_badge = QLabel("⏳ Pending: 0")
        self.top_pending_badge.setStyleSheet(
            "background-color: #1e293b; color: #38bdf8; font-size: 11px; font-weight: bold; "
            "padding: 3px 10px; border-radius: 12px; border: 1px solid #334155;"
        )
        top_bar.addWidget(self.top_pending_badge)

        # Quick Manual Sync Button
        self.top_sync_btn = QPushButton("🔄 Sync Now")
        self.top_sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 12px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
            QPushButton:disabled {
                background-color: #3f3f46;
                color: #71717a;
            }
        """)
        self.top_sync_btn.clicked.connect(lambda: self.start_async_sync(silent=False))
        top_bar.addWidget(self.top_sync_btn)

        # Quick Reconnect Button (shown when offline)
        self.top_reconnect_btn = QPushButton("⚡ Reconnect")
        self.top_reconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 10px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #15803d;
            }
        """)
        self.top_reconnect_btn.clicked.connect(lambda: self.start_async_sync(silent=False))
        self.top_reconnect_btn.setVisible(self.is_offline)
        top_bar.addWidget(self.top_reconnect_btn)

        top_bar.addSpacing(10)

        hw_hash = self.license_info.get("hardware_id", "effb942a4261")
        if len(hw_hash) > 16:
            hw_hash = hw_hash[:16] + "..."
        hw_label = QLabel(f"Hardware: {hw_hash}")
        hw_label.setStyleSheet("color: #71717a; font-size: 11px;")
        top_bar.addWidget(hw_label)

        main_layout.addLayout(top_bar)

        # Tabs: matching screenshot tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_sales_pos_tab(), "Sales POS")
        self.tabs.addTab(self.create_repairs_tab(), "Repairs Management")
        self.tabs.addTab(self.create_sync_tab(), "Sync Monitor")
        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)

        # Shortcut F12 for Checkout & Print Invoice
        f12_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F12), self)
        f12_shortcut.activated.connect(self.checkout_invoice)

    # -------------------------------------------------------------
    # TAB 1: SALES POS
    # -------------------------------------------------------------
    def create_sales_pos_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(12)

        # --- Row 1 of inputs ---
        row1 = QHBoxLayout()
        self.custom_item_check = QCheckBox("Custom Item / Service")
        self.custom_item_check.toggled.connect(self.on_custom_item_toggled)
        row1.addWidget(self.custom_item_check)

        row1.addSpacing(20)

        # Stock dropdown
        self.stock_combo = QComboBox()
        self.stock_combo.currentIndexChanged.connect(self.on_stock_combo_changed)
        row1.addWidget(self.stock_combo, 1)

        # Custom item description (hidden by default)
        self.custom_desc_input = QLineEdit()
        self.custom_desc_input.setPlaceholderText("Enter custom item or service description...")
        self.custom_desc_input.setVisible(False)
        row1.addWidget(self.custom_desc_input, 1)

        layout.addLayout(row1)

        # --- Row 2 of inputs ---
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        row2.addWidget(QLabel("Qty:"))
        self.qty_input = QLineEdit("1")
        self.qty_input.setFixedWidth(55)
        self.qty_input.textChanged.connect(self.update_row_profit)
        row2.addWidget(self.qty_input)

        row2.addWidget(QLabel("Cost/Unit:"))
        self.cost_input = QLineEdit("0.00")
        self.cost_input.setFixedWidth(110)
        self.cost_input.setReadOnly(True)
        self.cost_input.setStyleSheet("background-color: #181818; color: #a1a1aa; border: 1px solid #333333; padding: 5px 8px; border-radius: 3px;")
        self.cost_input.setToolTip("سعر الشراء (غير قابل للتعديل للأجهزة المخزنة)")
        self.cost_input.textChanged.connect(self.update_row_profit)
        row2.addWidget(self.cost_input)

        row2.addWidget(QLabel("Sale/Unit:"))
        self.sale_input = QLineEdit("0.00")
        self.sale_input.setFixedWidth(110)
        self.sale_input.textChanged.connect(self.update_row_profit)
        row2.addWidget(self.sale_input)

        self.row_profit_label = QLabel("Profit: 0.00 EGP")
        self.row_profit_label.setStyleSheet("color: #22c55e; font-weight: bold;")
        row2.addWidget(self.row_profit_label)

        row2.addStretch()

        self.add_to_invoice_btn = QPushButton("+ Add to Invoice")
        self.add_to_invoice_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 7px 20px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        self.add_to_invoice_btn.clicked.connect(self.add_item_to_invoice)
        row2.addWidget(self.add_to_invoice_btn)

        layout.addLayout(row2)

        # --- Section: Current Invoice Items ---
        curr_items_title = QLabel("Current Invoice Items:")
        curr_items_title.setStyleSheet("font-weight: bold; color: #ffffff; margin-top: 5px;")
        layout.addWidget(curr_items_title)

        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(5)
        self.invoice_table.setHorizontalHeaderLabels(["Item Description", "Qty", "Sale/Unit", "Total", "Net Profit"])
        self.invoice_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.invoice_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.invoice_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.invoice_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.invoice_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.invoice_table.setFixedHeight(140)
        layout.addWidget(self.invoice_table)

        # --- Bar below invoice table ---
        action_bar = QHBoxLayout()

        remove_btn = QPushButton("Remove Selected Item")
        remove_btn.clicked.connect(self.remove_selected_invoice_item)
        action_bar.addWidget(remove_btn)

        clear_btn = QPushButton("Clear Invoice")
        clear_btn.clicked.connect(self.clear_invoice)
        action_bar.addWidget(clear_btn)

        refresh_btn = QPushButton("Refresh Local Stock")
        refresh_btn.clicked.connect(self.load_data)
        action_bar.addWidget(refresh_btn)

        action_bar.addStretch()

        self.invoice_total_label = QLabel("Invoice Total: 0.00 EGP")
        self.invoice_total_label.setStyleSheet("color: #0098ff; font-weight: bold; font-size: 13px;")
        action_bar.addWidget(self.invoice_total_label)

        action_bar.addSpacing(15)

        self.invoice_profit_label = QLabel("Profit: 0.00 EGP")
        self.invoice_profit_label.setStyleSheet("color: #22c55e; font-weight: bold; font-size: 13px;")
        action_bar.addWidget(self.invoice_profit_label)

        action_bar.addSpacing(15)

        self.checkout_btn = QPushButton("Checkout Print Invoice (F12)")
        self.checkout_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 9px 22px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
        """)
        self.checkout_btn.clicked.connect(self.checkout_invoice)
        action_bar.addWidget(self.checkout_btn)

        layout.addLayout(action_bar)

        # --- Section: Recent Completed Invoices ---
        recent_title = QLabel("Recent Completed Invoices:")
        recent_title.setStyleSheet("font-weight: bold; color: #ffffff; margin-top: 10px;")
        layout.addWidget(recent_title)

        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(7)
        self.recent_table.setHorizontalHeaderLabels(["ID", "Invoice Summary", "Items Qty", "Total Amount", "Net Profit", "Sync", "Date"])
        self.recent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.recent_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.recent_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.recent_table)

        tab.setLayout(layout)
        return tab

    # -------------------------------------------------------------
    # TAB 2: REPAIRS MANAGEMENT (ENHANCED WORKFLOW)
    # -------------------------------------------------------------
    def create_repairs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(12)

        # New repair ticket box
        top_box = QFrame()
        top_box.setStyleSheet("background-color: #252526; border: 1px solid #333333; border-radius: 6px; padding: 12px;")
        t_lay = QVBoxLayout()
        t_lay.setSpacing(10)

        t_lbl = QLabel("تسجيل تذكرة صيانة جديدة (Create New Repair Ticket):")
        t_lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #ffffff;")
        t_lay.addWidget(t_lbl)

        # Row 1: Customer info, Device, Issue
        form_row1 = QHBoxLayout()
        form_row1.setSpacing(10)

        self.rep_cust_in = QLineEdit()
        self.rep_cust_in.setPlaceholderText("اسم العميل / رقم الهاتف (Customer Name/Phone)")
        form_row1.addWidget(self.rep_cust_in, 2)

        self.rep_dev_in = QLineEdit()
        self.rep_dev_in.setPlaceholderText("نوع الجهاز (Device e.g. iPhone 13 Pro)")
        form_row1.addWidget(self.rep_dev_in, 2)

        self.rep_issue_in = QLineEdit()
        self.rep_issue_in.setPlaceholderText("وصف المشكلة / العطل (Issue Description)")
        form_row1.addWidget(self.rep_issue_in, 3)

        t_lay.addLayout(form_row1)

        # Row 2: Financials & Status
        form_row2 = QHBoxLayout()
        form_row2.setSpacing(10)

        form_row2.addWidget(QLabel("تكلفة المحل:"))
        self.rep_cost_in = QLineEdit()
        self.rep_cost_in.setPlaceholderText("التكلفة (Cost)")
        self.rep_cost_in.setFixedWidth(110)
        self.rep_cost_in.textChanged.connect(self.on_repair_inputs_changed)
        form_row2.addWidget(self.rep_cost_in)

        form_row2.addWidget(QLabel("سعر العميل:"))
        self.rep_pay_in = QLineEdit()
        self.rep_pay_in.setPlaceholderText("السعر (Price)")
        self.rep_pay_in.setFixedWidth(110)
        self.rep_pay_in.textChanged.connect(self.on_repair_inputs_changed)
        form_row2.addWidget(self.rep_pay_in)

        form_row2.addWidget(QLabel("المدفوع مقدماً:"))
        self.rep_deposit_in = QLineEdit()
        self.rep_deposit_in.setPlaceholderText("تحت الحساب (Deposit)")
        self.rep_deposit_in.setFixedWidth(110)
        self.rep_deposit_in.textChanged.connect(self.on_repair_inputs_changed)
        form_row2.addWidget(self.rep_deposit_in)

        form_row2.addWidget(QLabel("الحالة:"))
        self.rep_status_combo = QComboBox()
        for code, label in REPAIR_STATUS_CHOICES:
            self.rep_status_combo.addItem(label, code)
        form_row2.addWidget(self.rep_status_combo, 1)

        t_lay.addLayout(form_row2)

        # Row 3: Live Indicators + Add Button
        form_row3 = QHBoxLayout()
        form_row3.setSpacing(15)

        self.rep_remaining_label = QLabel("المتبقي: 0.00 EGP")
        self.rep_remaining_label.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 13px;")
        form_row3.addWidget(self.rep_remaining_label)

        self.rep_profit_label = QLabel("الربح المتوقع: 0.00 EGP")
        self.rep_profit_label.setStyleSheet("color: #22c55e; font-weight: bold; font-size: 13px;")
        form_row3.addWidget(self.rep_profit_label)

        form_row3.addStretch()

        create_rep_btn = QPushButton("+ إضافة تذكرة الصيانة (+ Add Ticket)")
        create_rep_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 22px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        create_rep_btn.clicked.connect(self.add_repair_ticket)
        form_row3.addWidget(create_rep_btn)

        t_lay.addLayout(form_row3)
        top_box.setLayout(t_lay)
        layout.addWidget(top_box)

        # Repairs table header & refresh button
        table_top_bar = QHBoxLayout()
        tbl_lbl = QLabel("سجل تذاكر الصيانة (Active and Recent Repair Tickets):")
        tbl_lbl.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 13px;")
        table_top_bar.addWidget(tbl_lbl)

        table_top_bar.addStretch()

        rep_refresh_btn = QPushButton("تحديث من السيرفر (Refresh Repairs)")
        rep_refresh_btn.clicked.connect(lambda: self.start_async_sync(silent=False))
        table_top_bar.addWidget(rep_refresh_btn)
        layout.addLayout(table_top_bar)

        # Repairs table
        self.repairs_table = QTableWidget()
        self.repairs_table.setColumnCount(12)
        self.repairs_table.setHorizontalHeaderLabels([
            "ID", "Customer", "Device", "Issue", "Cost (تكلفة)",
            "Price (سعر)", "Deposit (مدفوع)", "Remaining (متبقي)",
            "Profit (ربح)", "Status (الحالة)", "Sync", "Date"
        ])
        self.repairs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.repairs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.repairs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.repairs_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.repairs_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.repairs_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.repairs_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.repairs_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.repairs_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.repairs_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        self.repairs_table.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)
        self.repairs_table.horizontalHeader().setSectionResizeMode(11, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.repairs_table)

        tab.setLayout(layout)
        return tab

    # -------------------------------------------------------------
    # TAB 3: SYNC MONITOR
    # -------------------------------------------------------------
    def create_sync_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        title = QLabel("Database & Synchronization Monitor")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        info_box = QFrame()
        info_box.setStyleSheet("background-color: #252526; border: 1px solid #333333; border-radius: 4px; padding: 15px;")
        info_lay = QVBoxLayout()
        info_lay.setSpacing(10)

        self.sync_status_label = QLabel(f"Connection Status: {'OFFLINE (Grace Period)' if self.is_offline else 'ONLINE (Connected to Server)'}")
        self.sync_status_label.setStyleSheet("font-weight: bold; color: #22c55e;" if not self.is_offline else "font-weight: bold; color: #f59e0b;")
        info_lay.addWidget(self.sync_status_label)

        info_lay.addWidget(QLabel(f"Server Base URL: {self.api_base_url}"))
        info_lay.addWidget(QLabel(f"Local Storage Database: {self.db_path}"))

        counts_layout = QHBoxLayout()
        self.unsynced_label = QLabel("Pending Unsynced Invoices: 0")
        self.unsynced_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        counts_layout.addWidget(self.unsynced_label)

        self.unsynced_repairs_label = QLabel("Pending Unsynced Repairs: 0")
        self.unsynced_repairs_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        counts_layout.addWidget(self.unsynced_repairs_label)
        counts_layout.addStretch()

        info_lay.addLayout(counts_layout)

        sync_btn = QPushButton("Sync All Data with Server Now (مزامنة فورية شاملة)")
        sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                padding: 9px 18px;
                font-size: 13px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        sync_btn.clicked.connect(lambda: self.start_async_sync(silent=False))
        info_lay.addWidget(sync_btn)

        info_box.setLayout(info_lay)
        layout.addWidget(info_box)

        # Sync activity log
        log_title = QLabel("Synchronization Activity Log:")
        log_title.setStyleSheet("font-weight: bold; color: #cccccc; margin-top: 10px;")
        layout.addWidget(log_title)

        self.sync_log_text = QPlainTextEdit()
        self.sync_log_text.setReadOnly(True)
        self.sync_log_text.setStyleSheet("background-color: #141414; color: #38bdf8; font-family: 'Consolas', monospace; font-size: 11px; border: 1px solid #333333;")
        self.sync_log_text.appendPlainText("Ready. Automatic real-time synchronization active.")
        layout.addWidget(self.sync_log_text)

        tab.setLayout(layout)
        return tab

    # -------------------------------------------------------------
    # LOGIC & EVENTS
    # -------------------------------------------------------------
    def on_custom_item_toggled(self, checked):
        self.stock_combo.setVisible(not checked)
        self.custom_desc_input.setVisible(checked)
        if checked:
            self.cost_input.setReadOnly(False)
            self.cost_input.setStyleSheet("background-color: #2b2b2b; color: #ffffff; border: 1px solid #3f3f46; padding: 5px 8px; border-radius: 3px;")
            self.cost_input.setText("0.00")
            self.sale_input.setText("0.00")
            self.sale_input.setReadOnly(False)
        else:
            self.cost_input.setReadOnly(True)
            self.cost_input.setStyleSheet("background-color: #181818; color: #a1a1aa; border: 1px solid #333333; padding: 5px 8px; border-radius: 3px;")
            self.on_stock_combo_changed(self.stock_combo.currentIndex())
        self.update_row_profit()

    def on_stock_combo_changed(self, idx):
        if idx >= 0 and idx < len(self.available_stock):
            item = self.available_stock[idx]
            self.cost_input.setReadOnly(True)
            self.cost_input.setStyleSheet("background-color: #181818; color: #a1a1aa; border: 1px solid #333333; padding: 5px 8px; border-radius: 3px;")
            self.cost_input.setText(f"{item['cost']:.2f}")
            self.sale_input.setReadOnly(False)
            self.sale_input.setText(f"{item['sale_price']:.2f}")
            self.update_row_profit()

    def update_row_profit(self):
        try:
            qty_str = self.qty_input.text().strip()
            cost_str = self.cost_input.text().strip()
            sale_str = self.sale_input.text().strip()

            qty = int(qty_str) if qty_str else 1
            cost = float(cost_str) if cost_str else 0.0
            sale = float(sale_str) if sale_str else 0.0

            profit = (sale - cost) * qty
            color = "#22c55e" if profit >= 0 else "#f85149"
            prefix = "+" if profit > 0 else ""
            self.row_profit_label.setText(f"Profit: {prefix}{profit:.2f} EGP")
            self.row_profit_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        except ValueError:
            self.row_profit_label.setText("Profit: 0.00 EGP")
            self.row_profit_label.setStyleSheet("color: #22c55e; font-weight: bold;")

    def add_item_to_invoice(self):
        is_custom = self.custom_item_check.isChecked()
        if is_custom:
            desc = self.custom_desc_input.text().strip()
            item_id = None
            server_item_id = None
            if not desc:
                QMessageBox.warning(self, "Input Error", "Please enter description for custom item/service.")
                return
        else:
            idx = self.stock_combo.currentIndex()
            if idx < 0 or idx >= len(self.available_stock):
                QMessageBox.warning(self, "Input Error", "Please select an item from stock.")
                return
            stock_item = self.available_stock[idx]
            desc = stock_item['description']
            item_id = stock_item['id']
            server_item_id = stock_item.get('server_id')

        try:
            qty = int(self.qty_input.text().strip() or "1")
            cost = float(self.cost_input.text().strip() or "0")
            sale = float(self.sale_input.text().strip() or "0")
            if qty <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numbers for Qty, Cost, and Sale price.")
            return

        total = sale * qty
        net_profit = (sale - cost) * qty

        self.current_invoice_items.append({
            "item_id": item_id,
            "server_item_id": server_item_id,
            "description": desc,
            "qty": qty,
            "cost_unit": cost,
            "sale_unit": sale,
            "total": total,
            "net_profit": net_profit
        })

        self.refresh_current_invoice_table()

    def refresh_current_invoice_table(self):
        self.invoice_table.setRowCount(len(self.current_invoice_items))
        inv_total = 0.0
        inv_profit = 0.0

        for row, item in enumerate(self.current_invoice_items):
            self.invoice_table.setItem(row, 0, QTableWidgetItem(item["description"]))
            self.invoice_table.setItem(row, 1, QTableWidgetItem(str(item["qty"])))
            self.invoice_table.setItem(row, 2, QTableWidgetItem(f"{item['sale_unit']:.2f}"))
            self.invoice_table.setItem(row, 3, QTableWidgetItem(f"{item['total']:.2f}"))

            p_item = QTableWidgetItem(f"{item['net_profit']:.2f}")
            p_item.setForeground(Qt.GlobalColor.green if item['net_profit'] >= 0 else Qt.GlobalColor.red)
            self.invoice_table.setItem(row, 4, p_item)

            inv_total += item["total"]
            inv_profit += item["net_profit"]

        self.invoice_total_label.setText(f"Invoice Total: {inv_total:.2f} EGP")
        self.invoice_profit_label.setText(f"Profit: {inv_profit:.2f} EGP")
        self.invoice_profit_label.setStyleSheet(
            f"color: {'#22c55e' if inv_profit >= 0 else '#f85149'}; font-weight: bold; font-size: 13px;"
        )

    def remove_selected_invoice_item(self):
        selected_row = self.invoice_table.currentRow()
        if selected_row >= 0 and selected_row < len(self.current_invoice_items):
            del self.current_invoice_items[selected_row]
            self.refresh_current_invoice_table()

    def clear_invoice(self):
        self.current_invoice_items = []
        self.refresh_current_invoice_table()

    def checkout_invoice(self):
        if not self.current_invoice_items:
            QMessageBox.warning(self, "Checkout", "Current invoice has no items.")
            return

        receipt_no = uuid.uuid4().hex[:8].upper()
        total_paid = sum(i["total"] for i in self.current_invoice_items)
        net_profit = sum(i["net_profit"] for i in self.current_invoice_items)
        total_qty = sum(i["qty"] for i in self.current_invoice_items)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Summary text
        first_desc = self.current_invoice_items[0]["description"]
        if len(self.current_invoice_items) > 1:
            summary = f"{first_desc} (+{len(self.current_invoice_items)-1} items)"
        else:
            summary = first_desc

        # 1. Save to SQLite locally first
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO invoices (id, summary, items_qty, total_amount, net_profit, date, items_json, is_synced)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            receipt_no.lower(),
            summary,
            total_qty,
            total_paid,
            net_profit,
            date_str,
            json.dumps(self.current_invoice_items)
        ))

        # Deduct stock locally
        for item in self.current_invoice_items:
            if item["item_id"]:
                cur.execute("UPDATE stock_items SET stock = MAX(0, stock - ?) WHERE id = ?", (item["qty"], item["item_id"]))

        conn.commit()
        conn.close()

        # 2. Trigger non-blocking background sync with web server
        self.start_async_sync(silent=True)

        # Show receipt popup dialog
        receipt_dialog = ReceiptDialog(receipt_no, self.current_invoice_items, total_paid, date_str, self)
        receipt_dialog.exec()

        # Clear invoice and refresh tables
        self.clear_invoice()
        self.load_data()

    # -------------------------------------------------------------
    # REPAIRS LOGIC
    # -------------------------------------------------------------
    def on_repair_inputs_changed(self):
        try:
            cost_str = self.rep_cost_in.text().strip()
            pay_str = self.rep_pay_in.text().strip()
            dep_str = self.rep_deposit_in.text().strip()

            cost = float(cost_str) if cost_str else 0.0
            price = float(pay_str) if pay_str else 0.0
            deposit = float(dep_str) if dep_str else 0.0

            remaining = price - deposit
            profit = price - cost

            rem_color = "#38bdf8" if remaining > 0 else "#22c55e"
            prof_color = "#22c55e" if profit >= 0 else "#ef4444"

            self.rep_remaining_label.setText(f"المتبقي على العميل: {remaining:.2f} EGP")
            self.rep_remaining_label.setStyleSheet(f"color: {rem_color}; font-weight: bold; font-size: 13px;")

            self.rep_profit_label.setText(f"الربح المحقق للمحل: {profit:.2f} EGP")
            self.rep_profit_label.setStyleSheet(f"color: {prof_color}; font-weight: bold; font-size: 13px;")
        except ValueError:
            self.rep_remaining_label.setText("المتبقي: 0.00 EGP")
            self.rep_profit_label.setText("الربح: 0.00 EGP")

    def add_repair_ticket(self):
        cust = self.rep_cust_in.text().strip()
        dev = self.rep_dev_in.text().strip()
        issue = self.rep_issue_in.text().strip()
        cost_str = self.rep_cost_in.text().strip()
        pay_str = self.rep_pay_in.text().strip()
        dep_str = self.rep_deposit_in.text().strip() or "0"
        status_code = self.rep_status_combo.currentData() or "diagnosing"

        if not (cust and dev and issue and cost_str and pay_str):
            QMessageBox.warning(self, "Input Error", "يرجى ملء جميع البيانات الأساسية: اسم العميل، نوع الجهاز، وصف المشكلة، التكلفة، وسعر العميل.")
            return

        try:
            cost = float(cost_str)
            pay = float(pay_str)
            deposit = float(dep_str)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "يرجى إدخال قيم عددية صحيحة للتكلفة وسعر العميل والمبلغ المدفوع.")
            return

        profit = pay - cost
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 1. Insert locally into SQLite
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO repairs (customer_name, device_info, issue, cost, payment, deposit, profit, status, date, is_synced)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (cust, dev, issue, cost, pay, deposit, profit, status_code, date_str))
        local_id = cur.lastrowid
        conn.commit()
        conn.close()

        # 2. Trigger non-blocking background sync with web server
        self.start_async_sync(silent=True)

        # Clear inputs
        self.rep_cust_in.clear()
        self.rep_dev_in.clear()
        self.rep_issue_in.clear()
        self.rep_cost_in.clear()
        self.rep_pay_in.clear()
        self.rep_deposit_in.clear()
        self.on_repair_inputs_changed()

        QMessageBox.information(self, "تم بنجاح", "تم تسجيل تذكرة الصيانة بنجاح وحفظها محلياً ومزامنتها مع السيرفر!")
        self.load_repairs_data()

    def update_repair_status_from_table(self, repair_id, new_status_code):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT server_id FROM repairs WHERE id = ?", (repair_id,))
        row = cur.fetchone()
        server_id = row[0] if row else None

        cur.execute("UPDATE repairs SET status = ?, is_synced = 0 WHERE id = ?", (new_status_code, repair_id))
        conn.commit()

        conn.close()
        self.start_async_sync(silent=True)
        self.load_repairs_data()

    # -------------------------------------------------------------
    # DATA LOADING & DISPLAY
    # -------------------------------------------------------------
    def load_data(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # 1. Load stock items
        cur.execute("SELECT id, description, stock, cost, sale_price, server_id FROM stock_items WHERE stock > 0")
        rows = cur.fetchall()
        self.available_stock = [
            {"id": r[0], "description": r[1], "stock": r[2], "cost": r[3], "sale_price": r[4], "server_id": r[5]}
            for r in rows
        ]

        self.stock_combo.blockSignals(True)
        self.stock_combo.clear()
        for s in self.available_stock:
            self.stock_combo.addItem(f"{s['description']} - Stock: {s['stock']}")
        self.stock_combo.blockSignals(False)

        if self.available_stock:
            self.on_stock_combo_changed(0)

        # 2. Load recent completed invoices
        cur.execute("SELECT id, summary, items_qty, total_amount, net_profit, is_synced, date FROM invoices ORDER BY rowid DESC LIMIT 50")
        inv_rows = cur.fetchall()
        self.recent_table.setRowCount(len(inv_rows))
        for row, r in enumerate(inv_rows):
            self.recent_table.setItem(row, 0, QTableWidgetItem(str(r[0])))
            self.recent_table.setItem(row, 1, QTableWidgetItem(str(r[1])))
            self.recent_table.setItem(row, 2, QTableWidgetItem(str(r[2])))
            self.recent_table.setItem(row, 3, QTableWidgetItem(f"{r[3]:.2f}"))
            self.recent_table.setItem(row, 4, QTableWidgetItem(f"{r[4]:.2f}"))

            sync_badge = QTableWidgetItem("🟢 Synced" if r[5] == 1 else "🟡 Pending")
            sync_badge.setForeground(Qt.GlobalColor.green if r[5] == 1 else Qt.GlobalColor.yellow)
            self.recent_table.setItem(row, 5, sync_badge)

            self.recent_table.setItem(row, 6, QTableWidgetItem(str(r[6])))

        # 3. Load unsynced counts and update badges
        cur.execute("SELECT COUNT(*) FROM invoices WHERE is_synced = 0")
        unsynced_inv = cur.fetchone()[0]
        self.unsynced_label.setText(f"Pending Unsynced Invoices: {unsynced_inv}")

        cur.execute("SELECT COUNT(*) FROM repairs WHERE is_synced = 0")
        unsynced_rep = cur.fetchone()[0]
        self.unsynced_repairs_label.setText(f"Pending Unsynced Repairs: {unsynced_rep}")

        total_pending = unsynced_inv + unsynced_rep
        if hasattr(self, "top_pending_badge"):
            if total_pending == 0:
                self.top_pending_badge.setText("✅ All Synced")
                self.top_pending_badge.setStyleSheet(
                    "background-color: #064e3b; color: #34d399; font-size: 11px; font-weight: bold; "
                    "padding: 3px 10px; border-radius: 12px; border: 1px solid #059669;"
                )
            else:
                self.top_pending_badge.setText(f"⏳ {total_pending} Pending Sync")
                self.top_pending_badge.setStyleSheet(
                    "background-color: #451a03; color: #fbbf24; font-size: 11px; font-weight: bold; "
                    "padding: 3px 10px; border-radius: 12px; border: 1px solid #d97706;"
                )

        conn.close()
        self.load_repairs_data()

    def load_repairs_data(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, customer_name, device_info, issue, cost, payment, deposit, profit, status, is_synced, date, server_id
            FROM repairs
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        self.repairs_table.setRowCount(len(rows))

        for row, r in enumerate(rows):
            rep_id = r[0]
            cust = str(r[1] or "")
            dev = str(r[2] or "")
            issue = str(r[3] or "")
            cost = float(r[4] or 0)
            pay = float(r[5] or 0)
            dep = float(r[6] or 0)
            remaining = pay - dep
            profit = float(r[7] if r[7] is not None else (pay - cost))
            raw_status = str(r[8] or "diagnosing").lower()
            current_status = STATUS_MAP_LEGACY.get(raw_status, raw_status)
            is_synced = r[9]
            date_str = str(r[10] or "")
            server_id = r[11]

            self.repairs_table.setItem(row, 0, QTableWidgetItem(f"#{rep_id}"))
            self.repairs_table.setItem(row, 1, QTableWidgetItem(cust))
            self.repairs_table.setItem(row, 2, QTableWidgetItem(dev))
            self.repairs_table.setItem(row, 3, QTableWidgetItem(issue))
            self.repairs_table.setItem(row, 4, QTableWidgetItem(f"{cost:.2f}"))
            self.repairs_table.setItem(row, 5, QTableWidgetItem(f"{pay:.2f}"))
            self.repairs_table.setItem(row, 6, QTableWidgetItem(f"{dep:.2f}"))

            rem_item = QTableWidgetItem(f"{remaining:.2f}")
            rem_item.setForeground(Qt.GlobalColor.cyan if remaining > 0 else Qt.GlobalColor.green)
            self.repairs_table.setItem(row, 7, rem_item)

            prof_item = QTableWidgetItem(f"{profit:.2f}")
            prof_item.setForeground(Qt.GlobalColor.green if profit >= 0 else Qt.GlobalColor.red)
            self.repairs_table.setItem(row, 8, prof_item)

            # Interactive Status dropdown inside table
            status_combo = QComboBox()
            status_combo.setStyleSheet("""
                QComboBox {
                    background-color: #2b2b2b;
                    border: 1px solid #3f3f46;
                    border-radius: 3px;
                    padding: 3px 6px;
                    font-size: 11px;
                }
            """)
            status_combo.blockSignals(True)
            current_idx = 0
            for i, (code, lbl) in enumerate(REPAIR_STATUS_CHOICES):
                status_combo.addItem(lbl, code)
                if code == current_status:
                    current_idx = i
            status_combo.setCurrentIndex(current_idx)
            status_combo.blockSignals(False)

            def make_handler(r_id, combo_ref):
                def handler(idx):
                    new_code = combo_ref.itemData(idx)
                    self.update_repair_status_from_table(r_id, new_code)
                return handler

            status_combo.currentIndexChanged.connect(make_handler(rep_id, status_combo))
            self.repairs_table.setCellWidget(row, 9, status_combo)

            sync_badge = QTableWidgetItem("🟢 Synced" if is_synced == 1 else "🟡 Local")
            sync_badge.setForeground(Qt.GlobalColor.green if is_synced == 1 else Qt.GlobalColor.yellow)
            self.repairs_table.setItem(row, 10, sync_badge)

            self.repairs_table.setItem(row, 11, QTableWidgetItem(date_str))

        conn.close()

    # -------------------------------------------------------------
    # FULL TWO-WAY SYNCHRONIZATION
    # -------------------------------------------------------------
    # ASYNCHRONOUS TWO-WAY SYNCHRONIZATION
    # -------------------------------------------------------------
    def log_sync(self, message):
        time_str = datetime.now().strftime("%H:%M:%S")
        if hasattr(self, "sync_log_text"):
            self.sync_log_text.appendPlainText(f"[{time_str}] {message}")

    def check_server_heartbeat(self):
        """Periodic background heartbeat check every 30 seconds."""
        if self.sync_worker and self.sync_worker.isRunning():
            return
        self.start_async_sync(silent=True)

    def start_async_sync(self, silent=False):
        """Spawns non-blocking QThread background worker for 2-way sync."""
        if self.sync_worker and self.sync_worker.isRunning():
            if not silent:
                QMessageBox.information(self, "Sync", "مزامنة البيانات جارية بالفعل في الخلفية...")
            return

        # Set UI to syncing state
        if hasattr(self, "top_conn_badge"):
            self.top_conn_badge.setText("🔄 Syncing...")
            self.top_conn_badge.setStyleSheet(
                "background-color: #1e3a8a; color: #60a5fa; font-size: 11px; font-weight: bold; "
                "padding: 3px 10px; border-radius: 12px; border: 1px solid #2563eb;"
            )
        if hasattr(self, "top_sync_btn"):
            self.top_sync_btn.setEnabled(False)

        self.sync_worker = SyncWorker(
            api_base_url=self.api_base_url,
            access_token=self.access_token,
            db_path=self.db_path,
            refresh_token=self.refresh_token
        )

        self.sync_worker.log_signal.connect(self.log_sync)
        self.sync_worker.status_signal.connect(self.on_sync_status)
        self.sync_worker.connection_status_signal.connect(self.on_connection_status)
        self.sync_worker.finished_signal.connect(lambda stats: self.on_sync_finished(stats, silent))
        self.sync_worker.start()

    def on_sync_status(self, status_text):
        if hasattr(self, "top_conn_badge"):
            self.top_conn_badge.setText(f"🔄 {status_text[:20]}...")

    def on_connection_status(self, is_online):
        self.is_offline = not is_online
        mode_str = "Offline Mode (Local)" if self.is_offline else "Online Mode (Connected)"
        self.setWindowTitle(f"Mobile Store POS & Repairs - {mode_str}")

        if hasattr(self, "top_conn_badge"):
            if is_online:
                self.top_conn_badge.setText("🟢 Online (Connected)")
                self.top_conn_badge.setStyleSheet(
                    "background-color: #064e3b; color: #34d399; font-size: 11px; font-weight: bold; "
                    "padding: 3px 10px; border-radius: 12px; border: 1px solid #059669;"
                )
            else:
                self.top_conn_badge.setText("🟠 Offline (Local Mode)")
                self.top_conn_badge.setStyleSheet(
                    "background-color: #451a03; color: #fbbf24; font-size: 11px; font-weight: bold; "
                    "padding: 3px 10px; border-radius: 12px; border: 1px solid #d97706;"
                )

        if hasattr(self, "top_reconnect_btn"):
            self.top_reconnect_btn.setVisible(not is_online)

        if hasattr(self, "sync_status_label"):
            if is_online:
                self.sync_status_label.setText("Connection Status: ONLINE (Connected to Server)")
                self.sync_status_label.setStyleSheet("font-weight: bold; color: #22c55e;")
            else:
                self.sync_status_label.setText("Connection Status: OFFLINE (Grace Period / Local Cache Active)")
                self.sync_status_label.setStyleSheet("font-weight: bold; color: #f59e0b;")

    def on_sync_finished(self, stats, silent):
        if hasattr(self, "top_sync_btn"):
            self.top_sync_btn.setEnabled(True)

        if stats.get("new_access_token"):
            self.access_token = stats["new_access_token"]

        # Refresh connection badge state
        is_online = not stats.get("offline", False)
        self.on_connection_status(is_online)

        # Reload tables and pending badge from SQLite
        self.load_data()

        # Notify user if manual click
        if not silent:
            if stats.get("success"):
                msg = (
                    f"تمت المزامنة بنجاح مع السيرفر!\n\n"
                    f"• فواتير مبيعات تم رفعها: {stats['pushed_sales']}\n"
                    f"• تذاكر صيانة تم رفعها: {stats['pushed_repairs']}\n"
                    f"• تذاكر صيانة تم سحبها: {stats['pulled_repairs']}\n"
                    f"• منتجات تم تحديثها من المخزن: {stats['pulled_items']}"
                )
                QMessageBox.information(self, "اكتملت المزامنة", msg)
            elif stats.get("offline"):
                QMessageBox.warning(
                    self,
                    "وضع عدم الاتصال",
                    "السيرفر غير متاح حالياً. تم حفظ كافة العمليات في قاعدة البيانات المحلية وسيتم مزامنتها تلقائياً عند عودة الاتصال."
                )
            else:
                err_msg = stats.get("error", "Unknown synchronization error")
                QMessageBox.warning(self, "خطأ في المزامنة", f"حدث خطأ أثناء المزامنة:\n{err_msg}")
