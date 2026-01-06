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
    for delivery_item in delivery_items:
        item = {
            "quantity": delivery_item.quantity,
        }
        if delivery_item.weight is not None:
            item["weight"] = float(delivery_item.weight)
        if (
            delivery_item.length is not None
            and delivery_item.width is not None
            and delivery_item.height is not None
        ):
            item["size"] = {
                "length": float(delivery_item.length),
                "width": float(delivery_item.width),
                "height": float(delivery_item.height),
            }
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
        "requirements": {"cargo_type": "lcv_m", "taxi_class": "cargo"},
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
