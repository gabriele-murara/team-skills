from functools import lru_cache
from pathlib import Path

# core/ is in the project root, next to .version
VERSION_FILE = Path(__file__).resolve().parent.parent / ".version"


@lru_cache(maxsize=None)
def get_version():
    """
    Returns the version of the project, read from the .version file in
    the project root. The file is read once per process.
    """
    return VERSION_FILE.read_text().strip()
