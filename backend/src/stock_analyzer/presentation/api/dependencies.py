"""FastAPI dependencies that hand out wired objects from the container."""

from typing import cast

from fastapi import Request

from stock_analyzer.bootstrap import Container


def get_container(request: Request) -> Container:
    """Return the container stored on the app at startup."""
    return cast(Container, request.app.state.container)
