import uuid
from decimal import Decimal

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse


class CashfreeAPIError(Exception):
    """Raised when Cashfree API fails or cannot be reached."""


def _cashfree_base_url():
    environment = getattr(settings, "CASHFREE_ENVIRONMENT", "sandbox").lower()

    if environment in ["production", "prod", "live"]:
        return "https://api.cashfree.com/pg"

    return "https://sandbox.cashfree.com/pg"


def _headers():
    client_id = getattr(settings, "CASHFREE_CLIENT_ID", "")
    client_secret = getattr(settings, "CASHFREE_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        raise ImproperlyConfigured(
            "Cashfree credentials are missing. Set CASHFREE_CLIENT_ID and CASHFREE_CLIENT_SECRET."
        )

    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-version": getattr(settings, "CASHFREE_API_VERSION", "2025-01-01"),
        "x-client-id": client_id,
        "x-client-secret": client_secret,
        "x-request-id": str(uuid.uuid4()),
        "x-idempotency-key": str(uuid.uuid4()),
    }


def _amount(value: Decimal) -> float:
    return float(Decimal(value).quantize(Decimal("0.01")))


def _send_request(method, url, **kwargs):
    try:
        response = requests.request(method, url, timeout=25, **kwargs)
    except requests.exceptions.RequestException as exc:
        raise CashfreeAPIError(
            "Unable to connect to Cashfree. Please check your internet connection, DNS, proxy, firewall, or try another network/hotspot."
        ) from exc

    if not response.ok:
        try:
            error_body = response.json()
        except ValueError:
            error_body = response.text

        raise CashfreeAPIError(
            f"Cashfree API error: {response.status_code} - {error_body}"
        )

    try:
        return response.json()
    except ValueError as exc:
        raise CashfreeAPIError("Cashfree returned an invalid response.") from exc


def create_order(booking, request):
    return_url = request.build_absolute_uri(reverse("payment_return")) + f"?order_id={booking.pnr}"
    notify_url = request.build_absolute_uri(reverse("cashfree_webhook"))

    user = booking.user

    customer_name = user.get_full_name() or user.username
    customer_email = user.email or getattr(
        settings,
        "CASHFREE_DEFAULT_CUSTOMER_EMAIL",
        "customer@example.com"
    )
    customer_phone = getattr(
        settings,
        "CASHFREE_DEFAULT_CUSTOMER_PHONE",
        "9999999999"
    )

    payload = {
        "order_id": booking.pnr,
        "order_amount": _amount(booking.total_amount),
        "order_currency": getattr(settings, "CASHFREE_ORDER_CURRENCY", "INR"),
        "customer_details": {
            "customer_id": f"user_{user.pk}",
            "customer_name": customer_name[:100],
            "customer_email": customer_email,
            "customer_phone": customer_phone,
        },
        "order_meta": {
            "return_url": return_url,
            "notify_url": notify_url,
        },
        "order_note": f"{booking.get_booking_type_display()} booking {booking.pnr}",
        "order_tags": {
            "pnr": booking.pnr,
            "booking_type": booking.booking_type,
        },
    }

    return _send_request(
        "POST",
        f"{_cashfree_base_url()}/orders",
        json=payload,
        headers=_headers(),
    )


def fetch_order(order_id):
    return _send_request(
        "GET",
        f"{_cashfree_base_url()}/orders/{order_id}",
        headers=_headers(),
    )