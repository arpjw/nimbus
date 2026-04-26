import os

from slack_sdk.web.async_client import AsyncWebClient


class SlackApp:
    def __init__(self):
        self._client = AsyncWebClient(token=os.environ.get("SLACK_BOT_TOKEN", ""))

    async def post_message(self, channel: str, text: str, blocks: list | None = None) -> str:
        kwargs: dict = {"channel": channel, "text": text}
        if blocks:
            kwargs["blocks"] = blocks
        resp = await self._client.chat_postMessage(**kwargs)
        return resp["ts"]

    async def post_thread_reply(self, channel: str, thread_ts: str, text: str) -> None:
        await self._client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=text,
        )

    async def get_channel_info(self, channel_id: str) -> dict:
        resp = await self._client.conversations_info(channel=channel_id)
        channel = resp["channel"]
        return {
            "id": channel["id"],
            "name": channel.get("name", ""),
            "is_private": channel.get("is_private", False),
        }
