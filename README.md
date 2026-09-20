# Network Port Scanner

A small TCP port scanner written in Python. It checks which ports are open on a host and grabs a quick banner from each open service. It uses only the standard library, so there is nothing to install.

> **Only scan hosts you own or have explicit permission to scan.** Scanning others without permission can be illegal, even for "just testing." `scanme.nmap.org` is a public host the Nmap project provides for practice; use it sparingly.

## Features

- Prompts for a target, start port and end port (defaults: `127.0.0.1`, ports `1-1024`).
- Lists every open port as it is found.
- Banner grab on each open port: reads the greeting a service sends, or sends a small HTTP request to services that wait for one.
- Pure standard library. No admin rights needed.
- Ctrl+C stops a scan and still prints a summary.

## Requirements

Python 3 (developed and tested on 3.14). No third-party packages.

## Usage

```
python port_scanner.py
```

Example (real output from `scanme.nmap.org`, ports 80-443):

```
Target host/IP [127.0.0.1]: scanme.nmap.org
Start port [1]: 80
End port [1024]: 443

Scanning scanme.nmap.org (45.33.32.156), ports 80-443...

     80/tcp  open  HTTP/1.1 200 OK

Done: 1 open port(s) in 187.3s.
```

Step-by-step instructions with a local demo are in `Port_Scanner_Step_by_Step.pdf`.

## How it works

It is a **TCP connect scan**: for each port, the script asks the operating system to open a normal connection and records what happens.

1. **DNS lookup.** A host name is resolved to an IPv4 address once, up front.
2. **TCP handshake per port.** The reply decides the result:

   ```
   Scanner                           Target port
      |  ---- SYN ----------------->  |
      |  <--- SYN-ACK -------------   |   port OPEN
      |  ---- ACK ----------------->  |   (connection made)
      |  <--- "SSH-2.0-dropbear" --   |   banner grab

      |  ---- SYN ----------------->  |
      |  <--- RST -----------------   |   port CLOSED

      |  ---- SYN ----------------->  |
      |  ...no reply, times out...    |   port FILTERED (firewall drops it)
   ```

3. **Banner grab.** Services such as SSH, FTP and SMTP speak first, so the script just reads. Web servers wait for a request, so if nothing arrives the script sends `HEAD / HTTP/1.0` and reads the reply. Only the first printable line is shown.
4. **Summary.** Open ports and elapsed time are printed at the end.

Closed and filtered ports are simply not listed.

## Settings

Two constants at the top of `port_scanner.py`:

| Constant | Default | Meaning |
|---|---|---|
| `CONNECT_TIMEOUT` | `0.5` | Seconds to wait for a connection. If scans of distant or high-latency hosts miss services, consider increasing it. |
| `BANNER_TIMEOUT` | `1.0` | Seconds to wait for a banner on an open port. |

On Windows a refused connection takes about 2 seconds to fail, so `CONNECT_TIMEOUT` effectively sets how long each closed port costs. Scanning the full default range (`1-1024`) may take several minutes.

## Tests

```
python -m unittest -v
```

The tests start small servers on `127.0.0.1` and never touch the network.

## Limitations

- Single-threaded, so wide port ranges are slow.
- TCP and IPv4 only (no UDP, no IPv6).
- Cannot tell a closed port from a firewalled one.
- HTTPS/TLS banners (for example port 443) are not decoded.
- Connect scans show up in the target's logs.

## Ideas for next steps

- Scan ports in parallel with `concurrent.futures.ThreadPoolExecutor` (the biggest speedup).
- Show service names with `socket.getservbyport`.
- Save results to CSV or JSON.
- Accept the target and range as command-line arguments.
- Add UDP scanning and TLS banner grabbing.

## Files

| File | Purpose |
|---|---|
| `port_scanner.py` | The scanner. |
| `test_port_scanner.py` | Unit tests (localhost only). |
| `Port_Scanner_Step_by_Step.pdf` | Step-by-step guide. |
| `README.md` | This file. |
