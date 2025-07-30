import time

from src.pyzurecli import PyzureServer

if __name__ == "__main__":
    p = PyzureServer(tenant_whitelist=["e58f9482-1a00-4559-b3b7-42cd6038c43e"]
    )
    p.thread.start()
    time.sleep(100)
