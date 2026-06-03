import socket
import time

EV3_ADDR = '192.168.2.2'
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # 建立藍牙序列埠連線
    print(f"正在連線到 EV3 ({EV3_ADDR})...")
    client_socket.connect((EV3_ADDR, 5000))
    print("連線成功！輸入 w:前進, s:後退, x:停止, q:離開")
    
    while True:
        user_input = input("輸入指令: ").strip().lower()
        
        if user_input == 'w':
            client_socket.sendall(b'F')
            print("發送：前進 (F)")
        elif user_input == 's':
            client_socket.sendall(b'B')
            print("發送：後退 (B)")
        elif user_input == 'x':
            client_socket.sendall(b'S')
            print("發送：停止 (S)")
        elif user_input == 'q':
            client_socket.sendall(b'S')
            break
        else:
            client_socket.sendall(b'S')
            
except Exception as e:
    print(f"Connection Failed or Error: {e}")
finally:
    if 'ev3_serial' in locals() and client_socket.is_open:
        client_socket.sendall.close()
        print("藍牙連線已安全關閉。")