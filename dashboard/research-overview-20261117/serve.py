"""Loopback preview of the static dashboard and linked public evidence only."""
import argparse
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
from urllib.parse import unquote,urlsplit

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        route=unquote(urlsplit(self.path).path)
        if route in ('/','/index.html'):path=HERE/'dist/index.html'
        elif route.startswith(('/docs/','/reports/')):
            path=(REPO/route.lstrip('/')).resolve()
            if not path.is_relative_to(REPO) or path.suffix not in ('.md','.json','.csv'):return self.send_error(404)
        else:return self.send_error(404)
        if not path.is_file():return self.send_error(404)
        raw=path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8' if path.suffix=='.html' else 'text/plain; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=0);args=parser.parse_args()
    server=HTTPServer(('127.0.0.1',args.port),Handler)
    print(f'http://127.0.0.1:{server.server_port}/',flush=True)
    try:server.serve_forever()
    finally:server.server_close()
