from functools import cached_property
from typing import Literal
from toomanyconfigs.simple_api import SimpleAPI

from . import _DEBUG
from ..models import Me, Organization


class _GraphAPIInit(SimpleAPI):
    def __init__(self, token: str, version: str = "v1.0", email_filters: list | None = None, people_filters: list | None = None, _debug: bool = _DEBUG):
        self._debug = _debug
        self._token: str = token
        self._version = version.strip("/")
        self._email_filters: list = email_filters
        self._people_filters: list = people_filters
        SimpleAPI.__init__(
            self,
            base_url=f"https://graph.microsoft.com/{self._version}",
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json"
            }
        )
        if _debug: self.to_pickle("test_graph_api")

    def __repr__(self):
        return f"[GraphAPI.{self._token[:8]}]"

    def safe_request(self, method: Literal["GET", "POST"], path: str, is_async: bool = True, **kwargs):
        from .pkg_safe_request import safe_request, sync_safe_request
        if is_async:
            return safe_request(self, method, path, **kwargs)
        else:
            return sync_safe_request(self, method, path, **kwargs)


class _GraphAPIProperties(_GraphAPIInit):
    def __init__(self, token: str, version: str = "v1.0", email_filters: list | None = None, people_filters: list | None = None, _debug: bool = _DEBUG):
        super().__init__(token, version, email_filters, people_filters, _debug)

    @cached_property
    def email_filters(self):
        from .pkg_filters import email_filters
        return email_filters(self._email_filters)

    @cached_property
    def people_filters(self) -> list["str"]:
        from .pkg_filters import _process_default_people_filter
        return _process_default_people_filter(self._people_filters)

    @property
    def me(self):
        response = self.safe_request(method="GET", path="me", is_async=False)
        return Me(**response.body)

    @property
    def organization(self):
        response = self.safe_request(method="GET", path="organization", is_async=False)
        val = response.body.get("value")[0]
        return Organization(**val)

    @property
    def people(self):
        from .pkg_filters import get_filtered_people
        return get_filtered_people(self)


class _GraphAPIMethods(_GraphAPIProperties):
    def __init__(self, token: str, version: str = "v1.0", email_filters: list | None = None, people_filters: list | None = None, _debug: bool = _DEBUG):
        super().__init__(token, version, email_filters, people_filters, _debug)

    def list_received_messages_from_person(self, person: str):
        from .pkg_messages import list_received_messages_from_person
        return list_received_messages_from_person(self, person)

    def list_sent_messages_to_person(self, person: str):
        from .pkg_messages import list_sent_messages_to_person
        return list_sent_messages_to_person(self, person)

    def list_messages_with_person(self, person: str) -> dict:
        from .pkg_messages import list_messages_with_person
        return list_messages_with_person(self, person)

    def list_filtered_people(self, filter_append: list | None = None, filter_override: list | None = None):
        from .pkg_filters import get_filtered_people
        get_filtered_people(self, filter_override, filter_append)

class GraphAPI(_GraphAPIMethods):
    def __init__(self, token: str, version: str = "v1.0", email_filters: list | None = None, people_filters: list | None = None, _debug: bool = _DEBUG):
        super().__init__(token, version, email_filters, people_filters, _debug)