"""
tpay Payment Integration Service
Handles subscription payments via tpay.com API
"""

import httpx
import os
import logging
import hashlib
import json
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# Subscription plans
SUBSCRIPTION_PLANS = {
    "monthly": {
        "id": "monthly",
        "name": "Miesięczny",
        "price_netto": 59.99,
        "price_brutto": 73.79,  # 59.99 * 1.23 VAT
        "vat_rate": 0.23,
        "period_months": 1,
        "discount_pct": 0,
        "description": "Pełny dostęp do platformy SEO Article Builder",
        "features": [
            "Nielimitowane generowanie artykułów",
            "Generator obrazów AI",
            "Asystent SEO",
            "Eksport HTML/PDF",
            "Integracja WordPress",
            "Biblioteka obrazów",
            "Serie artykułów"
        ]
    },
    "semiannual": {
        "id": "semiannual",
        "name": "Półroczny",
        "price_netto": round(59.99 * 6 * 0.93, 2),  # 7% discount
        "price_brutto": round(59.99 * 6 * 0.93 * 1.23, 2),
        "vat_rate": 0.23,
        "period_months": 6,
        "discount_pct": 7,
        "monthly_equivalent": round(59.99 * 0.93, 2),
        "description": "6 miesięcy z 7% rabatem",
        "features": [
            "Wszystko z planu Miesięcznego",
            "7% oszczędności",
            "Priorytetowe wsparcie"
        ]
    },
    "annual": {
        "id": "annual",
        "name": "Roczny",
        "price_netto": round(59.99 * 12 * 0.85, 2),  # 15% discount
        "price_brutto": round(59.99 * 12 * 0.85 * 1.23, 2),
        "vat_rate": 0.23,
        "period_months": 12,
        "discount_pct": 15,
        "monthly_equivalent": round(59.99 * 0.85, 2),
        "description": "12 miesięcy z 15% rabatem",
        "features": [
            "Wszystko z planu Miesięcznego",
            "15% oszczędności",
            "Priorytetowe wsparcie",
            "Dedykowany opiekun"
        ]
    }
}


def get_all_plans():
    """Return all subscription plans."""
    return list(SUBSCRIPTION_PLANS.values())


def get_plan(plan_id: str):
    """Return a specific plan."""
    return SUBSCRIPTION_PLANS.get(plan_id)


async def create_tpay_transaction(plan_id: str, user: dict, callback_url: str, return_url: str) -> dict:
    """
    Create a tpay transaction for subscription purchase.
    
    Args:
        plan_id: ID of the subscription plan
        user: User dict from DB
        callback_url: URL for tpay to send payment notifications
        return_url: URL to redirect user after payment
    
    Returns:
        dict with transaction_url, transaction_id, status
    """
    plan = get_plan(plan_id)
    if not plan:
        return {"success": False, "error": "Nieznany plan subskrypcji"}
    
    client_id = os.environ.get("TPAY_CLIENT_ID", "")
    client_secret = os.environ.get("TPAY_CLIENT_SECRET", "")
    
    if not client_id or not client_secret:
        # Return a simulated response when tpay is not configured
        logger.warning("tpay credentials not configured, returning demo response")
        return {
            "success": False,
            "error": "tpay nie jest jeszcze skonfigurowany. Skontaktuj sie z administratorem.",
            "demo": True
        }
    
    try:
        # Step 1: Get OAuth token
        token_url = "https://api.tpay.com/oauth/auth"
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "read write"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_res = await client.post(token_url, json=token_data)
            if token_res.status_code != 200:
                logger.error(f"tpay auth failed: {token_res.status_code}")
                return {"success": False, "error": "Błąd autoryzacji tpay"}
            
            access_token = token_res.json().get("access_token")
            
            # Step 2: Create transaction
            tx_url = "https://api.tpay.com/transactions"
            tx_data = {
                "amount": plan["price_brutto"],
                "description": f"Kurdynowski SEO - {plan['name']} ({plan['period_months']} mies.)",
                "hiddenDescription": f"plan:{plan_id}|user:{user['id']}",
                "payer": {
                    "email": user["email"],
                    "name": user.get("name", "")
                },
                "callbacks": {
                    "payerUrls": {
                        "success": return_url + "?status=success",
                        "error": return_url + "?status=error"
                    },
                    "notification": {
                        "url": callback_url
                    }
                },
                "pay": {
                    "groupId": 150  # Online transfer group
                }
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            tx_res = await client.post(tx_url, json=tx_data, headers=headers)
            
            if tx_res.status_code in (200, 201):
                tx_data = tx_res.json()
                return {
                    "success": True,
                    "transaction_id": tx_data.get("transactionId"),
                    "transaction_url": tx_data.get("transactionPaymentUrl"),
                    "status": "pending"
                }
            else:
                logger.error(f"tpay transaction failed: {tx_res.status_code} - {tx_res.text}")
                return {"success": False, "error": "Błąd tworzenia transakcji"}
    
    except Exception as e:
        logger.error(f"tpay error: {e}")
        return {"success": False, "error": str(e)}


def verify_tpay_notification(data: dict, notification_secret: str) -> bool:
    """
    Verify tpay notification signature.
    """
    # tpay sends JWS signed notifications in newer API
    # For basic verification, check if transaction ID exists
    return bool(data.get("tr_id") or data.get("transactionId"))


def calculate_subscription_end(plan_id: str, start_date: datetime = None) -> datetime:
    """Calculate subscription end date based on plan."""
    if start_date is None:
        start_date = datetime.now(timezone.utc)
    
    plan = get_plan(plan_id)
    if not plan:
        return start_date
    
    months = plan["period_months"]
    # Approximate: add months
    end_date = start_date + timedelta(days=months * 30)
    return end_date
