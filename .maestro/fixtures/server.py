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

# (url substring, fixture file[, extra response headers]) — first match wins.
# ONTHISDAY_FIXTURE selects the On This Day events fixture (e.g. the
# insufficient-events scenario for the WikiGames pairing-fallback flow).
ROUTES = [
    ("feed/onthisday/events", os.environ.get("ONTHISDAY_FIXTURE", "onthisday_events_insufficient.json")),
    ("include_text=", "semantic_search_results.json"),
    # Semantic search via MediaWiki full-text search (6240fa0d02, non-el languages):
    # MwQueryResponse with snippet/sectiontitle, plus the x-search-id header the app
    # must thread into its hybrid analytics events. Placed before the no-results
    # route so semantic results exist even for the magic empty lexical term.
    ("cirrusSemanticSearch", "semantic_search_results_fulltext.json",
     {"x-search-id": "maestro-search-id-123"}),
    # Magic no-results query: lexical search for this term returns nothing.
    # (Semantic search matches cirrusSemanticSearch above, so it still gets results.)
    ("zzyzxnoresults", "search_results_empty.json"),
    ("feed/configuration", "remote_config.json"),
    ("generator=prefixsearch", "search_results.json"),
    ("list=search", "search_results.json"),
    ("prop=info", "semantic_page_info.json"),
    ("page/summary/", "page_summary.json"),
]

# Non-JSON routes: (url substring, fixture file, content type) — first match wins.
# mock_article.html stands in for a PCS mobile-html article (pronunciation flow);
# test-pron.* are real 1s audio files fetched by the platform media player, whose
# request User-Agent the pronunciation-user-agent runner asserts on (6c43d3fe3c).
# The .ogg.mp3 entry serves iOS-style transcoded-path requests (…/file.ogg/file.ogg.mp3).
MEDIA_ROUTES = [
    ("page/mobile-html/", "mock_article.html", "text/html; charset=utf-8"),
    ("test-pron.ogg.mp3", "test-pron.mp3", "audio/mpeg"),
    ("test-pron.ogg", "test-pron.ogg", "audio/ogg"),
    ("test-pron.mp3", "test-pron.mp3", "audio/mpeg"),
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
    def _log(self, outcome):
        # Includes the request User-Agent: the pronunciation-user-agent runners
        # grep this log to assert media players send the app UA (6c43d3fe3c).
        sys.stderr.write("[fixture] %s %s -> %s UA=%s\n" % (
            self.command, self.path[:120], outcome,
            self.headers.get("User-Agent", "(none)")))

    def _respond(self):
        # Media/HTML fixtures (served with their real content type).
        for fragment, fixture, ctype in MEDIA_ROUTES:
            if fragment in self.path:
                with open(os.path.join(FIXTURE_DIR, fixture), "rb") as f:
                    body = f.read()
                self._log(fixture)
                total = len(body)
                # Media players probe with Range requests and expect 206es.
                range_header = self.headers.get("Range")
                if range_header and range_header.startswith("bytes="):
                    spec = range_header[len("bytes="):].split(",")[0]
                    start_s, _, end_s = spec.partition("-")
                    start = int(start_s) if start_s else 0
                    end = int(end_s) if end_s else total - 1
                    end = min(end, total - 1)
                    chunk = body[start:end + 1]
                    self.send_response(206)
                    self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, total))
                else:
                    chunk = body
                    self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(chunk)))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(chunk)
                return
        # Deterministic pure-red thumbnail (see image-dimming flows): solid red is
        # uniquely measurable in screenshots (no other UI pixel is red-dominant).
        if "test-thumb.png" in self.path:
            self._log("red thumb")
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
            self._log("404")
            body = b"{}"
            self.send_response(404)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = b"{}"
        matched = "(default empty)"
        extra_headers = {}
        for route in ROUTES:
            fragment, fixture = route[0], route[1]
            if fragment in self.path:
                with open(os.path.join(FIXTURE_DIR, fixture), "rb") as f:
                    body = f.read()
                matched = fixture
                if len(route) > 2:
                    extra_headers = route[2]
                break
        self._log(matched)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for name, value in extra_headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    do_GET = _respond
    do_POST = _respond
    do_HEAD = _respond

    def log_message(self, fmt, *args):
        pass  # request logging handled in _respond


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    sys.stderr.write("[fixture] serving on 127.0.0.1:%d (10.0.2.2:%d from emulator)\n" % (PORT, PORT))
    server.serve_forever()
