import argparse
import struct
import time
from threading import Thread

import serial
import serial.tools.list_ports
# 기존 gamepad 라이브러리는 여기서는 사용하지 않음
# import vgamepad as vg

from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController

parser = argparse.ArgumentParser(description='DJI Mavic 3 RC231, RC-N1)')
parser.add_argument('-p', '--port', help='RC Serial Port', default="COM9")
args = parser.parse_args()

# DJI RC의 시리얼 포트를 탐색하여 열기
try:
    s = None
    ports = serial.tools.list_ports.comports(True)
    for port in ports:
        try:
            print(port.description)
            if "For Protocol" in port.description:
                print("found DJI USB VCOM For Protocol")
                s = serial.Serial(port=port.name, baudrate=115200)
                print('Opened serial port:', s.name)
                break  # 원하는 포트를 찾으면 종료
            else:
                print("skip")
        except (OSError, serial.SerialException):
            pass
    if s is None:
        print("DJI RC 시리얼 포트를 찾지 못했습니다.")
        exit(1)
except serial.SerialException as e:
    print('Could not open serial port:', e)
    exit(1)

print('app version: 3.0.0\n')
print('\nDji RC231 emulation started...\n')
print('\nClose terminal to stop\n')
print('*******************************************************\n')
print('* Telegram: https://t.me/DJI_RC_N1_SIMULATOR_FLY_DC   *\n')
print('* Donate: https://www.buymeacoffee.com/ivanyakymenko  *\n')
print('*******************************************************\n')


