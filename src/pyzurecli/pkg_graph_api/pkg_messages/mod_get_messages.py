from .. import _GraphAPIMethods

self: _GraphAPIMethods

async def message(self, id: str) -> dict:
    response = await self.safe_request(method="get", path=f"/me/messages/{id}")
    val = response.body.get("value")
    return val