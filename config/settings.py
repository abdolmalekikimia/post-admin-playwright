"""Global configuration for Admin Panel Playwright tests."""
import os
from dotenv import load_dotenv

load_dotenv()

# ── URLs ──────────────────────────────────────────────────
BASE_URL = os.getenv("BASE_URL", "https://example.invalid")
LOGIN_URL = f"{BASE_URL}/admin/login"
DISCREPANCIES_URL = f"{BASE_URL}/admin/discrepancies"

# ── Credentials ───────────────────────────────────────────
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "demo.user")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# ── API Endpoints ─────────────────────────────────────────
API_BASE = f"{BASE_URL}/api"
ENDPOINTS = {
    "login":              f"{API_BASE}/auth/token",
    "parcels":            f"{API_BASE}/admin/parcels",
    "parcel_details":     f"{API_BASE}/admin/parcels/{{barcode}}",
    "discrepancies":      f"{API_BASE}/admin/parcels/discrepancies",
    "edges":              f"{API_BASE}/admin/edges",
    "config_snapshots":   f"{API_BASE}/admin/configuration-snapshots",
    "devices":            f"{API_BASE}/admin/devices",
    "postal_codes":       f"{API_BASE}/admin/postal-codes",
    "bags":               f"{API_BASE}/admin/bags",
    "dispatches":         f"{API_BASE}/admin/dispatches",
}

# ── Playwright Settings ───────────────────────────────────
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30000"))
SLOW_MO = int(os.getenv("SLOW_MO", "0"))
DEFAULT_VIEWPORT = {"width": 1440, "height": 900}
# Chrome/Edge سیستمی (CDN پلی‌رایت در ایران بلاک است)
BROWSER_CHANNEL = os.getenv("BROWSER_CHANNEL") or None  # chrome | msedge

# ── Test Data ─────────────────────────────────────────────
DEFAULT_CENTER_CODE = os.getenv("DEFAULT_CENTER_CODE", "10001")
