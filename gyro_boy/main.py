#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor
from pybricks.parameters import Port
import socket
import time

# 1. 初始化 EV3 與馬達
ev3 = EV3Brick()
left_motor = Motor(Port.A)
right_motor = Motor(Port.D)

# 2. 設定socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('', 5000))
server_socket.listen(1)


try:
    # 3. 等待電腦連線
    ev3.speaker.beep()
    print("等待電腦藍牙連線...")
    conn, addr = server_socket.accept()

    ev3.speaker.beep()
    print(f"已連線 {addr} , 開始接收指令。")

    # 4. 主控制迴圈
    while True:
        try:
            cmd = conn.recv(1024).decode()
            if not cmd:
                break
            
            if cmd == 'F':    # 前進
                left_motor.run(300)
                right_motor.run(300)
                pass
            elif cmd == 'B':  # 後退
                left_motor.run(-300)
                right_motor.run(-300)
                pass
            elif cmd == 'R':  # 後退
                left_motor.run(300)
                right_motor.run(-300)
                pass
            elif cmd == 'L':  # 後退
                left_motor.run(-300)
                right_motor.run(300)
                pass
            elif cmd == 'S':  # 停止
                left_motor.stop()
                right_motor.stop()
                pass
                
            time.sleep(0.05)
        except ConnectionResetError:
            print("Connection Reset")
            break
        except Exception as e:
            print(f"Unexpect Error: {e}")
            break
except Exception as e:
    print(f"Server Operation Failed: {e}")

finally:
    print("Connection lost, Stoping Motors...")
    left_motor.stop()
    right_motor.stop()
    if 'conn' in locals():
        conn.close()
    server_socket.close()
