#!/usr/bin/env python3
"""Minimal fixture server for Maestro flows.

Serves canned MediaWiki API responses to the app when the app's API base URL
is pointed at this server (http://10.0.2.2:<port> from the emulator's view).

Routing is by URL substring: add an entry to ROUTES mapping a query-string
fragment to a fixture file in this directory. Unmatched API requests get an
empty JSON object, which MediaWiki response models parse as "no results".
"""
import http.server
import os
import struct
import sys
import zlib

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))

# (url substring, fixture file) — first match wins.
# ONTHISDAY_FIXTURE selects the On This Day events fixture (e.g. the
# insufficient-events scenario for the WikiGames pairing-fallback flow).
ROUTES = [
    ("feed/onthisday/events", os.environ.get("ONTHISDAY_FIXTURE", "onthisday_events_insufficient.json")),
    ("include_text=", "semantic_search_results.json"),
    # Magic no-results query: lexical search for this term returns nothing.
    # (Semantic search matches include_text= above, so it still gets results.)
    ("zzyzxnoresults", "search_results_empty.json"),
    ("feed/configuration", "remote_config.json"),
    ("generator=prefixsearch", "search_results.json"),
    ("list=search", "search_results.json"),
    ("prop=info", "semantic_page_info.json"),
]


def _solid_png(width, height, rgb):
    """Minimal opaque solid-color PNG, no external deps. Used as a deterministic
    thumbnail so flows can measure image processing (e.g. dark-mode dimming)."""
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw)) +
            chunk(b"IEND", b""))


RED_THUMB = _solid_png(320, 320, (255, 0, 0))


class Handler(http.server.BaseHTTPRequestHandler):
    def _respond(self):
        # Deterministic pure-red thumbnail (see image-dimming flows): solid red is
        # uniquely measurable in screenshots (no other UI pixel is red-dominant).
        if "test-thumb.png" in self.path:
            sys.stderr.write("[fixture] %s %s -> red thumb\n" % (self.command, self.path[:120]))
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(RED_THUMB)))
            self.end_headers()
            self.wfile.write(RED_THUMB)
            return
        # Deterministic HTTP failure (client-error-logging flows): any request
        # mentioning this magic term gets a 404, which the app's HTTP layer must
        # report to the mediawiki.client.error logging-intake stream.
        if "errortrigger" in self.path:
            sys.stderr.write("[fixture] %s %s -> 404\n" % (self.command, self.path[:120]))
            body = b"{}"
            self.send_response(404)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = b"{}"
        matched = "(default empty)"
        for fragment, fixture in ROUTES:
            if fragment in self.path:
                with open(os.path.join(FIXTURE_DIR, fixture), "rb") as f:
                    body = f.read()
                matched = fixture
                break
        sys.stderr.write("[fixture] %s %s -> %s\n" % (self.command, self.path[:120], matched))
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = _respond
    do_POST = _respond

    def log_message(self, fmt, *args):
        pass  # request logging handled in _respond


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    sys.stderr.write("[fixture] serving on 127.0.0.1:%d (10.0.2.2:%d from emulator)\n" % (PORT, PORT))
    server.serve_forever()
