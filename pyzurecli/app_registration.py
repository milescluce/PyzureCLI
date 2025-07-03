from dataclasses import dataclass
from typing import Optional

from async_property import AwaitLoader, async_cached_property
from loguru import logger as log

from pyzurecli import az


@dataclass
class AppRegistrationCreds:
    """Azure App Registration credentials"""
    appId: str
    displayName: str
    tenantId: str
    objectId: Optional[str] = None


class AzureCLIAppRegistration(AwaitLoader):
    """Manages Azure App Registrations for multi-tenant OAuth"""

    instances = {}

    def __init__(self, azure_cli: az):
        self.azure_cli = azure_cli
        self.dir = azure_cli.dir
        log.success(f"{self}: Successfully initialized!")

    def __repr__(self):
        return f"[{self.dir.name.title()}.AppRegistration]"

    @classmethod
    async def __async_init__(cls, azure_cli: az):
        dir_name = azure_cli.dir.name
        if dir_name not in cls.instances:
            cls.instances[dir_name] = cls(azure_cli)

        instance = cls.instances[dir_name]
        await instance.creds  # Initialize credentials
        return instance

    @async_cached_property
    async def creds(self) -> AppRegistrationCreds:
        """Get or create multi-tenant OAuth app registration"""
        user_image = await self.azure_cli.user.image
        app_name = f"{self.dir.name.title()}-MultiTenant"

        # Check for existing app
        existing_app = await self._find_existing_app(user_image, app_name)
        if existing_app:
            await self._ensure_multi_tenant_config(user_image, existing_app.appId)
            return existing_app

        # Create new multi-tenant app
        return await self._create_multi_tenant_app(user_image, app_name)

    async def _find_existing_app(self, user_image, app_name: str) -> Optional[AppRegistrationCreds]:
        """Find existing app registration"""
        try:
            result = await user_image.run(
                f'az ad app list --display-name "{app_name}" --only-show-errors',
                headless=True
            )

            if result.json and len(result.json) > 0:
                app_data = result.json[0]
                log.info(f"{self}: Found existing app registration")

                return AppRegistrationCreds(
                    appId=app_data["appId"],
                    displayName=app_data["displayName"],
                    tenantId=await self._get_tenant_id(),
                    objectId=app_data.get("id")
                )
        except Exception as e:
            log.warning(f"{self}: Could not check for existing app: {e}")

        return None

    async def _create_multi_tenant_app(self, user_image, app_name: str) -> AppRegistrationCreds:
        """Create new multi-tenant app registration"""
        log.info(f"{self}: Creating multi-tenant OAuth app: {app_name}")

        redirect_uri = "http://localhost:8080/callback"

        create_cmd = [
            "az", "ad", "app", "create",
            "--display-name", app_name,
            "--sign-in-audience", "AzureADMultipleOrgs",  # Multi-tenant
            "--web-redirect-uris", redirect_uri,
            "--public-client-redirect-uris", redirect_uri,
            "--is-fallback-public-client", "true",  # PKCE support
            "--enable-id-token-issuance", "true",
            "--enable-access-token-issuance", "false",
            "--only-show-errors"
        ]

        result = await user_image.run(" ".join(f'"{arg}"' if " " in arg else arg for arg in create_cmd), headless=True)

        if not result.json:
            log.error(f"{self}: Failed to create app registration")
            raise RuntimeError("OAuth app registration creation failed")

        app_data = result.json
        log.success(f"{self}: Created multi-tenant app: {app_data['appId']}")

        return AppRegistrationCreds(
            appId=app_data["appId"],
            displayName=app_data["displayName"],
            tenantId=await self._get_tenant_id(),
            objectId=app_data.get("id")
        )

    async def _ensure_multi_tenant_config(self, user_image, app_id: str):
        """Ensure existing app is configured for multi-tenant"""
        try:
            update_cmd = [
                "az", "ad", "app", "update",
                "--id", app_id,
                "--sign-in-audience", "AzureADMultipleOrgs",
                "--is-fallback-public-client", "true",
                "--only-show-errors"
            ]

            await user_image.run(" ".join(update_cmd), headless=True)
            log.success(f"{self}: Updated app {app_id} for multi-tenant")

        except Exception as e:
            log.warning(f"{self}: Could not update app config: {e}")

    async def _get_tenant_id(self) -> str:
        """Get current tenant ID"""
        metadata = await self.azure_cli.metadata
        return metadata.tenant_id

    @async_cached_property
    async def client_id(self) -> str:
        """Get OAuth client ID"""
        creds = await self.creds
        return creds.appId

    async def generate_admin_consent_url(self, scopes: str = "User.Read Mail.Read Files.Read") -> str:
        """Generate admin consent URL for cross-tenant permissions"""
        client_id = await self.client_id

        consent_url = (
            f"https://login.microsoftonline.com/common/adminconsent?"
            f"client_id={client_id}&"
            f"redirect_uri=http://localhost:8080/callback&"
            f"scope={scopes}"
        )

        log.info(f"{self}: Admin consent URL generated for app {client_id}")
        return consent_url

    async def delete_app_registration(self):
        """Delete the OAuth app registration"""
        creds = await self.creds
        user_image = await self.azure_cli.user.image

        await user_image.run(f"az ad app delete --id {creds.appId} --only-show-errors", headless=True)
        log.info(f"{self}: Deleted app registration: {creds.appId}")