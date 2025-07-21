import time
from pathlib import Path

from functools import cached_property
from singleton_decorator import singleton
from toomanythreads import ThreadedServer

from src.pyzurecli import AzureCLI

@singleton
class PyzureServer(ThreadedServer):
    def __init__(self,
        host: str = None,
        port: int = None,
        verbose: bool = None,
        cwd: Path = None
    ):
        self.host = host,
        self.port = port,
        self.verbose = verbose,
        if cwd: self.cwd = cwd
        else: self.cwd = Path.cwd()
        super().__init__(
            host=host,
            port=port,
            verbose=verbose,
        )
        _ = self.azure_cli

    @cached_property
    def azure_cli(self) -> AzureCLI:
        return AzureCLI(self.cwd)

    @cached_property
    def app_registration(self):
        azure_cli = self.azure_cli
        return azure_cli.app_registration

if __name__ == "__main__":
    p = PyzureServer()
    p.thread.start()
    time.sleep(100)