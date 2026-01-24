import aiohttp
from app.settings import settings

import logging

default_logger = logging.getLogger(__name__)


class TgLogger:
    BOT_TOKEN = settings.TG_LOG_BOT_KEY
    CHAT_ID = settings.TG_LOG_CHAT_ID

    async def _request(self, message: str):
        if self.BOT_TOKEN and self.CHAT_ID:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage",
                        json={
                            "chat_id": self.CHAT_ID,
                            "text": message[:4096],
                            "parse_mode": "MarkDown",
                        },
                        headers={"Content-Type": "application/json"},
                    ) as response:
                        if response.status != 200:
                            print(
                                "Error sending Telegram message status:",
                                response.status,
                                await response.json(),
                            )
                except Exception as e:
                    print("Error sending Telegram message:", e)

    async def info(self, message: str):
        print(message)
        # default_logger.info(message)
        await self._request("INFO\n" + message)

    async def warning(self, message: str):
        print(message)
        # default_logger.warning(message)
        await self._request("WARNING\n" + message)

    async def error(self, message: str):
        print(message)
        # default_logger.error(message)
        await self._request("ERROR\n" + message)


logger = TgLogger()
