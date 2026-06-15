import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CRM_FILE = DATA_DIR / "crm.json"
POLICY_FILE = DATA_DIR / "refund_policy.md"

def load_crm_data():
    """Loads the synthetic CRM database."""
    try:
        with open(CRM_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"customers": []}

def get_refund_policy():
    """Reads the synthetic refund policy markdown document."""
    try:
        with open(POLICY_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Refund policy not found."

def format_orders(orders):
    """Utility to format a list of orders into a readable string."""
    if not orders:
        return "No recent orders."
    lines = []
    for o in orders:
        lines.append(f"- Order ID: {o['order_id']}, Item: {o['item_name']} (Category: {o['category']}), Date: {o['purchase_date']}, Amount: ${o['amount']}")
    return "\n".join(lines)
