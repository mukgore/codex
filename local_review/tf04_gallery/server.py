"""Loopback-only allowlisted private media viewer with byte-range streaming."""
import argparse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

HERE=Path(__file__).resolve().parent


def byte_range(header,size):
    if header is None:return 0,size-1,False
    match=re.fullmatch(r'bytes=(\d*)-(\d*)',header) if len(header)<128 else None
    if not match or size<=0 or not any(match.groups()):raise ValueError('Invalid range')
    first,last=match.groups()
    if not first:
        length=int(last)
        if length<=0:raise ValueError('Invalid suffix')
        return max(0,size-length),size-1,True
    start=int(first);end=min(int(last),size-1) if last else size-1
    if start>=size or end<start:raise ValueError('Outside range')
    return start,end,True


def serve(viewer,port):
    viewer=Path(viewer).resolve(strict=True)
    manifest_path=viewer/'manifest.private.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    source=Path(manifest['source_root']);record=Path(manifest['record_root'])
    clips={c['id']:c for c in manifest['clips']}
    if len(clips)!=48 or manifest['counts']!={'source':32,'candidate':8,'final':8}:raise ValueError('Verified full inventory required')
    routes={'/':(HERE/'gallery.html','text/html'),'/gallery.js':(HERE/'gallery.js','text/javascript'),
            '/gallery.css':(HERE/'gallery.css','text/css'),'/api/manifest':(manifest_path,'application/json'),
            '/records/summary.json':(source/'summary.json','application/json'),
            '/records/receipt.json':(record/'receipt.private.json','application/json'),
            '/records/viewing-conversions.json':(viewer/'conversion_log.private.json','application/json')}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_HEAD(self):self.respond()
        def do_GET(self):self.respond()
        def fail(self,status):
            self.send_response(status);self.send_header('Content-Length','0');self.end_headers()
        def respond(self):
            if self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'):
                return self.fail(403)
            route=urlsplit(self.path).path;download=False
            if route in routes:path,mime=routes[route]
            else:
                parts=route.strip('/').split('/')
                if len(parts)!=2 or parts[0] not in ('media','poster','original') or parts[1] not in clips:return self.fail(404)
                kind,identity=parts;clip=clips[identity]
                if kind=='poster':path=Path(clip['preview_path']);mime='image/png'
                elif kind=='original':path=Path(clip['original_path']);mime='application/octet-stream';download=True
                else:path=Path(clip['playable_path']);mime='video/mp4'
                path=path.resolve()
                if not any(path.is_relative_to(root.resolve()) for root in (viewer,source)):return self.fail(403)
            if not path.is_file():return self.fail(404)
            size=path.stat().st_size
            try:start,end,partial=byte_range(self.headers.get('Range'),size)
            except ValueError:
                self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.send_header('Content-Length','0');self.end_headers();return
            length=max(0,end-start+1)
            self.send_response(206 if partial else 200)
            self.send_header('Content-Type',mime+('; charset=utf-8' if mime.startswith('text/') or mime=='application/json' else ''))
            self.send_header('Content-Length',str(length));self.send_header('Accept-Ranges','bytes')
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self'; img-src 'self'; connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            if partial:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
            if download:self.send_header('Content-Disposition',f'attachment; filename="{identity}{path.suffix}"')
            self.end_headers()
            if self.command=='HEAD':return
            try:
                with path.open('rb') as stream:
                    stream.seek(start)
                    while length:
                        data=stream.read(min(65536,length))
                        if not data:break
                        self.wfile.write(data);length-=len(data)
            except ConnectionError:pass
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.daemon_threads=True
    address=f'http://127.0.0.1:{server.server_port}/'
    (viewer/'server-info.private.json').write_text(json.dumps({'gallery_url':address,'ui_url':manifest['ui_url'],'bind':'127.0.0.1'},indent=2),encoding='utf-8')
    print(address,flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--viewer',required=True);parser.add_argument('--port',type=int,default=0)
    args=parser.parse_args();serve(args.viewer,args.port)
