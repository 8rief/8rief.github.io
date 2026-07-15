#!/usr/bin/env python3
import argparse
import datetime as dt
import http.server
import urllib.parse
from pathlib import Path


class Handler(http.server.BaseHTTPRequestHandler):
    web_root: Path
    log_path: Path

    def send_text(self, status: int, text: str) -> None:
        body = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        name = params.get('name', ['index.txt'])[0]
        mode = parsed.path.strip('/') or 'safe'
        with self.log_path.open('a', encoding='utf-8') as f:
            f.write(f"{dt.datetime.now(dt.timezone.utc).isoformat()} mode={mode!r} name={name!r} peer={self.client_address[0]}:{self.client_address[1]}\n")
        if mode == 'unsafe':
            target = self.web_root / name
            try:
                self.send_text(200, f"UNSAFE read {target}\n" + target.read_text(encoding='utf-8'))
            except OSError as exc:
                self.send_text(404, f"UNSAFE error: {exc}\n")
            return
        if mode == 'safe':
            root = self.web_root.resolve()
            target = (root / name).resolve()
            if not target.is_relative_to(root) or not target.is_file():
                self.send_text(403, f"SAFE blocked name={name!r}\n")
                return
            self.send_text(200, f"SAFE read {target.name}\n" + target.read_text(encoding='utf-8'))
            return
        self.send_text(404, 'unknown endpoint\n')

    def log_message(self, fmt: str, *args) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=18185)
    parser.add_argument('--web-root', default='www')
    parser.add_argument('--log', default='reports/path.log')
    args = parser.parse_args()
    Handler.web_root = Path(args.web_root)
    Handler.log_path = Path(args.log)
    Handler.log_path.parent.mkdir(parents=True, exist_ok=True)
    Handler.log_path.write_text('', encoding='utf-8')
    http.server.ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
