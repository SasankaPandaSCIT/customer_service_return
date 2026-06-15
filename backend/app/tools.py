from langchain_core.tools import tool
from app.utils import load_crm_data, get_refund_policy, format_orders

@tool
def get_customer_info(customer_id: str) -> str:
    """Finds a customer by their Customer ID in the CRM and returns their recent orders."""
    crm_data = load_crm_data()
    for customer in crm_data.get("customers", []):
        if customer["customer_id"].upper() == customer_id.upper():
            orders_str = format_orders(customer.get("orders", []))
            return f"Customer ID: {customer['customer_id']}\nName: {customer['name']}\nRecent Orders:\n{orders_str}"
    return "Customer not found."

@tool
def get_order_details(order_id: str) -> str:
    """Fetches details for a specific order ID."""
    crm_data = load_crm_data()
    for customer in crm_data.get("customers", []):
        for order in customer.get("orders", []):
            if order["order_id"].upper() == order_id.upper():
                return f"Order ID: {order['order_id']}\nItem: {order['item_name']}\nCategory: {order['category']}\nPurchase Date: {order['purchase_date']}\nAmount: ${order['amount']}"
    return "Order not found."

@tool
def process_refund(order_id: str) -> str:
    """Mocks processing a refund in the system."""
    return f"SUCCESS: Refund for order {order_id} has been processed back to the original payment method."

@tool
def deny_refund(order_id: str, reason: str) -> str:
    """Mocks denying a refund in the system with a logged reason."""
    return f"DENIED: Refund for order {order_id} has been denied. Reason logged: {reason}."

@tool
def check_policy() -> str:
    """Returns the full synthetic refund policy text."""
    return get_refund_policy()
