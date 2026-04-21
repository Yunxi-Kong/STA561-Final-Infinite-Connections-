from __future__ import annotations

import argparse
import os
from contextlib import closing
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socket import socket


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    os.chdir(ROOT)
    port = find_open_port(args.host, args.port)
    server = ThreadingHTTPServer((args.host, port), SimpleHTTPRequestHandler)
    print(f"Serving Infinite Connections at http://{args.host}:{port}/web/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


def find_open_port(host: str, start_port: int) -> int:
    port = start_port
    while port < start_port + 100:
        with closing(socket()) as probe:
            if probe.connect_ex((host, port)) != 0:
                return port
        port += 1
    raise RuntimeError(f"No open port found from {start_port} to {start_port + 99}.")


if __name__ == "__main__":
    main()
