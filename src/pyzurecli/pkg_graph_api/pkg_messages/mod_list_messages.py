from . import _GraphAPIMethods, is_valid_email_regex
from .. import debug
from ..pkg_type_check_emails import type_check_emails

def list_received_messages_from_person(self: _GraphAPIMethods, person: str):
    if not is_valid_email_regex(person): raise TypeError("Not a valid email, got {person} instead")
    response = self.safe_request(
        method="GET",
        path=f"/me/messages?$filter=(from/emailAddress/address) eq '{person}'"
    )
    return type_check_emails(response)

def list_sent_messages_to_person(self: _GraphAPIMethods, person: str):
    if not is_valid_email_regex(person): raise TypeError("Not a valid email, got {person} instead")
    response = self.safe_request(
        method="GET",
        path=f'https://graph.microsoft.com/v1.0/me/mailFolders/SentItems/messages?$search="to:{person}"&$top=999'
    )
    return type_check_emails(response)

def list_messages_with_person(self: _GraphAPIMethods, person: str) -> dict:
    if not is_valid_email_regex(person): raise TypeError("Not a valid email, got {person} instead")
    msgs_from = self.list_received_messages_from_person(person)
    if not msgs_from: msgs_from = []
    msgs_to = self.list_sent_messages_to_person(person)
    if not msgs_to: msgs_to = []
    total = {
        "messages_from": msgs_from,
        "messages_to": msgs_to
    }
    num = len(msgs_from) + len(msgs_to)
    debug(f"Found {num} messages with {person}")
    return total