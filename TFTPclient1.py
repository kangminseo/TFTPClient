import socket
import argparse
import sys
from struct import pack

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

class TFTPClient:
    def __init__(self, server_address):
        self.server_address = server_address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(10)

    def send_wrq(self, filename, mode):
        format_str = f'>h{len(filename)}sB{len(mode)}sB'
        wrq_message = pack(format_str, OPCODE['WRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
        self.sock.sendto(wrq_message, self.server_address)

    def send_rrq(self, filename, mode):
        format_str = f'>h{len(filename)}sB{len(mode)}sB'
        rrq_message = pack(format_str, OPCODE['RRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
        self.sock.sendto(rrq_message, self.server_address)

    def send_ack(self, seq_num):
        format_str = '>hh'
        ack_message = pack(format_str, OPCODE['ACK'], seq_num)
        self.sock.sendto(ack_message, self.server_address)

    def send_data(self, seq_num, data):
        format_str = f'>hh{len(data)}s'
        data_message = pack(format_str, OPCODE['DATA'], seq_num, data)
        self.sock.sendto(data_message, self.server_address)

    def receive_file(self, filename):
        file = open(filename, "wb")
        seq_number = 0

        while True:
            data, _ = self.sock.recvfrom(516)
            opcode = int.from_bytes(data[:2], 'big')

            if opcode == OPCODE['DATA']:
                seq_number = int.from_bytes(data[2:4], 'big')
                self.send_ack(seq_number)

                file_block = data[4:]
                file.write(file_block)

                if len(file_block) < BLOCK_SIZE:
                    file.close()
                    break

            elif opcode == OPCODE['ERROR']:
                error_code = int.from_bytes(data[2:4], byteorder='big')
                print(ERROR_CODE[error_code])
                break

            else:
                break

    def send_file(self, filename):
        try:
            file_to_send = open(filename, "rb")

            while True:
                data, _ = self.sock.recvfrom(516)
                opcode = int.from_bytes(data[:2], 'big')

                if opcode == OPCODE['ACK']:
                    seq_number = int.from_bytes(data[2:4], 'big') + 1
                    line = file_to_send.read(512)

                    if not line:
                        self.send_data(seq_number, b'')
                        break

                    self.send_data(seq_number, line)

                    if len(line) < BLOCK_SIZE:
                        file_to_send.close()
                        break

        except FileNotFoundError:
            print("파일을 찾을 수 없습니다.")
            sys.exit(1)

    def close(self):
        self.sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TFTP 클라이언트 프로그램')
    parser.add_argument(dest="host", help="서버 IP 주소", type=str)
    parser.add_argument(dest="action", help="파일 put 또는 get", type=str)
    parser.add_argument(dest="filename", help="전송할 파일 이름", type=str)
    parser.add_argument("-p", "--port", dest="port", action="store", type=int)
    args = parser.parse_args()

    server_ip = args.host
    server_port = args.port if args.port is not None else DEFAULT_PORT
    server_address = (server_ip, server_port)

    tftp_client = TFTPClient(server_address)

    mode = DEFAULT_TRANSFER_MODE
    filename = args.filename

    if args.action == 'get':
        tftp_client.send_rrq(filename, mode)
        tftp_client.receive_file(filename)
        print("전송 성공")

    elif args.action == 'put':
        tftp_client.send_wrq(filename, mode)
        tftp_client.send_file(filename)
        print("전송 성공")

    tftp_client.close()
