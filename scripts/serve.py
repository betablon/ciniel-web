#!/usr/bin/env python3
"""
Static dev server for docs/, with the one behaviour `python -m http.server`
lacks: extensionless URLs.

The site lives in docs/ because GitHub Pages publishes `main` → `/docs`. It
links to /impressum, /privacy and /terms — no .html — because that is what
GitHub Pages serves for a .html file. The stdlib handler resolves
paths literally and 404s on all three, so local browsing disagrees with
production about which links work. This resolves /foo to foo.html when the bare
path has no file of its own, and nothing else.

    python3 scripts/serve.py [port]
"""

import os
import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        local = super().translate_path(path)
        # Only fill in .html for a path that names nothing — never shadow a real
        # file, and never touch a directory (index.html still resolves normally).
        if not os.path.exists(local) and not path.rstrip("/").endswith(".html"):
            candidate = local.rstrip("/") + ".html"
            if os.path.isfile(candidate):
                return candidate
        return local

    def end_headers(self):
        # Editing CSS and getting a cached copy back wastes more time than the
        # bytes ever save on localhost.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4321
    server = HTTPServer(("127.0.0.1", port), partial(Handler, directory=ROOT))
    print(f"serving {ROOT} at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
