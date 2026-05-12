import uuid
from bot.config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY


def create_yookassa_payment(amount: float, description: str, return_url: str = "https://t.me/") -> dict | None:
    try:
        import yookassa
        from yookassa import Payment, Configuration
        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY

        payment = Payment.create({
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,
            "description": description,
        }, uuid.uuid4())

        return {
            "id": payment.id,
            "url": payment.confirmation.confirmation_url,
            "status": payment.status,
        }
    except Exception as e:
        print(f"YooKassa error: {e}")
        return None


def check_yookassa_payment(payment_id: str) -> str:
    try:
        import yookassa
        from yookassa import Payment, Configuration
        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY
        payment = Payment.find_one(payment_id)
        return payment.status
    except Exception as e:
        print(f"YooKassa check error: {e}")
        return "error"
