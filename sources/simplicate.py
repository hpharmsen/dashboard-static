from pathlib import Path
from configparser import ConfigParser
from pysimplicate import Simplicate

_simplicate = None # Singleton
def simplicate():
    global _simplicate
    if not _simplicate:
        ini = ConfigParser()
        ini.read(Path(__file__).resolve().parent / 'credentials.ini')

        subdomain = ini['simplicate']['subdomain']
        api_key = ini['simplicate']['api_key']
        api_secret = ini['simplicate']['api_secret']

        _simplicate = Simplicate(subdomain, api_key, api_secret)
    return _simplicate

