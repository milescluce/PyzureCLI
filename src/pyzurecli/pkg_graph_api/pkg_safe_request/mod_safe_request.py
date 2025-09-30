from toomanyconfigs.simple_api import SimpleAPIResponse

from .. import _GraphAPIInit


def error_handling(response: SimpleAPIResponse):
    if error := response.body.get("error"):
        code = error["code"]
        msg = error["message"]
        msg = f"{code}: {msg}"
        if code == 400:
            raise ConnectionRefusedError(msg)  # Can't process the request because it's malformed or incorrect.
        elif code == 401:
            raise PermissionError(
                msg)  # Required authentication information is either missing or not valid for the resource.
        elif code == "InvalidAuthenticationToken":
            raise PermissionError(msg)
        elif code == 403:
            raise PermissionError(
                msg)  # Access is denied to the requested resource. The user does not have enough permission or does not have a required license.
        else:
            raise ConnectionError(msg)
    return response


async def safe_request(self, method: str, path: str, **kwargs) -> SimpleAPIResponse:
    self: _GraphAPIInit
    try:
        response = await self.async_request(method, path, **kwargs)
        return error_handling(response)
    except Exception:
        raise


def sync_safe_request(self, method: str, path: str, **kwargs) -> SimpleAPIResponse:
    self: _GraphAPIInit
    try:
        response = self.request(method, path, **kwargs)
        return error_handling(response)
    except Exception:
        raise
