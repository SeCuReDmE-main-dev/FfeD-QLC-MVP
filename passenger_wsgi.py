"""cPanel Passenger entrypoint for the FastAPI application.

Passenger exposes WSGI. a2wsgi provides the explicit ASGI-to-WSGI boundary;
the application itself remains FastAPI/ASGI for local and container runtimes.
"""

from a2wsgi import ASGIMiddleware

from ffed_qlc.api import app


application = ASGIMiddleware(app, wait_time=5.0)
