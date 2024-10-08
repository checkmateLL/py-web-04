import mimetypes
import urllib.parse
import json
import logging
import socket
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from datetime import datetime
import os

BASE_DIR = pathlib.Path()
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
#SOCKET_HOST = '127.0.0.1' # to run without docker
SOCKET_HOST = os.environ.get('SOCKET_HOST', '127.0.0.1') #to run with docker
SOCKET_PORT = 5000

STORAGE_DIR = BASE_DIR / 'storage'
DATA_FILE = STORAGE_DIR / 'data.json'


STORAGE_DIR.mkdir(exist_ok=True)
if not DATA_FILE.exists():
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)

class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SOCKET_HOST, SOCKET_PORT))
        client_socket.sendall(data)
        client_socket.close()

        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)        
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

def save_data_from_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    try:
        parse_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        timestamp = datetime.now().isoformat()
        
        try:
            with open('storage/data.json', 'r') as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = {}
        
        existing_data[timestamp] = parse_dict
        
        with open('storage/data.json', 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)

def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)
    logging.info("Starting socket server")
    try:
        while True:
            conn, address = server_socket.accept()
            logging.info(f"Connection from {address}")
            data = conn.recv(BUFFER_SIZE)
            logging.info(f"Socket received: {data}")
            save_data_from_form(data)
            conn.close()
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()

def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', HTTP_PORT)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    socket_server = threading.Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    socket_server.start()

    http_server = threading.Thread(target=run_http_server)
    http_server.start()