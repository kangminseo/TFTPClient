import socket
import argparse
from struct import pack
import time
import sys

# 기본 값 설정
DEFAULT_PORT = 69
BLOCK_SIZE = 512
DEFAULT_TRANSFER_MODE = 'octet'

# TFTP 통신을 위한 코드, 모드, 에러 코드 정의
OPCODE = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}
MODE = {'netascii': 1, 'octet': 2, 'mail': 3}
ERROR_CODE = {
    0: "정의되지 않음, 에러 메시지 참조 (있는 경우).",
    1: "파일을 찾을 수 없음.",
    2: "접근 위반.",
    3: "디스크 공간 부족 또는 할당 초과.",
    4: "잘못된 TFTP 작업.",
    5: "알 수 없는 전송 ID.",
    6: "파일이 이미 존재함.",
    7: "해당 사용자가 없음."
}

# 서버에 Write Request (WRQ) 메시지 전송
def send_wrq(filename, mode):
    format_str = f'>h{len(filename)}sB{len(mode)}sB'
    wrq_message = pack(format_str, OPCODE['WRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
    sock.sendto(wrq_message, server_address)
    print(wrq_message)
    timeout = time.time() + 10  # 10초 동안의 타임아웃 설정
    ack_received = False

    while True:
        if time.time() > timeout:
            print("타임아웃: ACK를 받지 못함.")
            break

        try:
            data, _ = sock.recvfrom(4)
            opcode = int.from_bytes(data[:2], 'big')
            ack_block = int.from_bytes(data[2:4], 'big')
            if opcode == OPCODE['ACK'] and ack_block == 0:  # 예상한 ACK 수신
                ack_received = True
                print("ACK 0 받음.")
                break
        except socket.error:
            pass

    if not ack_received:
        print("유효한 응답을 받지 못했습니다. 전송 실패.")
        sys.exit(1)


# 서버에 Read Request (RRQ) 메시지 전송
def send_rrq(filename, mode):
    format_str = f'>h{len(filename)}sB{len(mode)}sB'
    rrq_message = pack(format_str, OPCODE['RRQ'], bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
    sock.sendto(rrq_message, server_address)
    print(rrq_message)


# ACK 메시지 전송
def send_ack(seq_num, server):
    format_str = '>hh'
    ack_message = pack(format_str, OPCODE['ACK'], seq_num)
    sock.sendto(ack_message, server)
    print(seq_num)
    print(ack_message)


# 파일 전송
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
                print("타임아웃: 데이터 재전송.")
                sock.sendto(data, server_address)
                resend_attempts += 1

        if resend_attempts == 3:
            print("ACK 받지 못함. 전송 중단.")
            sys.exit(1)

        if len(file_block) < BLOCK_SIZE:
            break

        block_number += 1

    file.close()
    print("파일 전송 성공.")


# 명령줄 인자 파싱
parser = argparse.ArgumentParser(description='TFTP 클라이언트 프로그램')
parser.add_argument(dest="host", help="서버 IP 주소", type=str)
parser.add_argument(dest="operation", help="파일 가져오기 또는 전송", type=str)
parser.add_argument(dest="filename", help="전송할 파일 이름", type=str)
parser.add_argument("-p", "--port", dest="port", type=int)
args = parser.parse_args()

server_ip = args.host
server_port = args.port if args.port is not None else DEFAULT_PORT
server_address = (server_ip, server_port)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)  # 소켓 타임아웃을 5초로 설정

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
