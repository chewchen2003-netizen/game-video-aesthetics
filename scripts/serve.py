"""Serve the complete delivery website using only the Python standard library."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
import argparse,webbrowser
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8000);p.add_argument('--open',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parents[1]/'docs';url=f'http://127.0.0.1:{a.port}/';print(url,flush=True)
if a.open:webbrowser.open(url)
try:ThreadingHTTPServer(('127.0.0.1',a.port),partial(SimpleHTTPRequestHandler,directory=str(root))).serve_forever()
except KeyboardInterrupt:pass
