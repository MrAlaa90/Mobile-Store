import sys
import requests

API_URL = "http://127.0.0.1:8000/api"

def log(msg):
    print(f"[MOBILE-CONTRACT] {msg}")

def verify_mobile_contract():
    print("=" * 65)
    print("  VERIFYING FLUTTER MOBILE APP <-> DJANGO API CONTRACT")
    print("=" * 65)

    # 1. Healthcheck endpoint
    log("Checking /health/ for mobile ping test...")
    r = requests.get(f"{API_URL}/health/", timeout=5)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    log("✅ /health/ responds with 200 OK")

    # 2. Login endpoint for AuthProvider
    log("Checking /auth/login/ for AuthProvider...")
    r = requests.post(f"{API_URL}/auth/login/", json={"username": "admin", "password": "admin123"}, timeout=5)
    assert r.status_code == 200, f"Login failed: {r.text}"
    tokens = r.json()
    assert "access" in tokens and "refresh" in tokens, "Missing tokens"
    access_token = tokens["access"]
    refresh_token = tokens["refresh"]
    log("✅ /auth/login/ returns valid JWT access and refresh tokens")

    # 3. Refresh token for ApiService.refreshToken()
    log("Checking /auth/refresh/...")
    r = requests.post(f"{API_URL}/auth/refresh/", json={"refresh": refresh_token}, timeout=5)
    assert r.status_code == 200, f"Refresh failed: {r.text}"
    assert "access" in r.json(), "Missing refreshed access token"
    log("✅ /auth/refresh/ successfully renews access token")

    headers = {"Authorization": f"Bearer {access_token}"}

    # 4. Inventory endpoint for InventoryModel & InventoryProvider
    log("Checking /inventory/ for InventoryModel...")
    r = requests.get(f"{API_URL}/inventory/", headers=headers, timeout=5)
    assert r.status_code == 200
    items = r.json()
    assert len(items) > 0, "No inventory items"
    first_inv = items[0]
    for key in ["id", "name", "brand", "model", "purchase_price", "sale_price", "status"]:
        assert key in first_inv, f"InventoryModel missing key '{key}' in API"
    log(f"✅ /inventory/ contract verified: {len(items)} items matching InventoryModel schema")

    # 5. Repairs endpoint for RepairModel & RepairsProvider
    log("Checking /repairs/ for RepairModel...")
    r = requests.get(f"{API_URL}/repairs/", headers=headers, timeout=5)
    assert r.status_code == 200
    repairs = r.json()
    assert len(repairs) > 0, "No repair tickets"
    first_rep = repairs[0]
    for key in ["id", "customer_name", "device_info", "issue_description", "repair_cost", "customer_payment", "deposit", "status"]:
        assert key in first_rep, f"RepairModel missing key '{key}' in API"
    log(f"✅ /repairs/ contract verified: {len(repairs)} tickets matching RepairModel schema")

    # 6. Sales endpoint for SaleModel & SalesProvider
    log("Checking /sales/ for SaleModel...")
    r = requests.get(f"{API_URL}/sales/", headers=headers, timeout=5)
    assert r.status_code == 200
    sales = r.json()
    assert len(sales) > 0, "No sales records"
    first_sale = sales[0]
    for key in ["id", "invoice_id", "item_description", "customer_name", "quantity", "cost_price", "sale_price", "profit"]:
        assert key in first_sale, f"SaleModel missing key '{key}' in API"
    log(f"✅ /sales/ contract verified: {len(sales)} records matching SaleModel schema")

    # 7. Customers endpoint for CustomerModel
    log("Checking /customers/ for CustomerModel...")
    r = requests.get(f"{API_URL}/customers/", headers=headers, timeout=5)
    assert r.status_code == 200
    customers = r.json()
    assert len(customers) > 0, "No customers"
    first_cust = customers[0]
    for key in ["id", "name", "phone"]:
        assert key in first_cust, f"CustomerModel missing key '{key}' in API"
    log(f"✅ /customers/ contract verified: {len(customers)} customers matching CustomerModel schema")

    print("\n" + "=" * 65)
    print("  SUCCESS: 7/7 MOBILE API CONTRACT CHECKS PASSED PERFECTLY!")
    print("=" * 65)

if __name__ == "__main__":
    verify_mobile_contract()
