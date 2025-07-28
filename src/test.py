import time

from src.pyzurecli import PyzureServer

if __name__ == "__main__":
    p = PyzureServer()
    p.thread.start()
    time.sleep(100)
