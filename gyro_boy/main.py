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
gyro_sensor = GyroSensor(Port.S3)

# 初始化計時器
loop_timer = StopWatch()
fall_timer = StopWatch()
standby_timer = StopWatch()
print("Start Balancing Control Loop...")

# 2. 設定 Socket 伺服器
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', 5000))
server_socket.listen(1)

print("Waiting for Connection...")
conn, addr = server_socket.accept()
conn.setblocking(False)  # 設為非阻塞，防止 recv 卡住自平衡
print("Connected to", addr)

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
print("Gyro Calibrated Successfully! Offset:", gyro_offset)

# 4. 獨立變數初始化
robot_body_angle = 0
motor_position_sum = 0
wheel_angle = 0
drive_speed = 0
steering = 0
motor_position_change = [0, 0, 0, 0]
is_fallen = False

print("Start Balancing Control Loop...")

# 5. 主控制迴圈
try:
    while True:
        loop_timer.reset()

        # 【A】讀取並解析單字元指令
        try:
            cmd = conn.recv(1024).decode().strip()
            if cmd:
                print("Received Command:", cmd)
                if cmd == 'F':
                    drive_speed = 120
                    steering = 0
                elif cmd == 'B':
                    drive_speed = -120
                    steering = 0
                elif cmd == 'L':
                    drive_speed = 0
                    steering = -20
                elif cmd == 'R':
                    drive_speed = 0
                    steering = 20
                elif cmd == 'S':
                    drive_speed = 0
                    steering = 0
        except socket.error:
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
        
        wheel_angle += change - drive_speed * 0.01
        wheel_rate = sum(motor_position_change) / 0.04

        # PID 控制輸出功率計算
        output_power = (-0.01 * drive_speed) + (0.8 * robot_body_rate + 15 * robot_body_angle + 0.08 * wheel_rate + 0.12 * wheel_angle)
        
        # 限制功率在 -100 ~ 100 之間
        if output_power > 100:
            output_power = 100
        if output_power < -100:
            output_power = -100

        # --- 修正後的跌倒與扶正邏輯 ---

        # 1. 跌倒偵測：如果功率滿載(100)持續超過 1 秒，判定跌倒
        if abs(output_power) < 100:
            fall_timer.reset()
        elif fall_timer.time() > 1000:
            if not is_fallen:
                print("Robot fell down! Standing by...")
                is_fallen = True
                standby_timer.reset()  # 剛跌倒時，先重設扶正計時器

        # 2. 根據狀態控制馬達與進行復原
        if is_fallen:
            # 跌倒期間安全機制：馬達強制停止
            left_motor.stop()
            right_motor.stop()
            
            # 檢查車身是否處於接近垂直的狀態 (例如正負 5 度內)
            if abs(robot_body_angle) < 5:
                # 如果角度對了，但還沒滿 3 秒，就不斷檢查時間
                if standby_timer.time() > 3000:
                    print("Robot held stable for 3 seconds! Resuming balance...")
                    is_fallen = False
                    
                    # 【核心重設】重新將所有物理量歸零，準備完美重新啟動
                    robot_body_angle = 0  
                    left_motor.reset_angle(0)   # 直接重設馬達硬體編碼器
                    right_motor.reset_motor_angle = 0
                    motor_position_sum = 0
                    wheel_angle = 0
                    
                    fall_timer.reset()          # 重設跌倒計時器
            else:
                # 💡 關鍵：只要車身角度一偏離正負 5 度（代表還在晃、或還沒扶好）
                # 就一直重設計時器，逼它必須「重新累積」連續的 3 秒鐘！
                standby_timer.reset()
                
        else:
            # 只有在「沒跌倒」的正常狀態下，才允許輸出 PID 功率
            left_motor.dc(output_power - steering)
            right_motor.dc(output_power + steering)

        # 確保迴圈週期維持在 0.01 秒附近
        wait(10)

except Exception as e:
    print("Unexpected Error:", e)

finally:
    print("Stopping Motors and Closing Connection...")
    left_motor.stop()
    right_motor.stop()
    conn.close()
    server_socket.close()