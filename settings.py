from configparser import ConfigParser
from pathlib import Path


def get_output_folder():
    ini = ConfigParser()
    ini.read(Path(__file__).resolve().parent / 'sources' / 'credentials.ini')
    return Path(ini['output']['folder'])


ini = ConfigParser()
ini.read(Path(__file__).resolve().parent / 'sources' / 'credentials.ini')
