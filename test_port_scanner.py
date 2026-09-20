"""Unit tests for port_scanner.py. They only touch 127.0.0.1."""

import socket
import threading
import unittest
from unittest import mock

import port_scanner


def listen(handler):
    """Start a localhost server on a free port and call handler(conn) per connection."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen()

    def serve():
        while True:
            try:
                conn, _ = server.accept()
            except OSError:  # server socket was closed
                return
            handler(conn)

    threading.Thread(target=serve, daemon=True).start()
    return server, server.getsockname()[1]


def send_ssh_banner(conn):
    conn.sendall(b"SSH-2.0-TestServer_1.0\r\n")
    conn.close()


def answer_http(conn):
    conn.settimeout(2)
    conn.recv(1024)
    conn.sendall(b"HTTP/1.0 200 OK\r\nServer: TestHTTP\r\n\r\n")
    conn.close()


class ScanPortTests(unittest.TestCase):
    def start(self, handler):
        server, port = listen(handler)
        self.addCleanup(server.close)
        return port

    def test_reads_banner_sent_on_connect(self):
        port = self.start(send_ssh_banner)
        self.assertEqual(port_scanner.scan_port("127.0.0.1", port), "SSH-2.0-TestServer_1.0")

    def test_probes_service_that_waits_for_a_request(self):
        port = self.start(answer_http)
        self.assertEqual(port_scanner.scan_port("127.0.0.1", port), "HTTP/1.0 200 OK")

    def test_open_port_without_banner_returns_empty_string(self):
        held = []
        self.addCleanup(lambda: [conn.close() for conn in held])
        port = self.start(held.append)  # accepts the connection, never speaks
        with mock.patch.object(port_scanner, "BANNER_TIMEOUT", 0.2):
            self.assertEqual(port_scanner.scan_port("127.0.0.1", port), "")

    def test_closed_port_returns_none(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.assertIsNone(port_scanner.scan_port("127.0.0.1", port))


class CleanBannerTests(unittest.TestCase):
    def test_keeps_only_first_line(self):
        self.assertEqual(port_scanner.clean_banner(b"SSH-2.0-x\r\nsecond line"), "SSH-2.0-x")

    def test_empty_input(self):
        self.assertEqual(port_scanner.clean_banner(b""), "")

    def test_drops_binary_junk(self):
        self.assertEqual(port_scanner.clean_banner(b"\x00\x01\xff"), "")

    def test_caps_length_at_100(self):
        self.assertEqual(len(port_scanner.clean_banner(b"A" * 500)), 100)


class PromptPortTests(unittest.TestCase):
    def test_empty_input_uses_default(self):
        with mock.patch("builtins.input", return_value=""):
            self.assertEqual(port_scanner.prompt_port("Start port", 1), 1)

    def test_rejects_bad_values_until_valid(self):
        with mock.patch("builtins.input", side_effect=["abc", "0", "70000", "8080"]), \
                mock.patch("builtins.print"):
            self.assertEqual(port_scanner.prompt_port("Start port", 1), 8080)


if __name__ == "__main__":
    unittest.main()
