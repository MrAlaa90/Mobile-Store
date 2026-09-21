import sys
import time
import requests

BACKEND_BASE = "http://localhost:8000"
FRONTEND_BASE = "http://localhost:3000"

def log(msg):
    print(f"[TEST] {msg}")

def test_docker_stack():
    print("=" * 65)
    print("  MOBILE-STORE DOCKER COMPOSE INTEGRATION & VERIFICATION TEST")
    print("=" * 65)

    passed = 0
    total = 6

    # 1. Healthcheck
    log("Step 1: Pinging Django API healthcheck endpoint...")
    try:
        r = requests.get(f"{BACKEND_BASE}/api/health/", timeout=5)
        if r.status_code == 200:
            data = r.json()
            log(f"✅ Healthcheck OK: status={data.get('status')} service={data.get('service')}")
            passed += 1
        else:
            log(f"❌ Healthcheck returned status {r.status_code}")
    except Exception as e:
        log(f"❌ Could not connect to Django API: {e}")

    # 2. Authentication with Seeded Admin
    log("\nStep 2: Authenticating with seeded admin credentials (admin / admin123)...")
    tokens = {}
    try:
        r = requests.post(f"{BACKEND_BASE}/api/auth/login/", json={"username": "admin", "password": "admin123"}, timeout=5)
        if r.status_code == 200:
            tokens = r.json()
            log("✅ Authentication SUCCESS: JWT access token obtained.")
            passed += 1
        else:
            log(f"❌ Auth failed with status {r.status_code}: {r.text}")
    except Exception as e:
        log(f"❌ Auth request failed: {e}")

    headers = {"Authorization": f"Bearer {tokens.get('access')}"} if tokens.get("access") else {}

    # 3. Inventory in PostgreSQL
    log("\nStep 3: Querying inventory items from PostgreSQL...")
    try:
        r = requests.get(f"{BACKEND_BASE}/api/inventory/", headers=headers, timeout=5)
        if r.status_code == 200:
            items = r.json()
            log(f"✅ Inventory query SUCCESS: Retrieved {len(items)} items from PostgreSQL.")
            for itm in items[:3]:
                log(f"   - {itm.get('brand')} {itm.get('model')} ({itm.get('name')}) | ${itm.get('sale_price')}")
            passed += 1
        else:
            log(f"❌ Inventory query returned status {r.status_code}")
    except Exception as e:
        log(f"❌ Inventory query failed: {e}")

    # 4. Repair Tickets in PostgreSQL
    log("\nStep 4: Querying repair tickets from PostgreSQL...")
    try:
        r = requests.get(f"{BACKEND_BASE}/api/repairs/", headers=headers, timeout=5)
        if r.status_code == 200:
            repairs = r.json()
            log(f"✅ Repairs query SUCCESS: Retrieved {len(repairs)} tickets from PostgreSQL.")
            for rep in repairs[:3]:
                log(f"   - #{rep.get('id')} {rep.get('customer_name')} | {rep.get('device_info')} | Status: {rep.get('status')}")
            passed += 1
        else:
            log(f"❌ Repairs query returned status {r.status_code}")
    except Exception as e:
        log(f"❌ Repairs query failed: {e}")

    # 5. Customers in PostgreSQL
    log("\nStep 5: Querying customer database...")
    try:
        r = requests.get(f"{BACKEND_BASE}/api/customers/", headers=headers, timeout=5)
        if r.status_code == 200:
            customers = r.json()
            log(f"✅ Customers query SUCCESS: Retrieved {len(customers)} customers.")
            passed += 1
        else:
            log(f"❌ Customers query returned status {r.status_code}")
    except Exception as e:
        log(f"❌ Customers query failed: {e}")

    # 6. React Frontend HTML
    log("\nStep 6: Checking React Dashboard frontend (port 3000 / port 5173)...")
    frontend_ok = False
    for port in [3000, 5173]:
        try:
            r = requests.get(f"http://localhost:{port}", timeout=4)
            if r.status_code == 200 and ("root" in r.text or "html" in r.text or "doctype" in r.text.lower()):
                tag = "Docker Compose Port" if port == 3000 else "Local Dev Server Port"
                log(f"✅ Frontend Web Server SUCCESS on port {port} ({tag}): Serving React application (HTTP 200).")
                frontend_ok = True
                passed += 1
                break
        except Exception:
            continue

    if not frontend_ok:
        log("❌ Frontend connection failed on both port 3000 (Docker) and port 5173.")

    print("\n" + "=" * 65)
    print(f"  VERIFICATION RESULTS: {passed}/{total} CHECKS PASSED")
    print("=" * 65)

    return passed == total

if __name__ == "__main__":
    success = test_docker_stack()
    sys.exit(0 if success else 1)
