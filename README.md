# TFTPClient
네트워크 기말과제
이과제는 네트워크 프로그래밍 기말과제 입니다.


이 코드는 TFTP(Tiny File Transfer Protocol) 클라이언트를 구현하고 있습니다. TFTP는 파일을 전송하기 위한 간단한 프로토콜로, 주로 부트로더나 임베디드 시스템 등에서 사용됩니다. 코드를 각 부분별로 설명하겠습니다:

모듈 임포트 및 설정값 정의:

socket, argparse, sys, struct 모듈을 임포트합니다.
TFTP의 기본 설정값, 메시지 타입, 오류 코드 등을 정의합니다.
함수 정의:

서버에 WRQ(Write Request) 메시지를 보내는 send_wrq 함수와 RRQ(Read Request) 메시지를 보내는 send_rrq 함수 등을 정의합니다.
ACK, DATA 등의 메시지를 서버로 보내는 함수들이 있습니다.
파일을 서버로부터 받는 receive_file 함수와 서버에 파일을 보내는 send_file 함수가 정의되어 있습니다.
명령행 인자 파싱:

argparse 모듈을 사용하여 명령행 인자를 파싱합니다. 서버 주소, 액션(get 또는 put), 전송할 파일 이름 등을 받아옵니다.
서버 설정 및 소켓 생성:

명령행 인자로 받은 서버 주소와 포트를 설정합니다. 포트 번호가 명시되지 않으면 기본 포트인 69번을 사용합니다.
UDP 소켓을 생성하고 타임아웃을 설정합니다.
액션(get 또는 put)에 따라 처리:

사용자가 get 액션을 선택한 경우, 서버에 RRQ 메시지를 보내고 파일을 받는 receive_file 함수를 호출합니다.
사용자가 put 액션을 선택한 경우, 서버에 WRQ 메시지를 보내고 파일을 보내는 send_file 함수를 호출합니다.
