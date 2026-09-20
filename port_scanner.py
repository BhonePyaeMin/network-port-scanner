#!/usr/bin/env python3
"""Simple single-threaded TCP port scanner with banner grabbing.

Only scan hosts you own or have explicit permission to scan.
"""

import socket
import sys
import time

DEFAULT_TARGET = "127.0.0.1"
DEFAULT_START = 1
DEFAULT_END = 1024
CONNECT_TIMEOUT = 0.5
BANNER_TIMEOUT = 1.0
HTTP_PROBE = b"HEAD / HTTP/1.0\r\n\r\n"


def prompt(label, default):
    value = input(f"{label} [{default}]: ").strip()
    return value or str(default)


def prompt_port(label, default):
    while True:
        raw = prompt(label, default)
        try:
            port = int(raw)
        except ValueError:
            print("  Please enter a number.")
            continue
        if 1 <= port <= 65535:
            return port
        print("  Port must be between 1 and 65535.")


def clean_banner(data):
    """First line of the response, ASCII-printable only, capped at 100 chars."""
    text = data.decode("utf-8", errors="replace").strip()
    if not text:
        return ""
    first_line = text.splitlines()[0]
    return "".join(ch for ch in first_line if 32 <= ord(ch) < 127)[:100]


def grab_banner(sock):
    """Read what the service says on connect; if it stays silent, poke it once."""
    sock.settimeout(BANNER_TIMEOUT)
    try:
        data = sock.recv(1024)  # SSH, FTP, SMTP, etc. speak first
    except OSError:
        data = b""
    if not data:
        try:
            sock.sendall(HTTP_PROBE)  # HTTP servers wait for a request
            data = sock.recv(1024)
        except OSError:
            data = b""
    return clean_banner(data)


def scan_port(ip, port):
    """Return None if the port is closed/filtered, else the banner ('' if none)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(CONNECT_TIMEOUT)
        if sock.connect_ex((ip, port)) != 0:
            return None
        return grab_banner(sock)


def main():
    print("Simple TCP port scanner")
    print("Only scan hosts you own or have explicit permission to scan.\n")

    target = prompt("Target host/IP", DEFAULT_TARGET)
    start = prompt_port("Start port", DEFAULT_START)
    end = prompt_port("End port", DEFAULT_END)
    if start > end:
        print("Start port is greater than end port; swapping them.")
        start, end = end, start

    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        sys.exit(f"Could not resolve '{target}'.")

    print(f"\nScanning {target} ({ip}), ports {start}-{end}...\n")
    began = time.time()
    open_ports = []
    try:
        for port in range(start, end + 1):
            banner = scan_port(ip, port)
            if banner is None:
                continue
            open_ports.append(port)
            suffix = f"  {banner}" if banner else ""
            print(f"  {port:>5}/tcp  open{suffix}", flush=True)
    except KeyboardInterrupt:
        print("\nInterrupted.")

    elapsed = time.time() - began
    print(f"\nDone: {len(open_ports)} open port(s) in {elapsed:.1f}s.")


if __name__ == "__main__":
    main()
