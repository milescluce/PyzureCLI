import time
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from types import SimpleNamespace

from loguru import logger as log
from singleton_decorator import singleton


@dataclass
class GraphToken:
    accessToken: str
    expiresOn: str
    expires_on: str
    subscription: str
    tenant: str
    tokenType: str


@singleton
class AzureCLI:
    instance = None

    def __init__(self, dir: Path):
        self.dir = dir
        _ = self.user
        _ = self.service_principal
        _ = self.app_registration
        log.success(f"{self}: Successfully initialized!")

    def __repr__(self):
        return f"[{self.dir.name.title()}.AzureCLI]"

    @cached_property
    def user(self):
        from pyzurecli.user import AzureCLIUser
        return AzureCLIUser.__async_init__(self)

    @cached_property
    def service_principal(self):
        return self.user.sp_from_user(self)

    @cached_property
    def app_registration(self):
        from pyzurecli.app_registration import AzureCLIAppRegistration
        return AzureCLIAppRegistration.__async_init__(self)

    @cached_property
    def metadata(self) -> SimpleNamespace:
        from pyzurecli.user import UserSession  # abandoned rel imports lol
        ses: UserSession = self.user.azure_profile
        if ses is None:
            try:
                ses: UserSession = self.user.azure_profile
                log.debug(ses)
            except ses is None:
                raise RuntimeError(f"{self}: UserSession returned '{ses}', "
                                   f"which is unreadable! "
                                   f"Either your login failed or there was "
                                   f"an race condition... Try restarting."
                                   )
        subscription = ses.subscriptions[0]
        subscription_id = subscription.id
        tenant_id = subscription.tenantId
        return SimpleNamespace(
            user=ses,
            subscription_id=subscription_id,
            tenant_id=tenant_id
        )


def debug():
    AzureCLI(Path.cwd())


if __name__ == "__main__":
    debug()
    time.sleep(500)
