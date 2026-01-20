from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Awaitable, List, Literal, Optional, Type

import aiohttp

from app.orders.models import Order
from app.orders.schemas import ProviderOrderInfo, SerializedResponse
from app.services.logger import logger


class ProviderClientBase(ABC):
    @abstractmethod
    async def request_deposit(
        self, order: Type[Order]
    ) -> Awaitable[SerializedResponse[ProviderOrderInfo]]:
        "Запрос к провайдеру на создание депозита"

    @classmethod
    def parse_callback_data(cls, request_data: dict) -> ProviderOrderInfo:
        "This method is used when receiving callback from merchant"
        raise NotImplementedError("Webhook is not supported for this provider.")

    @abstractmethod
    async def get_order_info(
        self, order: Order
    ) -> Awaitable[SerializedResponse[ProviderOrderInfo]]:
        "This method is used to get order status from merchant"

    @classmethod
    def _get_param(cls, params: dict, param_name: str):
        for k, v in params.items():
            if k == param_name:
                return v
            if v is dict:
                item = cls._get_param(v, param_name)
                if item or item == 0:
                    return item
        return None

    async def _request(
        self,
        url,
        method: Literal["GET", "POST"] = "POST",
        params=None,
        data=None,
        json=None,
        headers=None,
        order_id=None,
        log=True,
        timeout=20,
    ) -> SerializedResponse:
        success = True
        result_data = {}
        error = ""
        response = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, json=json, data=data, headers=headers, timeout=timeout
                ) as response:
                    result_data = await response.json()
                    if not response.status < 300:
                        success = False
                        error = f"Http статус ответа {response.status}. Body ответа: {result_data}"
        except Exception as err:
            error = f"Ошибка: {err}"
            success = False
        if log:
            logger.info(
                (f"Заявка № {order_id}\n" if order_id else "")
                + f"{'Успешный' if success else 'Неудачный'} запрос к платежной системе {self.__class__.__name__}\n"
                + "Параметры запроса:\n"
                + f"- URL: {url}\n"
                + f"- METHOD: {method}\n"
                + f"- Заголовки: {headers}\n"
                + f"- DATA: {params or data or json}\n"
                + "\nПараметры ответа:\n"
                + f"- Статус: {response.status if response else ''}\n"
                + f"- DATA: {result_data}\n"
                + f"- Ошибка: {error}"
            )
        return SerializedResponse(
            success=success,
            raw_data=result_data,
            error=error,
            status_code=response.status if response else None,
        )
