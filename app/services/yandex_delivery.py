from decimal import Decimal
from typing import List
import aiohttp
from app.services.schemas import DeliveryItem
from app.settings import settings


async def get_yandex_delivery_price(
    delivery_items: List[DeliveryItem], latitude: float, longitude: float
) -> Decimal:
    url = "https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/check-price"
    headers = {
        "Content-Type": "application/json",
        "Accept-Language": "ru",
        "Authorization": f"Bearer {settings.YANDEX_DELIVERY_API_KEY}",
    }
    items = []
    cargo_type_weight = {
        "van": 1000,
        "lcv_m": 2000,
        "lcv_l": 4000,
        "lcv_xl": 8000,
    }
    cargo_type = None
    current_max_weight = 0
    for delivery_item in delivery_items:
        item = {
            "quantity": delivery_item.quantity,
        }
        if (
            delivery_item.cargo_type
            and cargo_type_weight.get(delivery_item.cargo_type, 0) > current_max_weight
        ):
            cargo_type = delivery_item.cargo_type
            current_max_weight = cargo_type_weight[delivery_item.cargo_type]

        items.append(item)
    payload = {
        "items": items,
        "route_points": [
            {"coordinates": [30.271168, 60.019356]},  # Квартира Лехи
            {
                "coordinates": [
                    float(longitude),
                    float(latitude),
                ]
            },
        ],
        "requirements": {"cargo_type": cargo_type, "taxi_class": "cargo"},
    }
    print("Yandex delivery request payload:", payload)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                data = await response.json()
                print("Yandex delivery response status:", response.status)
                print("Yandex delivery response data:", data)
                if response.status == 200:
                    price = data.get("price", 0)
                    return Decimal(price)
                else:
                    return Decimal()
    except Exception as e:
        print("Error fetching Yandex delivery price:", e)
        return Decimal()
