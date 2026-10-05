"""Per-run cache of deployed, hashed public JS/CSS; never cache HTML or APIs.

Playwright routing disables the browser HTTP cache. Fresh mock contexts would
otherwise download identical lazy chunks repeatedly. Only bytes fetched from
the configured frontend in this run are replayed; no generated UI is served.
"""
import re
from urllib.parse import urlsplit
from config import BASE_URL, DEFAULT_TIMEOUT


class FrontendAssets:
    def __init__(self):
        self.host = urlsplit(BASE_URL).netloc
        self.responses = {}

    def install(self, context):
        context.route("**/assets/**", self.handle)

    def handle(self, route):
        request = route.request
        url = urlsplit(request.url)
        hashed = re.search(r"/assets/[^/]+-[A-Za-z0-9_-]+\.(?:js|css)$", url.path)
        if request.method != "GET" or url.netloc != self.host or not hashed:
            route.continue_()
            return
        cached = self.responses.get(request.url)
        if cached is None:
            response = route.fetch(timeout=DEFAULT_TIMEOUT)
            content_type = response.headers.get("content-type", "")
            if response.status != 200 or not any(t in content_type for t in ("javascript", "text/css")):
                # Preserve deployment errors; never replace them with a fixture.
                route.fulfill(response=response)
                return
            headers = {key: value for key, value in response.headers.items()
                       if key.lower() not in ("set-cookie", "content-length", "content-encoding", "transfer-encoding")}
            cached = (headers, response.body())
            self.responses[request.url] = cached
        headers, body = cached
        route.fulfill(status=200, headers=headers, body=body)
