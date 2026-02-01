from decimal import Decimal
from typing import Awaitable, Type
import base64
import hashlib

from app.settings import settings
from app.orders.models import Order, OrderStatus
from app.orders.schemas import MerchantData, ProviderOrderInfo, SerializedResponse
from app.services.payment_systems.base import ProviderClientBase
from app.services.redis import redis_client


class Paykeeper(ProviderClientBase):
    URL = "https://237200454513.server.paykeeper.ru/"
    USER = settings.PAYKEEPER_USER
    PASSWORD = settings.PAYKEEPER_PASSWORD
    SECRET = settings.PAYKEEPER_SECRET
    STATUS_MAPPER = {
        "created": OrderStatus.CREATED,
        "sent": OrderStatus.CREATED,
        "paid": OrderStatus.PAID,
        "expired": OrderStatus.ERROR,
    }

    async def _make_request(
        self,
        resource,
        method="GET",
        params=None,
        data=None,
        order_id=None,
    ) -> SerializedResponse:
        url = f"{self.URL}{resource}"
        basic_auth = base64.b64encode(f"{self.USER}:{self.PASSWORD}".encode()).decode()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {basic_auth}",
        }
        if method == "POST":
            token = await redis_client.get("paykeeper_token")
            if not token:
                response = await self._request(
                    f"{self.URL}info/settings/token/",
                    "GET",
                    headers=headers,
                    log=False,
                )
                token = self._get_param(response.raw_data, "token")
                if token:
                    await redis_client.set("paykeeper_token", token, 12 * 60 * 60)
            if data:
                data["token"] = token
        return await self._request(
            url=url,
            method=method,
            headers=headers,
            data=data,
            params=params,
            order_id=order_id,
        )

    async def request_deposit(
        self, order: Type[Order]
    ) -> SerializedResponse[ProviderOrderInfo]:
        "Запрос к платежке на создание депозита"
        resource = "change/invoice/preview/"
        body = {
            "pay_amount": order.get_prepayment_amount(),
            "clientid": order.detail.first_name,
            "orderid": order.id,
            "client_email": order.detail.email,
            "service_name": "Покупка товаров",
            "client_phone": order.detail.phone,
        }

        res: SerializedResponse = await self._make_request(
            resource=resource, method="POST", data=body, order_id=order.id
        )
        if not self._get_param(res.raw_data, "invoice_id"):
            res.success = False
            res.error = f"Реквизиты не найдены.\n {res.raw_data}"
        elif res.success:
            res.serialized_data = ProviderOrderInfo(
                order_id=order.id,
                provider_order_id=self._get_param(res.raw_data, "invoice_id"),
                status=OrderStatus.CREATED,
                merchant_data=MerchantData(
                    payment_url=self._get_param(res.raw_data, "invoice_url"),
                ),
            )
        return res

    @classmethod
    def parse_callback_data(cls, request_data: dict) -> ProviderOrderInfo:
        "This method is used when receiving callback from merchant"
        return ProviderOrderInfo(
            order_id=cls._get_param(request_data, "orderid"),
            provider_order_id=cls._get_param(request_data, "id"),
            status=OrderStatus.SUCCESS,
            amount_actual=Decimal(cls._get_param(request_data, "sum")),
        )

    async def get_order_info(
        self, order: Order
    ) -> SerializedResponse[ProviderOrderInfo]:
        "This method is used to get order status from merchant"
        if not order.external_id:
            return SerializedResponse(
                success=False,
                error="external order id необходим для получения информации по заявке",
            )
        resource = f"info/invoice/byid/?id={order.external_id}"

        res: SerializedResponse = await self._make_request(
            resource=resource, method="GET", order_id=order.id
        )
        if res.success:
            res.serialized_data = ProviderOrderInfo(
                order_id=order.id,
                provider_order_id=self._get_param(res.raw_data, "id"),
                status=self.STATUS_MAPPER.get(
                    self._get_param(res.raw_data, "status"),
                    OrderStatus.ERROR,
                ),
                amount_actual=Decimal(self._get_param(res.raw_data, "pay_amount")),
            )
        return res

    def check_webhook(self, data: dict) -> bool:
        string_to_sign = ""
        for k, v in data.items():
            if k in ["id", "sum", "clientid", "orderid"]:
                string_to_sign += str(v)
        string_to_sign += self.SECRET
        sign = hashlib.md5(string_to_sign.encode()).hexdigest()
        return sign == data["key"]

    def get_callback_response(self, provider_order_id: str) -> str:
        sign = hashlib.md5((provider_order_id + self.SECRET).encode()).hexdigest()
        return f"OK {sign}"
