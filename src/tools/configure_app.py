from starlette.middleware.cors import CORSMiddleware
from timing_asgi import TimingClient, TimingMiddleware
from timing_asgi.integrations import StarletteScopeToName

from src.tools.log import log, Colors


class PrintTimings(TimingClient):
    def timing(self, metric_name, timing, tags):
        if 'time:wall' in tags:
            time = "{:.5f}".format(timing)
            log.m("DURATION: " + time, color=Colors.yellow)


def configure_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


def configure_timing(app):
    app.add_middleware(
        TimingMiddleware,
        client=PrintTimings(),
        metric_namer=StarletteScopeToName(prefix="meloncloud", starlette_app=app)
    )
