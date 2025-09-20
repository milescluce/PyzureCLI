from typing import Annotated

from . import _GraphAPIMethods, is_valid_email_regex
from .. import debug, validate_range
from ..pkg_type_check_emails import type_check_emails

async def list_received_messages_from_person(self: _GraphAPIMethods, person: str, top: Annotated[int, validate_range(1, 999)] = 999):
    if not is_valid_email_regex(person): raise TypeError("Not a valid email, got {person} instead")
    response = await self.safe_request(
        method="GET",
        path=f"/me/messages?$filter=(from/emailAddress/address) eq '{person}'&$select={self.email_filters}&$top={top}"
    )
    return type_check_emails(response.body)

async def list_sent_messages_to_person(self: _GraphAPIMethods, person: str, top: Annotated[int, validate_range(1, 999)] = 999):
    if not is_valid_email_regex(person): raise TypeError("Not a valid email, got {person} instead")
    response = await self.safe_request(
        method="GET",
        path=f'https://graph.microsoft.com/v1.0/me/mailFolders/SentItems/messages?$search="to:{person}"&$select={self.email_filters}&$top={top}'
    )
    return type_check_emails(response.body)

async def list_messages_with_person(self: _GraphAPIMethods, person: str, top: Annotated[int, validate_range(1, 999)] = 999) -> dict:
    if not is_valid_email_regex(person): raise TypeError("Not a valid email, got {person} instead")
    msgs_from = await self.list_received_messages_from_person(person, top)
    if not msgs_from: msgs_from = []
    msgs_to = await self.list_sent_messages_to_person(person, top)
    if not msgs_to: msgs_to = []
    total = {
        "messages_from": msgs_from,
        "messages_to": msgs_to
    }
    top = len(msgs_from) + len(msgs_to)
    debug(f"Found {top} messages with {person}")
    return total