# =======================================================================
# 체크섬 계산 함수들 (원본 코드 내용)
# =======================================================================
def calc_checksum(packet, plength):
    crc = [0x0000, 0x1189, 0x2312, 0x329b, 0x4624, 0x57ad, 0x6536, 0x74bf,
           0x8c48, 0x9dc1, 0xaf5a, 0xbed3, 0xca6c, 0xdbe5, 0xe97e, 0xf8f7,
           0x1081, 0x0108, 0x3393, 0x221a, 0x56a5, 0x472c, 0x75b7, 0x643e,
           0x9cc9, 0x8d40, 0xbfdb, 0xae52, 0xdaed, 0xcb64, 0xf9ff, 0xe876,
           0x2102, 0x308b, 0x0210, 0x1399, 0x6726, 0x76af, 0x4434, 0x55bd,
           0xad4a, 0xbcc3, 0x8e58, 0x9fd1, 0xeb6e, 0xfae7, 0xc87c, 0xd9f5,
           0x3183, 0x200a, 0x1291, 0x0318, 0x77a7, 0x662e, 0x54b5, 0x453c,
           0xbdcb, 0xac42, 0x9ed9, 0x8f50, 0xfbef, 0xea66, 0xd8fd, 0xc974,
           0x4204, 0x538d, 0x6116, 0x709f, 0x0420, 0x15a9, 0x2732, 0x36bb,
           0xce4c, 0xdfc5, 0xed5e, 0xfcd7, 0x8868, 0x99e1, 0xab7a, 0xbaf3,
           0x5285, 0x430c, 0x7197, 0x601e, 0x14a1, 0x0528, 0x37b3, 0x263a,
           0xdecd, 0xcf44, 0xfddf, 0xec56, 0x98e9, 0x8960, 0xbbfb, 0xaa72,
           0x6306, 0x728f, 0x4014, 0x519d, 0x2522, 0x34ab, 0x0630, 0x17b9,
           0xef4e, 0xfec7, 0xcc5c, 0xddd5, 0xa96a, 0xb8e3, 0x8a78, 0x9bf1,
           0x7387, 0x620e, 0x5095, 0x411c, 0x35a3, 0x242a, 0x16b1, 0x0738,
           0xffcf, 0xee46, 0xdcdd, 0xcd54, 0xb9eb, 0xa862, 0x9af9, 0x8b70,
           0x8408, 0x9581, 0xa71a, 0xb693, 0xc22c, 0xd3a5, 0xe13e, 0xf0b7,
           0x0840, 0x19c9, 0x2b52, 0x3adb, 0x4e64, 0x5fed, 0x6d76, 0x7cff,
           0x9489, 0x8500, 0xb79b, 0xa612, 0xd2ad, 0xc324, 0xf1bf, 0xe036,
           0x18c1, 0x0948, 0x3bd3, 0x2a5a, 0x5ee5, 0x4f6c, 0x7df7, 0x6c7e,
           0xa50a, 0xb483, 0x8618, 0x9791, 0xe32e, 0xf2a7, 0xc03c, 0xd1b5,
           0x2942, 0x38cb, 0x0a50, 0x1bd9, 0x6f66, 0x7eef, 0x4c74, 0x5dfd,
           0xb58b, 0xa402, 0x9699, 0x8710, 0xf3af, 0xe226, 0xd0bd, 0xc134,
           0x39c3, 0x284a, 0x1ad1, 0x0b58, 0x7fe7, 0x6e6e, 0x5cf5, 0x4d7c,
           0xc60c, 0xd785, 0xe51e, 0xf497, 0x8028, 0x91a1, 0xa33a, 0xb2b3,
           0x4a44, 0x5bcd, 0x6956, 0x78df, 0x0c60, 0x1de9, 0x2f72, 0x3efb,
           0xd68d, 0xc704, 0xf59f, 0xe416, 0x90a9, 0x8120, 0xb3bb, 0xa232,
           0x5ac5, 0x4b4c, 0x79d7, 0x685e, 0x1ce1, 0x0d68, 0x3ff3, 0x2e7a,
           0xe70e, 0xf687, 0xc41c, 0xd595, 0xa12a, 0xb0a3, 0x8238, 0x93b1,
           0x6b46, 0x7acf, 0x4854, 0x59dd, 0x2d62, 0x3ceb, 0x0e70, 0x1ff9,
           0xf78f, 0xe606, 0xd49d, 0xc514, 0xb1ab, 0xa022, 0x92b9, 0x8330,
           0x7bc7, 0x6a4e, 0x58d5, 0x495c, 0x3de3, 0x2c6a, 0x1ef1, 0x0f78]
    v = 0x3692  # DJI P3/P4/Mavic Seed
    for i in range(0, plength):
        vv = v >> 8
        v = vv ^ crc[((packet[i] ^ v) & 0xFF)]
    return v

