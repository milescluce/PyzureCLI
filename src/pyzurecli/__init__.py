from .factory import AzureCLI

TEST = True
if not TEST: az = AzureCLI

from .user import AzureUser, AzureCLIUser, Subscription, UserSession
from .sp import SPUser, ServicePrincipalCreds, ServicePrincipalContext, AzureCLIServicePrincipal
from .app_registration import AzureCLIAppRegistration, AppRegistrationCreds
from .models import Me, Organization
from .pkg_graph_api import GraphAPI
