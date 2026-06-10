#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, GyroSensor
from pybricks.parameters import Port
from pybricks.tools import wait, StopWatch
import socket

# 1. 初始化 EV3 硬體
ev3 = EV3Brick()
left_motor = Motor(Port.A)
right_motor = Motor(Port.D)
gyro_sensor = GyroSensor(Port.S2)

# 初始化計時器
loop_timer = StopWatch()
fall_timer = StopWatch()

# 2. 設定 Socket 伺服器
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', 5000))
server_socket.listen(1)

print("Waiting for Connection...")
conn, addr = server_socket.accept()
conn.setblocking(False)  # 設為非阻塞，防止 recv 卡住自平衡
print("Connected to {}".format(addr))

# 3. 陀螺儀校準 (保持機器人靜止)
print("Calibrating Gyro... Please keep robot still.")
while True:
    gyro_minimum_rate = 440
    gyro_maximum_rate = -440
    gyro_sum = 0
    
    for _ in range(200):
        gyro_sensor_value = gyro_sensor.speed()
        gyro_sum += gyro_sensor_value
        if gyro_sensor_value > gyro_maximum_rate:
            gyro_maximum_rate = gyro_sensor_value
        if gyro_sensor_value < gyro_minimum_rate:
            gyro_minimum_rate = gyro_sensor_value
        wait(5)
        
    if gyro_maximum_rate - gyro_minimum_rate < 2:
        break

gyro_offset = gyro_sum / 200
print("Gyro Calibrated Successfully! Offset: {}".format(gyro_offset))

# 4. 獨立變數初始化
robot_body_angle = 0
motor_position_sum = 0
wheel_angle = 0
drive_speed = 0
steering = 0
motor_position_change = [0, 0, 0, 0]

print("Start Balancing Control Loop...")

# 5. 主控制迴圈
try:
    while True:
        loop_timer.reset()

        # 【A】讀取並解析單字元指令
        try:
            cmd = conn.recv(1024).decode().strip()
            if cmd:
                print("Received Command: {}".format(cmd))
                if cmd == 'F':
                    drive_speed = 120
                    steering = 0
                elif cmd == 'B':
                    drive_speed = -120
                    steering = 0
                elif cmd == 'L':
                    drive_speed = 0
                    steering = -25
                elif cmd == 'R':
                    drive_speed = 0
                    steering = 25
                elif cmd == 'S':
                    drive_speed = 0
                    steering = 0
        except socket.error:
            # 沒有收到新指令時，直接略過維持前一次的動作
            pass

        # 【B】自平衡演算法 (控制週期固定為 0.01 秒)
        gyro_sensor_value = gyro_sensor.speed()
        gyro_offset = (gyro_offset * 0.9995) + (0.0005 * gyro_sensor_value)
        robot_body_rate = gyro_sensor_value - gyro_offset
        robot_body_angle += robot_body_rate * 0.01

        previous_motor_sum = motor_position_sum
        motor_position_sum = left_motor.angle() + right_motor.angle()
        change = motor_position_sum - previous_motor_sum
        
        motor_position_change.insert(0, change)
        del motor_position_change[-1]
        
        # 💡 注意：原地旋轉時由於兩輪反轉，車輪轉速總和(wheel_rate)變化不大，有助於維持平衡
        wheel_angle += change - drive_speed * 0.01
        wheel_rate = sum(motor_position_change) / 0.04

        # PID 控制輸出功率計算
        output_power = (-0.01 * drive_speed) + (0.8 * robot_body_rate + 15 * robot_body_angle + 0.08 * wheel_rate + 0.12 * wheel_angle)
        
        # 限制功率在 -100 ~ 100 之間
        if output_power > 100:
            output_power = 100
        if output_power < -100:
            output_power = -100

        # 驅動馬達 (直接套用修正後的原地旋轉驅動邏輯)
        left_motor.dc(output_power - steering)
        right_motor.dc(output_power + steering)

        # 跌倒偵測
        if abs(output_power) < 100:
            fall_timer.reset()
        elif fall_timer.time() > 1000:
            print("Robot fell down!")
            break

        # 確保整個大迴圈剛好固定在 10ms 週期
        wait_time = 10 - loop_timer.time()
        if wait_time > 0:
            wait(wait_time)

except Exception as e:
    print("Unexpected Error: {}".format(e))

finally:
    print("Stopping Motors and Closing Connection...")
    left_motor.stop()
    right_motor.stop()
    conn.close()
    server_socket.close()