def calc_pkt55_hdr_checksum(seed, packet, plength):
    arr_2A103 = [0x00,0x5E,0xBC,0xE2,0x61,0x3F,0xDD,0x83,0xC2,0x9C,0x7E,0x20,0xA3,0xFD,0x1F,0x41,
                 0x9D,0xC3,0x21,0x7F,0xFC,0xA2,0x40,0x1E,0x5F,0x01,0xE3,0xBD,0x3E,0x60,0x82,0xDC,
                 0x23,0x7D,0x9F,0xC1,0x42,0x1C,0xFE,0xA0,0xE1,0xBF,0x5D,0x03,0x80,0xDE,0x3C,0x62,
                 0xBE,0xE0,0x02,0x5C,0xDF,0x81,0x63,0x3D,0x7C,0x22,0xC0,0x9E,0x1D,0x43,0xA1,0xFF,
                 0x46,0x18,0xFA,0xA4,0x27,0x79,0x9B,0xC5,0x84,0xDA,0x38,0x66,0xE5,0xBB,0x59,0x07,
                 0xDB,0x85,0x67,0x39,0xBA,0xE4,0x06,0x58,0x19,0x47,0xA5,0xFB,0x78,0x26,0xC4,0x9A,
                 0x65,0x3B,0xD9,0x87,0x04,0x5A,0xB8,0xE6,0xA7,0xF9,0x1B,0x45,0xC6,0x98,0x7A,0x24,
                 0xF8,0xA6,0x44,0x1A,0x99,0xC7,0x25,0x7B,0x3A,0x64,0x86,0xD8,0x5B,0x05,0xE7,0xB9,
                 0x8C,0xD2,0x30,0x6E,0xED,0xB3,0x51,0x0F,0x4E,0x10,0xF2,0xAC,0x2F,0x71,0x93,0xCD,
                 0x11,0x4F,0xAD,0xF3,0x70,0x2E,0xCC,0x92,0xD3,0x8D,0x6F,0x31,0xB2,0xEC,0x0E,0x50,
                 0xAF,0xF1,0x13,0x4D,0xCE,0x90,0x72,0x2C,0x6D,0x33,0xD1,0x8F,0x0C,0x52,0xB0,0xEE,
                 0x32,0x6C,0x8E,0xD0,0x53,0x0D,0xEF,0xB1,0xF0,0xAE,0x4C,0x12,0x91,0xCF,0x2D,0x73,
                 0xCA,0x94,0x76,0x28,0xAB,0xF5,0x17,0x49,0x08,0x56,0xB4,0xEA,0x69,0x37,0xD5,0x8B,
                 0x57,0x09,0xEB,0xB5,0x36,0x68,0x8A,0xD4,0x95,0xCB,0x29,0x77,0xF4,0xAA,0x48,0x16,
                 0xE9,0xB7,0x55,0x0B,0x88,0xD6,0x34,0x6A,0x2B,0x75,0x97,0xC9,0x4A,0x14,0xF6,0xA8,
                 0x74,0x2A,0xC8,0x96,0x15,0x4B,0xA9,0xF7,0xB6,0xE8,0x0A,0x54,0xD7,0x89,0x6B,0x35]
    chksum = seed
    for i in range(0, plength):
        chksum = arr_2A103[((packet[i] ^ chksum) & 0xFF)]
    return chksum

def send_duml(s, source, target, cmd_type, cmd_set, cmd_id, payload=None):
    sequence_number = 0x34eb
    packet = bytearray.fromhex('55')
    length = 13
    if payload is not None:
        length = length + len(payload)

    if length > 0x3ff:
        print("Packet too large")
        exit(1)

    packet += struct.pack('B', length & 0xff)
    packet += struct.pack('B', (length >> 8) | 0x4)
    hdr_crc = calc_pkt55_hdr_checksum(0x77, packet, 3)
    packet += struct.pack('B', hdr_crc)
    packet += struct.pack('B', source)
    packet += struct.pack('B', target)
    packet += struct.pack('<H', sequence_number)
    packet += struct.pack('B', cmd_type)
    packet += struct.pack('B', cmd_set)
    packet += struct.pack('B', cmd_id)

    if payload is not None:
        packet += payload

    crc = calc_checksum(packet, len(packet))
    packet += struct.pack('<H', crc)
    s.write(packet)
    sequence_number += 1

# =======================================================================
# 조종간 입력값 변환 함수 (min 364, center 1024, max 1684) -> (min -32768, center 0, max 32767)
# =======================================================================
def parseInput(input_bytes, name):
    output = (int.from_bytes(input_bytes, byteorder='little') - 1024) * 2 * 4096 // 165
    if output >= 32768:
        output = 32767
    return output

# 전역 변수 st에 조종간 좌표값 저장 (오른쪽: "rh", "rv", 왼쪽: "lh", "lv")
st = {"rh": 0, "rv": 0, "lh": 0, "lv": 0}

