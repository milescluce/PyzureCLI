import time
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Type

from loguru import logger as log
from singleton_decorator import singleton
from starlette.responses import Response
from toomanyports import PortManager
from toomanysessions import SessionedServer, Session, User, Sessions, Users

from .factory import AzureCLI
from .graph import GraphAPI, Me

DEBUG = True


@dataclass
class PyzureServerSession(Session):
    graph_token: str = None
    graph_api: GraphAPI = None


@singleton
class PyzureServer(SessionedServer):
    def __init__(
            self,
            host: str = "localhost",
            port: int = PortManager.random_port(),
            cwd: Path = Path.cwd(),
            session_name: str = "session",
            session_age: int = (3600 * 8),
            # session_model: Type[Session] = Session,
            # authentication_model: Type[Callable] = authenticate,
            user_model: Type[User] = User,
            restrict_to_domain: str = None,
            verbose: bool = DEBUG,
    ):
        self.host = host
        self.port = port
        self.cwd = cwd
        self.session_name = session_name
        self.session_age = session_age
        self.session_model = PyzureServerSession
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
        self.restrict_to_domain = restrict_to_domain
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

    async def authentication_model(self, session: PyzureServerSession, session_name, redirect_uri):
        time.sleep(session.throttle)
        result = self.azure_cli.msal.public_client.acquire_token_interactive(
            scopes=["User.Read"],
            port=self.azure_cli.msal_server_port
        )
        if not result:
            session.authenticated = False
            return Response("Authentication Error", 401)
        session.graph_token = result["access_token"]
        log.debug(f"{self}: Got MSAL information from session {session.token}:\n  - result={result}")

        session.graph_api = GraphAPI(session.graph_token)
        me: Me = await session.graph_api.me

        if not self.restrict_to_domain:
            if me.mail:
                if self.restrict_to_domain in me.mail:
                    session.authenticated = True
                    session.throttle = 0
                    return session
            else:
                if self.restrict_to_domain in me.userPrincipalName:
                    session.authenticated = True
                    session.throttle = 0
                    return session
        else:
            session.authenticated = True
            session.throttle = 0
            return session

        session.authenticated = False
        session.throttle = (session.throttle + 1) * 5
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
