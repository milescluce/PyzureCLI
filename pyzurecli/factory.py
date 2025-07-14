import asyncio
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from async_property import AwaitLoader, async_cached_property
from loguru import logger as log
import time

@dataclass
class GraphToken:
    accessToken: str
    expiresOn: str
    expires_on: str
    subscription: str
    tenant: str
    tokenType: str


class AzureCLI(AwaitLoader):
    instance = None

    def __init__(self, dir: Path):
        self.dir = dir
        if not self.instance: self.instance = self
        log.success(f"{self}: Successfully initialized!")

    def __repr__(self):
        return f"[{self.dir.name.title()}.AzureCLI]"

    @classmethod
    async def __async_init__(cls, dir: Path):
        if not cls.instance:
            cls.instance = cls(dir)
            _ = await cls.instance.user
            _ = await cls.instance.service_principal
            _ = await cls.instance.app_registration
        return cls.instance

    @async_cached_property
    async def user(self):
        from pyzurecli import AzureCLIUser
        return await AzureCLIUser.__async_init__(self)

    @async_cached_property
    async def service_principal(self):
        return await self.user.sp_from_user(self)

    @async_cached_property
    async def app_registration(self):
        from pyzurecli import AzureCLIAppRegistration
        return await AzureCLIAppRegistration.__async_init__(self)

    @async_cached_property
    async def metadata(self) -> SimpleNamespace:
        from pyzurecli import UserSession #abandoned rel imports lol
        ses: UserSession = await self.user.azure_profile
        if ses is None:
            try:
                ses: UserSession = await self.user.azure_profile
                log.debug(ses)
            except ses is None: raise RuntimeError(f"{self}: UserSession returned '{ses}', "
                                           f"which is unreadable! "
                                           f"Either your login failed or there was "
                                           f"an async race condition... Try restarting."
                                           )
        subscription = ses.subscriptions[0]
        subscription_id = subscription.id
        tenant_id = subscription.tenantId
        return SimpleNamespace(
            user=ses,
            subscription_id=subscription_id,
            tenant_id=tenant_id
        )


az = AzureCLI

async def debug():
    await az.__async_init__(Path.cwd())

if __name__ == "__main__":
    asyncio.run(debug())
    time.sleep(500)
