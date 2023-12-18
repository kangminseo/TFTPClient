import socket
import argparse
from struct import pack
import time
import sys

DEFAULT_PORT = 69
BLOCK_SIZE = 512
DEFAULT_TRANSFER_MODE = 'octet'

OPCODE = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}
MODE = {'netascii': 1, 'octet': 2, 'mail': 3}

ERROR_CODE = {
    0: "Not defined, see error message (if any).",
    1: "File not found.",
    2: "Access violation.",
    3: "Disk full or allocation exceeded.",
    4: "Illegal TFTP operation.",
    5: "Unknown transfer ID.",
    6: "File already exists.",
    7: "No such user."
}


def send_wrq(filename, mode):
    format_str = f'>h{len(filename)}sB{len(mode)}sB'
    wrq_message = pack(format_str, OPCODE['WRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
    sock.sendto(wrq_message, server_address)
    print(wrq_message)
    timeout = time.time() + 10  # Timeout set to 10 seconds
    ack_received = False

    while True:
        if time.time() > timeout:
            print("Timeout: No ACK received.")
            break

        try:
            data, _ = sock.recvfrom(4)
            opcode = int.from_bytes(data[:2], 'big')
            ack_block = int.from_bytes(data[2:4], 'big')
            if opcode == OPCODE['ACK'] and ack_block == 0:  # Expected ACK
                ack_received = True
                print("ACK 0 received.")
                break
        except socket.error:
            pass

    if not ack_received:
        print("No valid response received. Transmission failed.")
        sys.exit(1)


def send_rrq(filename, mode):
    format_str = f'>h{len(filename)}sB{len(mode)}sB'
    rrq_message = pack(format_str, OPCODE['RRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
    sock.sendto(rrq_message, server_address)
    print(rrq_message)


def send_ack(seq_num, server):
    format_str = '>hh'
    ack_message = pack(format_str, OPCODE['ACK'], seq_num)
    sock.sendto(ack_message, server)
    print(seq_num)
    print(ack_message)


def send_file(filename):
    file = open(filename, 'rb')
    block_number = 1

    while True:
        file_block = file.read(BLOCK_SIZE)
        data = pack(f'>hh{len(file_block)}s', OPCODE['DATA'], block_number, file_block)
        sock.sendto(data, server_address)

        expected_ack = pack('>hh', OPCODE['ACK'], block_number)
        resend_attempts = 0
        while resend_attempts < 3:
            try:
                ack, _ = sock.recvfrom(4)
                if ack == expected_ack:
                    break
            except socket.timeout:
                print("Timeout: Resending data.")
                sock.sendto(data, server_address)
                resend_attempts += 1

        if resend_attempts == 3:
            print("Failed to receive ACK. Transmission aborted.")
            sys.exit(1)

        if len(file_block) < BLOCK_SIZE:
            break

        block_number += 1

    file.close()
    print("File sent successfully.")


# parse command line arguments
parser = argparse.ArgumentParser(description='TFTP client program')
parser.add_argument(dest="host", help="Server IP address", type=str)
parser.add_argument(dest="operation", help="get or put a file", type=str)
parser.add_argument(dest="filename", help="name of file to transfer", type=str)
parser.add_argument("-p", "--port", dest="port", type=int)
args = parser.parse_args()

server_ip = args.host
server_port = args.port if args.port is not None else DEFAULT_PORT
server_address = (server_ip, server_port)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)  # Set socket timeout to 5 seconds

mode = DEFAULT_TRANSFER_MODE
operation = args.operation
filename = args.filename

if operation == 'get':
    send_rrq(filename, mode)
    file = open(filename, 'wb')
    expected_block_number = 1

    while True:
        data, server_new_socket = sock.recvfrom(516)
        opcode = int.from_bytes(data[:2], 'big')

        if opcode == OPCODE['DATA']:
            block_number = int.from_bytes(data[2:4], 'big')
            if block_number == expected_block_number:
                send_ack(block_number, server_new_socket)
                file_block = data[4:]
                file.write(file_block)
                expected_block_number += 1
                print(file_block.decode())
            else:
                send_ack(block_number, server_new_socket)

        elif opcode == OPCODE['ERROR']:
            error_code = int.from_bytes(data[2:4], byteorder='big')
            print(ERROR_CODE[error_code])
            break

        else:
            break

        if len(file_block) < BLOCK_SIZE:
            file.close()
            print(len(file_block))
            break

elif operation == 'put':
    send_wrq(filename, mode)
    send_file(filename)

sock.close()
