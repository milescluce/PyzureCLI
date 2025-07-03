import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from types import SimpleNamespace
from typing import List

from async_property import AwaitLoader, async_cached_property
from loguru import logger as log

from .util import json_to_dataclass
from .factory import AzureCLI
from dockwershell import AsyncDockerImage
from dockwershell.manager import path_to_wsl, Docker

@dataclass
class AzureUser:
    name: str
    type: str


@dataclass
class Subscription:
    id: str
    name: str
    state: str
    user: AzureUser
    isDefault: bool
    tenantId: str
    environmentName: str
    homeTenantId: str
    tenantDefaultDomain: str
    tenantDisplayName: str
    managedByTenants: list


@dataclass
class UserSession:
    subscriptions: list[Subscription]
    installationId: str


class AzureCLIUser(AwaitLoader):
    instances = {}
    dockerfile: str = """
    FROM mcr.microsoft.com/azure-cli
    WORKDIR /app
    """

    def __init__(self, azure_cli: AzureCLI):
        self.azure_cli = azure_cli
        self.dir: Path = azure_cli.dir
        _ = self.paths
        _ = self.run_args
        log.success(f"{self}: Successfully initialized!")

    def __repr__(self):
        return f"[{self.azure_cli.dir.name.title()}.AzureCLI.User]"

    @classmethod
    async def __async_init__(cls, azure_cli: AzureCLI):
        dir = azure_cli.dir
        if dir.name not in cls.instances:
            cls.instances[dir.name] = cls(azure_cli)
            inst: AzureCLIUser = cls.instances[dir.name]
            log.debug(f"{inst}: Attempting to login!")
            await inst.azure_profile
        return cls.instances[dir.name]

    @cached_property
    def paths(self) -> SimpleNamespace:
        dir: Path = self.dir / "azure" / "user"
        dir.mkdir(exist_ok=True, parents=True)

        dockerfile: Path = dir / "Dockerfile.user"
        dockerfile.touch(exist_ok=True)
        with open(dockerfile, "w", encoding="utf-8") as f: f.write(self.dockerfile)

        azure_config: Path = dir / ".azure"
        azure_config.mkdir(exist_ok=True)
        azure_cmds: Path = azure_config / "commands"
        azure_cmds.mkdir(exist_ok=True)
        azure_profile: Path = azure_config / "azureProfile.json"

        return SimpleNamespace(
            dir=dir,
            dockerfile=dockerfile,
            azure_config=azure_config,
            azure_profile=azure_profile
        )

    @cached_property
    def run_args(self):
        dir_wsl = path_to_wsl(self.paths.dir)
        cfg_wsl = path_to_wsl(self.paths.azure_config)
        cmd = f"-v {dir_wsl}:/app -v {cfg_wsl}:/root/.azure -e AZURE_CONFIG_DIR=/root/.azure -w /app"
        return cmd

    @async_cached_property
    async def image(self):
        inst: AsyncDockerImage = await Docker.new(self.paths.dockerfile, run_args=self.run_args, rebuild=True)
        return inst

    @async_cached_property
    async def azure_profile(self):
        image: AsyncDockerImage = await self.image
        try:
            log.debug(f"{self}: Attempting to load account from {self.paths.azure_profile}...")
            with open(self.paths.azure_profile, "r", encoding="utf-8-sig") as file:
                data = json.load(file)
                log.debug(f"{self}: Found {self.paths.azure_profile}! Data:\n{data}")
                ses = json_to_dataclass(UserSession, data)
                return ses
        except Exception as e:
            log.error(f"{self}: Error while parsing UserSession...\n{e}")
            log.warning(f"{self}: No account session found... Are you logged in?")
            await image.run(cmd="az login --use-device-code", headless=False)
            await image.run(cmd="az account show")

    @classmethod
    async def sp_from_user(cls, azure_cli: AzureCLI):
        from .sp import AzureCLIServicePrincipal
        if not getattr(azure_cli, "user", None):
            await cls.__async_init__(azure_cli)
        sp = await AzureCLIServicePrincipal.__async_init__(azure_cli)
        setattr(azure_cli, "service_principal", sp)
        if sp is None: raise RuntimeError(f"{azure_cli}: Failed to attach Service Principal!")
        if not isinstance(sp, AzureCLIServicePrincipal): raise RuntimeError
        return sp


# class GraphAPI:
#     @cached_property
#     def graph_token(self):
#         token_metadata = self.azure_cli.run(
#             "az account get-access-token --resource https://graph.microsoft.com",
#             headless=True,
#             expect_json=True)
#         return self._GraphToken(**token_metadata)

@dataclass(slots=True)
class ServicePrincipalCreds:
    appId: str
    displayName: str
    password: str
    tenant: str


@dataclass
class SPUser:
    name: str  # this is the clientId of the service principal
    type: str  # always "servicePrincipal"


@dataclass
class ServicePrincipalContext:
    cloudName: str
    homeTenantId: str
    id: str  # subscriptionId
    isDefault: bool
    managedByTenants: List  # usually empty unless you're delegating mgmt
    name: str  # sub name e.g. "Azure subscription 1"
    # state: str                   # "Enabled" or "Disabled"
    tenantId: str
    # actual tenant used
    user: SPUser
