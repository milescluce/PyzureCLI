import json
import re
from dataclasses import dataclass
from functools import cached_property
from typing import List, Optional, Any, Dict

import requests
from loguru import logger as log


class AzureUser:
    def __init__(self, _project):
        self.project = _project
        self.azure_cli = self.project.azure_cli
        _ = self.metadata

    @cached_property
    def tenant_id(self):
        return self.metadata.tenantId

    @cached_property
    def subscription_id(self):
        return self.metadata.id

    @dataclass
    class Metadata:
        environmentName: str
        homeTenantId: str
        id: str
        isDefault: bool
        managedByTenants: List[str]
        name: str
        state: str
        tenantDefaultDomain: str
        tenantDisplayName: str
        tenantId: str
        user: dict

    @cached_property
    def metadata(self):
        return self.Metadata(**self.azure_cli.metadata)

    @dataclass
    class _GraphToken:
        accessToken: str
        expiresOn: str
        expires_on: str
        subscription: str
        tenant: str
        tokenType: str

    @cached_property
    def graph_token(self):
        token_metadata = self.azure_cli.run(
            "az account get-access-token --resource https://graph.microsoft.com",
            headless=True,
            expect_json=True)
        return self._GraphToken(**token_metadata)


class GraphAPI:
    def __init__(self, _project, version: str = "v1.0"):
        self.project = _project
        self.token = self.project.azure_user.graph_token
        self.version = version.strip("/")

    def request(self, method, resource, query_parameters, headers, json_body=None):
        url = f"https://graph.microsoft.com/{self.version}/{resource}"
        if query_parameters:
            url += f"?{query_parameters}"

        full_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        if headers:
            full_headers.update(headers)

        log.info(f"[GraphAPI] Sending {method.upper()} request to: {url}")

        try:
            resp = requests.request(
                method=method.upper(),
                url=url,
                headers=full_headers,
                json=json_body
            )
            if not resp.ok:
                log.error(f"[GraphAPI] Error {resp.status_code}: {resp.text}")
                return None

            return resp.json()

        except Exception as e:
            log.exception(f"[GraphAPI] Request failed: {e}")
            return None


class ServicePrincipal:
    def __init__(self, _project):
        self.project = _project
        self.azure_user = self.project.azure_user
        self.client_id = self.metadata.appId
        self.client_secret = self.metadata.password
        self.tenant_id = self.metadata.tenant
        self.name = self.metadata.displayName

    @dataclass
    class _Metadata:
        appId: str
        displayName: str
        password: str
        tenant: str

    @cached_property
    def metadata(self):
        data = self.azure_user.azure_cli.run(
            f"az ad sp create-for-rbac -n mileslib --role Contributor --scope /subscriptions/{self.azure_user.subscription_id}",
            headless=True, expect_json=False)
        if "Found an existing application instance (id)" in data:
            parts = data.split("(id) ")[1]
            extracted_id = parts.split(".")[0].strip()
            data = self.project.azure_user.azure_cli.run(f"az ad sp show --id {extracted_id}", headless=True,
                                                         expect_json=True)
            return self._Metadata(**data)
        json_match = re.search(r"\{.*}", data, re.DOTALL)
        if not json_match: raise ValueError("No JSON object found in output.")
        try:
            parsed_data = json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            raise ValueError("Failed to parse JSON content.") from e
        return self._Metadata(**parsed_data)


class AzureResourceGroup:
    def __init__(self, _project):
        self.project = _project
        self.rg_name = f"{self.project.name}-rg"
        self.region = "westus"

    @dataclass
    class _Metadata:
        id: str
        location: str
        managedBy: str
        name: str
        properties: dict
        tags: dict
        type: str

    @cached_property
    def metadata(self):
        data = self.project.azure_user.azure_cli.run(f"az group create -l {self.region} -n {self.rg_name}",
                                                     headless=True, expect_json=True)
        return self._Metadata(**data)


@dataclass
class Sku:
    family: str
    name: str


@dataclass
class SystemData:
    createdAt: str
    createdBy: str
    createdByType: str
    lastModifiedAt: str
    lastModifiedBy: str
    lastModifiedByType: str


@dataclass
class Properties:
    accessPolicies: List[Dict[str, Any]]
    createMode: Optional[str]
    enablePurgeProtection: Optional[bool]
    enableRbacAuthorization: bool
    enableSoftDelete: bool
    enabledForDeployment: bool
    enabledForDiskEncryption: Optional[bool]
    enabledForTemplateDeployment: Optional[bool]
    hsmPoolResourceId: Optional[str]
    networkAcls: Optional[Dict[str, Any]]
    privateEndpointConnections: Optional[List[Dict[str, Any]]]
    provisioningState: str
    publicNetworkAccess: str
    sku: Sku
    softDeleteRetentionInDays: int
    tenantId: str
    vaultUri: str


class KeyVault:
    def __init__(self, _project):
        self.project = _project
        self.name = f"{self.project.name}-vault"
        self.location = self.project.azure_resource_group.region
        self.rg = self.project.azure_resource_group.rg_name

    @dataclass
    class _Metadata:
        id: str
        location: str
        name: str
        properties: Properties
        resourceGroup: str
        systemData: SystemData
        tags: Dict[str, str]
        type: str

    @cached_property
    def metadata(self):
        self.project.azure_cli_sp.run(
            f"az keyvault create --location {self.location} --name {self.name} --resource-group {self.rg}",
            headless=True, expect_json=False)
        data = self.project.service_principal.azure_cli.run(f"az keyvault show --name {self.name}", headless=True,
                                                            expect_json=True)
        log.debug(data)
        return KeyVault._Metadata(**data)
