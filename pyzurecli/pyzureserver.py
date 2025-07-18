import time
from pathlib import Path
from tabnanny import verbose

from propcache import cached_property
from toomanythreads import ThreadedServer

from pyzurecli import AzureCLI

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