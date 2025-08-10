
from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class DonationType(str, Enum):
    Donation = "Donation"
    Subscription = "Subscription"
    Commission = "Commission"
    ShopOrder = "Shop Order"

class KofiShopItem(BaseModel):
    direct_link_code: str
    variation_name: str
    quantity: int
    
class KofiShippingAddress(BaseModel):
    full_name: str
    street_address: str
    city: str
    state_or_province: str
    postal_code: str
    country: str
    country_code: str
    telephone: str

class KofiWebhookData(BaseModel):
    type: DonationType
    verification_token: str
    message_id: str
    timestamp: str
    is_public: bool
    from_name: str
    message: str
    amount: str
    url: str
    email: str
    currency: str
    is_subscription_payment: bool
    is_first_subscription_payment: bool
    kofi_transaction_id: str
    shop_items: List[KofiShopItem] | None = None
    shipping: KofiShippingAddress | None = None
    tier_name: str | None = None
