import secrets
import time
from functools import cached_property
from pathlib import Path
from typing import Type, Callable

import requests
from fastapi import APIRouter
from singleton_decorator import singleton
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from loguru import logger as log
from toomanyports import PortManager
from toomanysessions import SessionedServer, Session, authenticate, User, Sessions, Users
from src.pyzurecli import AzureCLI

DEBUG = True

class PyzureOAuth(APIRouter):
    def __init__(self, server: 'PyzureServer'):
        self.server = server
        super().__init__(prefix="/oauth")

        @self.get("/")
        async def request(request: Request):
            """Handle OAuth request"""
            return RedirectResponse(
                url = self.server.app_registration.admin_consent_url
            )

        @self.get("/callback")
        async def callback(request: Request):
            """Handle OAuth callback"""


@singleton
class PyzureServer(SessionedServer):
    def __init__(
        self,
        host: str = "localhost",
        port: int = PortManager.random_port(),
        cwd: Path = Path.cwd(),
        session_name: str = "session",
        session_age: int = (3600 * 8),
        session_model: Type[Session] = Session,
        # authentication_model: Type[Callable] = authenticate,
        user_model: Type[User] = User,
        verbose: bool = DEBUG,
    ):
        self.host = host
        self.port = port
        self.verbose = verbose
        self.cwd = cwd
        self.session_name = session_name
        self.session_age = session_age
        self.session_model = session_model
        self.authentication_model = self.admin_consent
        self.sessions = Sessions(
            self.session_model,
            self.authentication_model,
            verbose,
        )
        self.user_model = user_model
        self.users = Users(
            self.user_model,
            self.user_model.create,
        )
        self.callback_method = self.hello
        self.token_endpoint = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        self.verbose = verbose
        super().__init__(
            host=self.host,
            port=self.port,
            session_name=self.session_name,
            session_age=self.session_age,
            session_model=self.session_model,
            authentication_model=self.authentication_model,
            user_model=self.user_model,
            verbose=self.verbose,
        )
        _ = self.azure_cli

    def admin_consent(self, session: Session, aiohttp=None):
        data = {
            'client_id': self.app_registration.client_id,
            'scope': self.app_registration.scopes,
            'code': session.token,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code',
            # 'code_verifier': pkce_verifier
        }

        resp = requests.post(self.token_endpoint, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        log.warning(resp.__dict__)
        
        
        # session.authenticated = True
        # return RedirectResponse(
        #     url = self.app_registration.admin_consent_url
        # )

    def hello(self, request):
        log.debug(request)

    @cached_property
    def oauth(self):
        inst = PyzureOAuth(self)
        self.include_router(inst)
        return inst

    @cached_property
    def azure_cli(self) -> AzureCLI:
        inst = AzureCLI(self.cwd)
        inst.redirect_uri = self.redirect_uri
        return inst

    @cached_property
    def app_registration(self):
        azure_cli = self.azure_cli
        return azure_cli.app_registration


if __name__ == "__main__":
    p = PyzureServer()
    p.thread.start()
    time.sleep(100)
