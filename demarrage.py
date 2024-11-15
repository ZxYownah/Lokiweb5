import os
import sys
import json
import time
import argparse
import threading
from queue import Queue
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from termcolor import colored

VERSION = "v0.5.3"
BANNER = """
       _______  _        _______                   __________________ _______  ______ 
|\     /|(  ___  )( (    /|(  ____ \|\     /||\     /|\__   __/\__   __/(  ____ )(  __  \
| )   ( || (   ) ||  \  ( || (    \/( \   / )| )   ( |   ) (      ) (   | (    )|| (  \  )
| (___) || |   | ||   \ | || (__     \ (_) / | (___) |   | |      | |   | (____)|| |   ) |
|  ___  || |   | || (\ \) ||  __)     \   /  |  ___  |   | |      | |   |  _____)| |   | |
| (   ) || |   | || | \   || (         ) (   | (   ) |   | |      | |   | (      | |   ) |
| )   ( || (___) || )  \  || (____/\   | |   | )   ( |   | |      | |   | )      | (__/  )
|/     \|(_______)|/    )_)(_______/   \_/   |/     \|   )_(      )_(   |/       (______/


"""


class CustomHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        code, headers, data = self.server.manager.on_GET(self.path, self.headers)
        if code != 200:
            self.server.manager.send_error(self, code, headers, data)
        else:
            self.server.manager.send_success_response(self, data, headers)

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) if 'Content-Length' in self.headers else 0
        post_data = self.rfile.read(content_length)
        code, headers, data = self.server.manager.on_POST(self.path, self.headers, post_data)
        if code != 200:
            self.server.manager.send_error(self, code, headers, data)
        else:
            self.server.manager.send_success_response(self, data, headers)


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class ServerManager:

    def __init__(self, config):
        self.config = config
        self.servers = []
        self.loggers = []
        self.doc_root = os.path.expanduser(config['servers'][0]['doc_root'])  # Expand ~ to home directory
        self.setup_loggers()

    def setup_loggers(self):
        for logger_name, logger_config in self.config['loggers'].items():
            if logger_config['active']:
                self.loggers.append(logger_name)

    def start_servers(self):
        for server_config in self.config['servers']:
            port = server_config['port']
            server_address = ('', port)
            server = ThreadingHTTPServer(server_address, CustomHTTPRequestHandler)
            server.manager = self
            print(colored(f"Starting server on port {port}", "green"))
            server.timeout = server_config.get('timeout', 10)
            self.servers.append(server)
            # Utilisation de `threading.Thread` pour démarrer le serveur
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.start()

    def send_error(self, handler, code, headers, message):
        handler.send_response(code)
        for header, value in headers:
            handler.send_header(header, value)
        handler.end_headers()
        handler.wfile.write(message.encode('utf-8'))

    def send_success_response(self, handler, data, headers):
        handler.send_response(200)
        for header, value in headers:
            handler.send_header(header, value)
        handler.end_headers()
        # Écrire directement les données si elles sont déjà au format bytes
        handler.wfile.write(data)

    """ OLD
    def send_success_response(self, handler, data, headers):
        handler.send_response(200)
        for header, value in headers:
            handler.send_header(header, value)
        handler.end_headers()
        handler.wfile.write(data.encode('utf-8'))
    """

    def on_request(self, handler):
        if not handler.path.startswith("/"):
            return 400, [("Connection", "close")], "Bad Request"
        return None, None

    def on_GET(self, path, headers):
        # Map root path '/' to 'index.html' by default
        if path == "/":
            path = "/index.html"

        # Construct full file path
        full_path = os.path.join(self.doc_root, path.lstrip("/"))

        # Serve the file if it exists
        if os.path.isfile(full_path):
            with open(full_path, "rb") as file:
                data = file.read()
            return 200, [("Content-Type", "text/html")], data
        else:
            # File not found
            return 404, [("Content-Type", "text/html")], "<html><body>Page Not Found</body></html>"

    def on_POST(self, path, headers, post_data):
        return 200, [("Content-Type", "text/html")], "<html><body>POST data received</body></html>"

    def on_complete(self, client, code, req_headers, res_headers, request, response):
        print(f"Request from {client} completed with code {code}.")


if __name__ == '__main__':
    print(colored(BANNER, 'yellow'))
    print(f"Welcome to HoneyHTTPd {VERSION}\n")

    parser = argparse.ArgumentParser(description='Start a custom HTTP server.')
    parser.add_argument('--config', help='Path to configuration file', required=True)
    args = parser.parse_args()

    config_path = args.config
    if not os.path.exists(config_path):
        print(colored("Configuration file not found.", "red"))
        sys.exit(1)

    with open(config_path, "r") as file:
        config = json.load(file)

    manager = ServerManager(config)
    manager.start_servers()
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