# =======================================================================
# 수정된 입력 업데이트 스레드:
# - 키보드: 왼쪽 조종간이 임계치를 초과하면 0.1초마다 해당 방향의 키(w,a,s,d)를 눌렀다 떼는 이벤트 전송
# - 마우스: 오른쪽 조종간은 20ms 간격으로 부드럽게 이동
# =======================================================================
def input_update_thread():
    keyboard = KeyboardController()
    mouse = MouseController()
    
    deadzone_keyboard = 5000
    deadzone_mouse = 1000
    mouse_sensitivity = 0.0010  # 필요시 이 값을 조절하세요
    
    kbd_repeat_interval = 0.01  # 0.1초마다 키 이벤트 발생
    last_kbd_time = time.time()
    
    while True:
        current_time = time.time()
        # 키보드 업데이트: 0.1초 간격
        if current_time - last_kbd_time >= kbd_repeat_interval:
            last_kbd_time = current_time
            # 수직 방향: 위쪽(w) / 아래쪽(s)
            if st["lv"] > deadzone_keyboard:
                keyboard.press('w')
                keyboard.release('w')
            elif st["lv"] < -deadzone_keyboard:
                keyboard.press('s')
                keyboard.release('s')
            # 수평 방향: 오른쪽(d) / 왼쪽(a)
            if st["lh"] > deadzone_keyboard:
                keyboard.press('d')
                keyboard.release('d')
            elif st["lh"] < -deadzone_keyboard:
                keyboard.press('a')
                keyboard.release('a')
                
        # 마우스 업데이트: 20ms 간격 (부드러운 이동)
        move_x = 0
        move_y = 0
        if abs(st["rh"]) > deadzone_mouse:
            move_x = int(st["rh"] * mouse_sensitivity)
        if abs(st["rv"]) > deadzone_mouse:
            move_y = -int(st["rv"] * mouse_sensitivity)
        if move_x != 0 or move_y != 0:
            mouse.move(move_x, move_y)
        
        # 디버깅 출력 (원한다면 주석 처리 가능)
        print(f"[Input Thread] Parsed - RH: {st['rh']}, RV: {st['rv']}, LH: {st['lh']}, LV: {st['lv']}")
        
        time.sleep(0.02)  # 20ms (50Hz)로 업데이트

# 스레드 시작
thread = Thread(target=input_update_thread, args=())
thread.daemon = True
thread.start()

# =======================================================================
# 메인 루프: 시리얼 데이터 수신 및 조종간 값 파싱
# =======================================================================
try:
    # RC 시뮬레이터 모드 활성화
    send_duml(s, 0x0a, 0x06, 0x40, 0x06, 0x24, bytearray.fromhex('01'))
    
    while True:
        # 조종간 입력 요청
        send_duml(s, 0x0a, 0x06, 0x40, 0x06, 0x01, bytearray.fromhex(''))
        
        # 패킷 수신
        buffer = bytearray()
        while True:
            b = s.read(1)
            if b == bytearray.fromhex('55'):
                buffer.extend(b)
                ph = s.read(2)
                buffer.extend(ph)
                ph_val = struct.unpack('<H', ph)[0]
                pl = ph_val & 0x03FF  # 패킷 길이
                h_crc = s.read(1)     # 헤더 체크섬 (출력용은 아님)
                buffer.extend(h_crc)
                pd = s.read(pl - 4)
                buffer.extend(pd)
                break
            else:
                break

        data = buffer
        if data:
            hex_str = ' '.join(format(x, '02x') for x in data)
            print(f"[Serial Debug] Raw Data Packet: {hex_str}")

        if len(data) == 38:
            st["rh"] = parseInput(data[13:15], 'lv')
            st["rv"] = parseInput(data[16:18], 'lh')
            st["lv"] = parseInput(data[19:21], 'rv')
            st["lh"] = parseInput(data[22:24], 'rh')
            print(f"[Serial Debug] Parsed Joystick Values - RH: {st['rh']}, RV: {st['rv']}, LH: {st['lh']}, LV: {st['lv']}")
        else:
            if data:
                print(f"[Serial Debug] Received packet length: {len(data)} (expected 38)")
except serial.SerialException as e:
    print('\n\nCould not read/write:', e)
except KeyboardInterrupt:
    print('\n\nDetected keyboard interrupt.')

print('Stopping.')
