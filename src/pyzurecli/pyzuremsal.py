from msal import PublicClientApplication

from src.pyzurecli import AzureCLI


class MSAL:
    def __init__(self, azure_cli: AzureCLI):
        self.azure_cli: AzureCLI = azure_cli
        self.public_client: PublicClientApplication = PublicClientApplication(
            self.azure_cli.app_registration.client_id,
            authority="https://login.microsoftonline.com/common",
        )
        # self.acquire_token_interactive = self.public_client.acquire_token_interactive(
        #     scopes=["User.Read"],
        #     port=azure_cli.msal_server_port
        # )