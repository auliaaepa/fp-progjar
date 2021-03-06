import socket
import os
import sys
import datetime
import argparse
from bs4 import BeautifulSoup
from wsgiref.handlers import format_date_time

# define receive buffer size
RECV_BUF = 4096

def get_request_header(method, urn, protocol, host, port, type=None, length=None):
    request_header = f"{method} {urn} {protocol}\r\n"
    request_header += f"Host: {host}:{port}\r\n"
    if type: request_header += f"Content-Type: {type}\r\n"
    if length: request_header += f"Content-Length: {length}\r\n"
    request_header += f"Date: {format_date_time(datetime.datetime.utcnow().timestamp())}\r\n"
    request_header += "\r\n"
    return request_header

def main():
    # define argument parser
    parser = argparse.ArgumentParser(allow_abbrev=False, description="HTTP client for one request")
    parser.add_argument('host', type=str, nargs='?', default="localhost", help='HTTP server host (default: localhost)')
    parser.add_argument('port', type=int, nargs='?', default=8000, help='HTTP server port (default: 8000)')
    parser.add_argument('--method', type=str, default="GET", help='HTTP request method (default: GET)')
    parser.add_argument('--urn', type=str, default="/", help='HTTP request urn (default: /)')
    parser.add_argument('--protocol', type=str, default="HTTP/1.1", help='HTTP request protocol (default: HTTP/1.1)')
    parser.add_argument('--body', type=str, default="", help='HTTP request body')

    # get arguments
    args = parser.parse_args()
    host = args.host
    port = args.port
    request_method = args.method.upper()
    request_urn = args.urn
    request_protocol = args.protocol
    request_body = args.body

    # initialize socket object with AF_INET as address family and SOCK_STREAM as socket type
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect socket to the given address
    client_socket.connect((host, port))

    if request_method == "GET":
        # send request to server
        request_header = get_request_header(request_method, request_urn, request_protocol, host, port)
        client_socket.sendall(request_header.encode())

        # receive response from server
        response = client_socket.recv(RECV_BUF).decode()
        response_header, response_body = tuple(response.split("\r\n\r\n"))
        response_location = None
        for header in response_header.split("\r\n")[1:]:
            if "Content-Length" in header:
                response_length = int(header.split()[1])                
                while len(response_body) < response_length:
                    response_body += client_socket.recv(RECV_BUF).decode()
            elif "Location" in header:
                response_location = header.split()[1]
        
        # parsing the reponse body
        response_body = "".join(line.strip() for line in response_body.split("\n"))
        soup = BeautifulSoup(response_body, "html.parser")
        tag = soup.find('body')
        for string in tag.strings:
            print(string)
        
        # redirection
        if response_location:
            print("===REDIRECTION===")
            python_version = "python3" if sys.version_info[0]==3 else "python"
            os.system(f"{python_version} client.py {host} {port} --method {request_method} --urn {response_location} --protocol {request_protocol}")
    elif request_method == "HEAD":
        # send request to server
        request_header = get_request_header(request_method, request_urn, request_protocol, host, port)
        client_socket.sendall(request_header.encode())

        # receive response from server
        response = client_socket.recv(RECV_BUF).decode()
        response_header, response_body = tuple(response.split("\r\n\r\n"))
        response_location = None
        for header in response_header.split("\r\n")[1:]:
            if "Location" in header:
                response_location = header.split()[1]

        # only print reponse header
        print(response_header)
        
        # redirection
        if response_location:
            print("===REDIRECTION===")
            python_version = "python3" if sys.version_info[0]==3 else "python"
            os.system(f"{python_version} client.py {host} {port} --method {request_method} --urn {response_location} --protocol {request_protocol}")
    elif request_method == "POST":
        # send request to server
        content_type = "application/x-www-form-urlencoded"
        request_header = get_request_header(request_method, request_urn, request_protocol, host, port, content_type, len(request_body))
        client_socket.sendall(request_header.encode() + request_body.encode())

        # receive response from server
        response = client_socket.recv(RECV_BUF).decode()
        response_header, response_body = tuple(response.split("\r\n\r\n"))
        header_split = response_header.split("\r\n")
        for header in header_split[1:]:
            if "Content-Length" in header:
                response_length = int(header.split()[1])                
                while len(response_body) < response_length:
                    response_body += client_socket.recv(RECV_BUF).decode()
        
        # parsing the reponse body
        response_body = "".join(line.strip() for line in response_body.split("\n"))
        soup = BeautifulSoup(response_body, "html.parser")
        tag = soup.find('body')
        for string in tag.strings:
            print(string)

if __name__ == "__main__":
    main()