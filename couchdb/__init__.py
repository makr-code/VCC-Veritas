import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lightweight shim for optional `couchdb` package when not installed.
# Keep this module silent at INFO level to avoid noisy startup logs; it
# only emits DEBUG traces when developers need to inspect shim usage.
logger.debug("couchdb shim loaded (silent). Real package not installed.")


class _DummyDB:
    def __init__(self, name: str) -> None:
        self._name = name

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<couchdb-shim-db:{self._name}>"

    def _fail(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError(
            "couchdb shim: real 'couchdb' package is not installed. "
            "Install it to enable file/document backends."
        )

    create = _fail
    save = _fail
    delete = _fail
    __getitem__ = _fail
    __setitem__ = _fail
    __delitem__ = _fail


class Server:
    """Tolerant shim of `couchdb.Server`.

    Construction does not raise; operations on the returned object will raise
    a clear RuntimeError indicating the real package is missing.
    """

    def __init__(self, url: str = "", *args: Any, **kwargs: Any) -> None:
        self.url = url
        logger.debug(
            "couchdb shim: created dummy Server for url=%s — operations will fail",
            url,
        )

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<couchdb-shim-server url={self.url}>"

    def create(self, name: str) -> _DummyDB:
        # Return a dummy DB object instead of raising; callers can decide
        # how to react. This avoids tracebacks during startup.
        logger.debug("couchdb shim: create(%s) called — returning dummy DB", name)
        return _DummyDB(name)

    def __getitem__(self, name: str) -> _DummyDB:
        # Return a dummy DB object rather than raising; presence checks
        # should be handled via `__contains__` to avoid exceptions during
        # membership tests (e.g. `if db_name not in server`).
        return _DummyDB(name)

    def _raise(self) -> None:
        raise RuntimeError(
            "couchdb shim: real 'couchdb' package is not installed. "
            "Install it to enable file/document backends."
        )

    def __contains__(self, name: str) -> bool:
        # Always report that the DB is not present so callers can decide
        # to create or skip the file backend without raising exceptions.
        return False


def validate_shim_usage() -> None:
    logger.debug("couchdb shim loaded — operations will raise if attempted")
