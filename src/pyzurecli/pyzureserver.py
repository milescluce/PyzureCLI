import base64
import hashlib
import secrets
import time
from functools import cached_property
from pathlib import Path
from typing import Type, Callable

from fastapi import APIRouter
from msal import PublicClientApplication
from singleton_decorator import singleton
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from toomanyports import PortManager
from toomanysessions import SessionedServer, Session, authenticate, User, Sessions, Users
from loguru import logger as log
from src.pyzurecli.factory import AzureCLI

DEBUG = True

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
            authentication_model: Type[Callable] = authenticate,
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
        # self.callback_method = self.hello
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

    async def authentication_model(self, session: Session, session_name, redirect_uri):
        time.sleep(session.throttle)
        result = self.azure_cli.msal.public_client.acquire_token_interactive(
            scopes=["User.Read"],
            port=self.azure_cli.msal_server_port
        )
        log.debug(f"{self}: Got MSAL information from session {session.token}:\n  - result={result}")
        if not result:
            session.authenticated = False
            session.throttle = session.throttle + 5
        session.authenticated = True
        return session

    @cached_property
    def azure_cli(self) -> AzureCLI:
        inst = AzureCLI(
            cwd=self.cwd,
            pyzure_server_port=self.port
        )
        return inst

    @cached_property
    def app_registration(self):
        azure_cli = self.azure_cli
        return azure_cli.app_registration

if __name__ == "__main__":
    p = PyzureServer()
    p.thread.start()
    time.sleep(100)
