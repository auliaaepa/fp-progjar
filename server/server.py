import socket
import select
import threading
import queue
import os
import configparser
import mimetypes
import datetime
from wsgiref.handlers import format_date_time
import time

from requests import request

RECV_BUF = 4096
BACKLOG = 5
CONF_FILE = "httpserver.conf"

class ServerResponseThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.q = queue.Queue()

    def add(self, client_socket, request_method, request_urn, request_protocol, request_body):
        """put tuple (client socket, request method, request urn, request protocol, request body) to queue"""
        self.q.put((client_socket, request_method, request_urn, request_protocol, request_body))

    def stop(self):
        """stop server"""
        self.running = False

    def run(self):
        """respond to the client in the queue when server running"""
        while self.running:
            try:
                client_socket, request_method, request_urn, request_protocol, request_body = self.q.get(block=True, timeout=1)
                self.send_response(client_socket, request_method, request_urn, request_protocol, request_body)
            except queue.Empty:
                pass
    
    def send_response(self, client_socket, request_method, request_urn, request_protocol, request_body):
        """send a response to client socket based on client request"""
        # get requested file name
        request_file = request_urn
        if request_file[0] == "/": request_file = request_file[1:]
        if request_file == "": request_file = "index.html"
        
        if request_method == "GET":
            if os.path.isfile(request_file):
                # send response in the form of file attachment
                with open(request_file, "rb") as file:
                    response_content = file.read()
                response_status = "200 OK"
                content_mime = mimetypes.guess_type(request_file)[0]
                content_length = len(response_content)
                response_header = self.get_response_header(response_status, content_mime, content_length)
            else:
                # send response in the form of 404.html if urn invalid 
                with open("404.html", "rb") as file:
                    response_content = file.read()
                response_status = "404 Not Found"
                content_mime = "text/html"
                content_length = len(response_content)
                response_header = self.get_response_header(response_status, content_mime, content_length)
        elif request_method == "POST":
            if request_file == "registrasi.html":
                if request_body != "":
                    body_split = request_body.split("&")
                    for input in body_split:
                        if "email" in input:
                            email = input.split("=")
                        elif "password" in input:
                            password = input.split("=")                    
                    if len(body_split) == 2 and email and password:
                        with open("sukses.html", "rb") as file:
                            response_content = file.read()
                        response_status = "200 OK"
                        content_mime = "text/html"
                        content_length = len(response_content)
                        response_header = self.get_response_header(response_status, content_mime, content_length)
            else:
                # send response in the form of 404.html if urn invalid 
                with open("404.html", "rb") as file:
                    response_content = file.read()
                response_status = "404 Not Found"
                content_mime = "text/html"
                content_length = len(response_content)
                response_header = self.get_response_header(response_status, content_mime, content_length)
        
        # send response
        client_socket.sendall(response_header.encode()+response_content)
        print("SEND", client_socket.getpeername())

    def get_response_header(self, status, mime, length):
        """generate response header"""
        response_header = "HTTP/1.1 " + status + "\r\n"
        response_header += "Content-Type: " + mime + "; charset=UTF-8\r\n"
        response_header += "Content-Length: " + str(length) + "\r\n"
        response_header += "Date: " + format_date_time(datetime.datetime.utcnow().timestamp()) + "\r\n"
        response_header += "\r\n"
        return response_header

def main():
    # initialize ServerResponseThread object and start it
    server_response = ServerResponseThread()
    server_response.start()

    # initialize socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # get port for "localhost" from config file and bind to it
    config = configparser.ConfigParser()
    config.read(CONF_FILE)
    host = "localhost"
    port = int(config[host]["Port"])
    print("Server address:", host, port)
    server_socket.bind((host, port))

    # listen to client
    server_socket.listen(BACKLOG)

    while True:
        try:
            # accept client
            client_socket, client_address = server_socket.accept()
            # time.sleep(5)
            ready = select.select([client_socket, ], [], [], 2)
            # print(ready)
            if ready[0]:
                # receive request and send response to the valid request
                client_request = ready[0][0].recv(RECV_BUF).decode()
                if client_request != "": 
                    request_header, request_body = tuple(client_request.split("\r\n\r\n")) 
                    request_method, request_urn, request_protocol = tuple(request_header.split("\r\n")[0].split())
                    request_header = request_header.split("\r\n")[1:]
                    for header in request_header:
                        if "Content-Length" in header:
                            request_length = int(header.split()[1])
                            while len(request_body) < request_length:
                                request_body += client_socket.recv(RECV_BUF).decode()
                    print("RECV", ready[0][0].getpeername(), request_method, request_urn, request_protocol)
                    server_response.add(ready[0][0], request_method, request_urn, request_protocol, request_body)

        except KeyboardInterrupt:
            print("Stop")
            break

        except socket.error:
            print("Socket error!")
            break

    server_response.stop()
    server_response.join()

if __name__ == "__main__":
    main()