"""PayFast payment integration utilities."""

import hashlib
import logging
import urllib.parse

from flask import current_app

logger = logging.getLogger(__name__)

PAYFAST_SANDBOX_URL = "https://sandbox.payfast.co.za/eng/process"
PAYFAST_LIVE_URL = "https://www.payfast.co.za/eng/process"


def get_payfast_url():
    """Return the PayFast URL based on sandbox setting."""
    if current_app.config.get("PAYFAST_SANDBOX", True):
        return PAYFAST_SANDBOX_URL
    return PAYFAST_LIVE_URL


def build_payment_data(order, return_url, cancel_url, notify_url):
    """Build the PayFast payment form data."""
    data = {
        "merchant_id": current_app.config["PAYFAST_MERCHANT_ID"],
        "merchant_key": current_app.config["PAYFAST_MERCHANT_KEY"],
        "return_url": return_url,
        "cancel_url": cancel_url,
        "notify_url": notify_url,
        "m_payment_id": order.order_number,
        "amount": f"{order.total:.2f}",
        "item_name": f"Order #{order.order_number}",
        "email_address": order.customer.email,
    }
    return data


def generate_signature(data):
    """Generate MD5 signature for PayFast data."""
    passphrase = current_app.config.get("PAYFAST_PASSPHRASE", "")

    # Build param string
    pf_output = ""
    for key, val in data.items():
        if val:
            pf_output += f"{key}={urllib.parse.quote_plus(str(val).strip())}&"
    pf_output = pf_output[:-1]  # Remove trailing &

    if passphrase:
        pf_output += f"&passphrase={urllib.parse.quote_plus(passphrase.strip())}"

    return hashlib.md5(pf_output.encode()).hexdigest()


def verify_payment(post_data):
    """Verify a PayFast ITN (Instant Transaction Notification)."""
    param_string = ""
    for key, val in sorted(post_data.items()):
        if key != "signature":
            param_string += f"{key}={urllib.parse.quote_plus(str(val))}&"
    param_string = param_string[:-1]

    passphrase = current_app.config.get("PAYFAST_PASSPHRASE", "")
    if passphrase:
        param_string += f"&passphrase={urllib.parse.quote_plus(passphrase)}"

    computed_sig = hashlib.md5(param_string.encode()).hexdigest()
    return computed_sig == post_data.get("signature", "")
