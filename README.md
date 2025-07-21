# PyzureCLI

Asynchronous Azure CLI automation via Docker-based isolation.

PyzureCLI runs every `az` command inside a disposable Docker container, providing:

* **Interactive login** (device-code flow) with persistent session cache at `./azure/user`
* **Service principal** creation and managed login, cached under `./azure/sp`
* **App registration** for multi-tenant OAuth flows, configured in `./azure/app_registration`

```python
import asyncio
from pathlib import Path
from src.pyzurecli import az


async def main():
    # Initialize AzureCLI client (entry via factory.py)
    cli = await az.__async_init__(Path.cwd())

    # Inspect current subscription metadata
    meta = await cli.metadata
    print("Subscription ID:", meta.subscription_id)

    # Create or retrieve a Service Principal
    sp = await cli.service_principal
    print("SP App ID:", sp.creds.appId)

    # Create or retrieve an App Registration
    ar = await cli.app_registration
    client_id = await ar.client_id
    print("App Registration Client ID:", client_id)

    # Generate an admin-consent URL
    url = await ar.generate_admin_consent_url()
    print("Consent URL:", url)


asyncio.run(main())
```

## License

MIT © genderlesspit
