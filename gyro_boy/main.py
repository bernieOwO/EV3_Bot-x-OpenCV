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
    print("Waiting for Connection...")
    conn, addr = server_socket.accept()

    ev3.speaker.beep()
    print("Connected to", addr)

    # 4. 主控制迴圈
    while True:
        try:
            cmd = conn.recv(1024).decode()
            if not cmd:
                break
            
            if cmd == 'F':
                left_motor.run(300)
                right_motor.run(300)
            elif cmd == 'B':
                left_motor.run(-300)
                right_motor.run(-300)
            elif cmd == 'R':
                left_motor.run(-150)
                right_motor.run(150)
            elif cmd == 'L':
                left_motor.run(150)
                right_motor.run(-150)
            elif cmd == 'S':
                left_motor.stop()
                right_motor.stop()
                
            time.sleep(0.05)
        except ConnectionResetError:
            print("Connection Reset")
            break
        except Exception as e:
            print("Unexpected Error:", e)
            break
except Exception as e:
    print("Server Operation Failed:", e)

finally:
    print("Connection lost, Stopping Motors...")
    left_motor.stop()
    right_motor.stop()
    if 'conn' in locals():
        conn.close()
    server_socket.close()