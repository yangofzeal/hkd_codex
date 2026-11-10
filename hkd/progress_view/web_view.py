#!/usr/bin/env python3
"""Read-only loopback progress viewer; never exposes a terminal or directory listing."""
import argparse
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def handler_for(root):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            allowed = {'/': ('index.html', 'text/html; charset=utf-8'),
                       '/index.html': ('index.html', 'text/html; charset=utf-8'),
                       '/status.json': ('status.json', 'application/json')}
            route = allowed.get(self.path.split('?', 1)[0])
            if route is None:
                self.send_error(404)
                return
            try:
                data = (root / route[0]).read_bytes()
            except OSError:
                self.send_error(503, 'Progress snapshot not available')
                return
            self.send_response(200)
            self.send_header('Content-Type', route[1])
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format, *args):
            pass
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(os.environ.get('HKD_PROGRESS_ROOT', Path(__file__).resolve().parent)))
    parser.add_argument('--port', type=int, default=8769)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(root))
    except OSError as error:
        parser.exit(1, 'Cannot start progress viewer: ' + str(error) + '\n')
    print(f'Progress view: http://127.0.0.1:{server.server_port}/', flush=True)
    print('Read-only saved progress. Ctrl-C stops this server.', flush=True)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
