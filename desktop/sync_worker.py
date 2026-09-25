import json
import sqlite3
import requests
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

STATUS_MAP_LEGACY = {
    "pending": "diagnosing",
    "completed": "delivered",
}

class SyncWorker(QThread):
    """
    Non-blocking background synchronization worker for Mobile-Store Desktop POS.
    Executes two-way sync (SQLite <-> Django REST API) in a separate thread.
    """
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    connection_status_signal = pyqtSignal(bool)
    finished_signal = pyqtSignal(dict)

    def __init__(self, api_base_url, access_token, db_path, refresh_token=None, parent=None):
        super().__init__(parent)
        self.api_base_url = api_base_url.rstrip("/")
        self.access_token = access_token
        self.db_path = db_path
        self.refresh_token = refresh_token

    def log(self, message):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_signal.emit(f"[{time_str}] {message}")

    def check_health(self):
        """Pings the API server to check reachability."""
        try:
            resp = requests.get(f"{self.api_base_url}/health/", timeout=3)
            return resp.status_code == 200
        except Exception:
            # Fallback to checking root or auth
            try:
                resp = requests.get(f"{self.api_base_url}/license/check/", timeout=3)
                return resp.status_code in (200, 401, 403)
            except Exception:
                return False

    def try_refresh_token(self):
        """Attempts to renew expired access token using refresh_token."""
        if not self.refresh_token:
            return False
        try:
            resp = requests.post(
                f"{self.api_base_url}/auth/refresh/",
                json={"refresh": self.refresh_token},
                timeout=4
            )
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("access", self.access_token)
                self.log("Access token refreshed successfully.")
                return True
        except Exception as e:
            self.log(f"Token refresh failed: {e}")
        return False

    def run(self):
        stats = {
            "success": False,
            "pushed_sales": 0,
            "pushed_repairs": 0,
            "pulled_repairs": 0,
            "pulled_items": 0,
            "error": None,
            "offline": False,
            "new_access_token": None,
        }

        self.status_signal.emit("Checking server connectivity...")
        is_reachable = self.check_health()
        self.connection_status_signal.emit(is_reachable)

        if not is_reachable:
            stats["offline"] = True
            stats["error"] = "Server unreachable. Running in offline mode."
            self.log("Server is currently unreachable. Transactions stored safely in local SQLite.")
            self.finished_signal.emit(stats)
            return

        if not self.access_token:
            stats["error"] = "No authentication token available for sync."
            self.log("Sync skipped: missing access token.")
            self.finished_signal.emit(stats)
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}
        conn = None

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # Test authenticated endpoint
            test_resp = requests.get(f"{self.api_base_url}/inventory/", headers=headers, timeout=4)
            if test_resp.status_code == 401:
                # Token expired, try refresh
                if self.try_refresh_token():
                    headers = {"Authorization": f"Bearer {self.access_token}"}
                    stats["new_access_token"] = self.access_token
                else:
                    stats["error"] = "Authentication expired. Please log in again."
                    self.finished_signal.emit(stats)
                    return

            self.log("Connected to server. Starting two-way synchronization...")

            # -------------------------------------------------------------
            # 1. Push Unsynced Invoices
            # -------------------------------------------------------------
            self.status_signal.emit("Pushing unsynced sales invoices...")
            cur.execute("SELECT id, items_json, summary, total_amount, date FROM invoices WHERE is_synced = 0")
            unsynced_invoices = cur.fetchall()

            for inv_id, items_json_str, summary, total_amount, date_str in unsynced_invoices:
                all_ok = True
                if items_json_str:
                    try:
                        items = json.loads(items_json_str)
                        for itm in items:
                            sale_payload = {
                                "invoice_id": str(inv_id),
                                "item_description": itm.get("description", "POS Item"),
                                "item": itm.get("server_item_id"),
                                "customer_name": "Walk-in Customer",
                                "quantity": itm.get("qty", 1),
                                "cost_price": str(itm.get("cost_unit", 0)),
                                "sale_price": str(itm.get("sale_unit", 0)),
                            }
                            resp = requests.post(
                                f"{self.api_base_url}/sales/",
                                json=sale_payload,
                                headers=headers,
                                timeout=6
                            )
                            if resp.status_code not in (200, 201):
                                all_ok = False
                                self.log(f"Server rejected item for invoice #{inv_id}: {resp.text}")
                    except Exception as e:
                        all_ok = False
                        self.log(f"Failed parsing items for invoice #{inv_id}: {e}")
                else:
                    # Single fallback record for invoice without item breakdown
                    resp = requests.post(
                        f"{self.api_base_url}/sales/",
                        json={
                            "invoice_id": str(inv_id),
                            "item_description": summary or f"Invoice #{inv_id}",
                            "customer_name": "Walk-in Customer",
                            "quantity": 1,
                            "cost_price": "0.00",
                            "sale_price": str(total_amount),
                        },
                        headers=headers,
                        timeout=6
                    )
                    if resp.status_code not in (200, 201):
                        all_ok = False

                if all_ok:
                    cur.execute("UPDATE invoices SET is_synced = 1 WHERE id = ?", (inv_id,))
                    conn.commit()
                    stats["pushed_sales"] += 1
                    self.log(f"Successfully pushed invoice #{inv_id} to server.")

            # -------------------------------------------------------------
            # 2. Push Unsynced Repairs
            # -------------------------------------------------------------
            self.status_signal.emit("Pushing unsynced repair tickets...")
            cur.execute("""
                SELECT id, customer_name, device_info, issue, cost, payment, deposit, status, server_id
                FROM repairs
                WHERE is_synced = 0
            """)
            unsynced_repairs = cur.fetchall()

            for rep in unsynced_repairs:
                r_id, cust, dev, issue, cost, pay, dep, st_raw, srv_id = rep
                st = STATUS_MAP_LEGACY.get(str(st_raw).lower(), str(st_raw).lower())

                repair_payload = {
                    "customer_name": cust or "Walk-in Customer",
                    "device_info": dev or "Unknown Device",
                    "issue_description": issue or "Hardware Diagnostic",
                    "repair_cost": str(cost or 0),
                    "customer_payment": str(pay or 0),
                    "deposit": str(dep or 0),
                    "status": st,
                }

                try:
                    if srv_id:
                        # Update existing on server
                        patch_res = requests.patch(
                            f"{self.api_base_url}/repairs/{srv_id}/",
                            json=repair_payload,
                            headers=headers,
                            timeout=6
                        )
                        if patch_res.status_code in (200, 201):
                            cur.execute("UPDATE repairs SET is_synced = 1 WHERE id = ?", (r_id,))
                            conn.commit()
                            stats["pushed_repairs"] += 1
                    else:
                        # Create new on server
                        post_res = requests.post(
                            f"{self.api_base_url}/repairs/",
                            json=repair_payload,
                            headers=headers,
                            timeout=6
                        )
                        if post_res.status_code in (200, 201):
                            new_srv_id = post_res.json().get("id")
                            cur.execute("UPDATE repairs SET is_synced = 1, server_id = ? WHERE id = ?", (new_srv_id, r_id))
                            conn.commit()
                            stats["pushed_repairs"] += 1
                            self.log(f"Pushed local repair #{r_id} -> Server ID #{new_srv_id}")
                except Exception as e:
                    self.log(f"Failed syncing repair #{r_id}: {e}")

            # -------------------------------------------------------------
            # 3. Pull Remote Repairs from Server
            # -------------------------------------------------------------
            self.status_signal.emit("Pulling repairs from server...")
            try:
                get_rep = requests.get(f"{self.api_base_url}/repairs/", headers=headers, timeout=6)
                if get_rep.status_code == 200:
                    remote_repairs = get_rep.json()
                    for r in remote_repairs:
                        r_id = r["id"]
                        cust = r.get("customer_name") or "Customer"
                        dev = r.get("device_info") or ""
                        issue = r.get("issue_description") or ""
                        cost = float(r.get("repair_cost") or 0)
                        pay = float(r.get("customer_payment") or 0)
                        dep = float(r.get("deposit") or 0)
                        profit = float(r.get("profit") or (pay - cost))
                        st = r.get("status") or "diagnosing"
                        date_str = r.get("created_at", "")[:16].replace("T", " ")

                        cur.execute("SELECT id FROM repairs WHERE server_id = ?", (r_id,))
                        existing = cur.fetchone()
                        if existing:
                            # Update local copy if already synced
                            cur.execute("""
                                UPDATE repairs
                                SET customer_name = ?, device_info = ?, issue = ?, cost = ?, payment = ?, deposit = ?, profit = ?, status = ?, is_synced = 1
                                WHERE id = ?
                            """, (cust, dev, issue, cost, pay, dep, profit, st, existing[0]))
                        else:
                            cur.execute("""
                                INSERT INTO repairs (customer_name, device_info, issue, cost, payment, deposit, profit, status, date, server_id, is_synced)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                            """, (cust, dev, issue, cost, pay, dep, profit, st, date_str, r_id))
                            stats["pulled_repairs"] += 1
                    conn.commit()
            except Exception as e:
                self.log(f"Failed pulling remote repairs: {e}")

            # -------------------------------------------------------------
            # 4. Pull Remote Inventory from Server
            # -------------------------------------------------------------
            self.status_signal.emit("Pulling inventory from server...")
            try:
                get_inv = requests.get(f"{self.api_base_url}/inventory/", headers=headers, timeout=6)
                if get_inv.status_code == 200:
                    remote_inv = get_inv.json()
                    active_server_ids = set()
                    for item in remote_inv:
                        srv_item_id = item["id"]
                        active_server_ids.add(srv_item_id)
                        desc = f"{item['brand']} {item['model']} - {item['name']}".strip()
                        cost = float(item.get("purchase_price") or 0)
                        sale = float(item.get("sale_price") or 0)
                        stock = 1 if item.get("status") != "sold" else 0

                        cur.execute("SELECT id FROM stock_items WHERE server_id = ?", (srv_item_id,))
                        existing_stock = cur.fetchone()
                        if existing_stock:
                            cur.execute("""
                                UPDATE stock_items SET description = ?, stock = ?, cost = ?, sale_price = ? WHERE id = ?
                            """, (desc, stock, cost, sale, existing_stock[0]))
                        else:
                            cur.execute("SELECT id FROM stock_items WHERE description = ?", (desc,))
                            by_desc = cur.fetchone()
                            if by_desc:
                                cur.execute("UPDATE stock_items SET server_id = ?, cost = ?, sale_price = ? WHERE id = ?", (srv_item_id, cost, sale, by_desc[0]))
                            else:
                                cur.execute("""
                                    INSERT INTO stock_items (description, stock, cost, sale_price, server_id)
                                    VALUES (?, ?, ?, ?, ?)
                                    """, (desc, stock, cost, sale, srv_item_id))
                                stats["pulled_items"] += 1

                    # Remove any items deleted from cloud for this tenant
                    cur.execute("SELECT id, server_id FROM stock_items WHERE server_id IS NOT NULL")
                    for loc_id, s_id in cur.fetchall():
                        if s_id not in active_server_ids:
                            cur.execute("DELETE FROM stock_items WHERE id = ?", (loc_id,))

                    conn.commit()
            except Exception as e:
                self.log(f"Failed pulling remote inventory: {e}")

            # -------------------------------------------------------------
            # 5. Pull Remote Sales / Invoices from Server
            # -------------------------------------------------------------
            self.status_signal.emit("Pulling sales invoices from server...")
            try:
                get_sales = requests.get(f"{self.api_base_url}/sales/", headers=headers, timeout=6)
                if get_sales.status_code == 200:
                    remote_sales = get_sales.json()
                    for sale in remote_sales:
                        s_id = str(sale.get("invoice_id") or f"sale-{sale.get('id')}")
                        s_summary = sale.get("item_name") or "Sale Invoice"
                        s_qty = int(sale.get("quantity") or 1)
                        s_total = float(sale.get("total_price") or 0)
                        s_profit = float(sale.get("profit") or 0)
                        s_date = str(sale.get("date") or "")[:16].replace("T", " ")

                        cur.execute("SELECT id FROM invoices WHERE id = ?", (s_id,))
                        if not cur.fetchone():
                            cur.execute("""
                                INSERT INTO invoices (id, summary, items_qty, total_amount, net_profit, date, is_synced)
                                VALUES (?, ?, ?, ?, ?, ?, 1)
                            """, (s_id, s_summary, s_qty, s_total, s_profit, s_date))
                    conn.commit()
            except Exception as e:
                self.log(f"Failed pulling remote sales: {e}")

            stats["success"] = True
            self.log(f"Sync complete: Pushed {stats['pushed_sales']} sales, {stats['pushed_repairs']} repairs; Pulled {stats['pulled_repairs']} repairs, {stats['pulled_items']} stock items.")

        except Exception as e:
            stats["error"] = str(e)
            self.log(f"Sync error: {e}")
        finally:
            if conn:
                conn.close()
            self.status_signal.emit("Sync finished.")
            self.finished_signal.emit(stats)
