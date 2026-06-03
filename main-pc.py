import cv2
import mediapipe as mp
import math
from robot_controller import RobotController as rc

# ===== MediaPipe 方法設定 =====
mp_drawing = mp.solutions.drawing_utils              # MediaPipe 繪圖工具
mp_drawing_styles = mp.solutions.drawing_styles      # MediaPipe 繪圖樣式
mp_hands = mp.solutions.hands                        # MediaPipe 手掌偵測方法

# ===== 開啟攝影機 =====
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# ===== 設定 =====
WIDTH = 540              # 畫面寬度
HEIGHT = 320             # 畫面高度
fontFace = cv2.FONT_HERSHEY_SIMPLEX           # 設定文字字型
lineType = cv2.LINE_AA                        # 設定文字線條樣式

# ===== EV3 設定 =====
ROBOT_IP = '192.168.2.2'
robot = rc(ROBOT_IP)
robot.connect()

# ===== 計算手勢方向 =====
def hand_gesture(hand):
    dx = hand[8][0] - hand[5][0]
    dy = hand[8][1] - hand[5][1]

    angle = math.degrees(math.atan2(dy, dx))

    gesture = "UNKNOWN"
    if -135 <= angle < -45:
        gesture = "FOWARD"
    elif 45 <= angle < 135:
        gesture = "BACKWARD"
    elif -45 <= angle < 45:
        gesture = "RIGHT"
    elif angle >= 135 or angle < -135:
        gesture = "LEFT"

    return gesture

# ===== 啟用手掌偵測 =====
with mp_hands.Hands(
    model_complexity=0,                       # 模型複雜度，0 速度較快
    max_num_hands=1,                          # 最多偵測 1 隻手
    min_detection_confidence=0.6,             # 手掌偵測信心值
    min_tracking_confidence=0.6               # 手掌追蹤信心值
) as hands:
    try: 
        if not cap.isOpened():                    # 檢查攝影機是否開啟
            print("Cannot open camera")
            exit()

        while True:
            ret, img = cap.read()                 # 讀取攝影機畫面

            if not ret:                           # 若讀取失敗
                print("Cannot receive frame")
                break

            img = cv2.resize(img, (WIDTH, HEIGHT))            # 調整畫面尺寸
            img = cv2.flip(img, 1)                            # 左右鏡像翻轉
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)   # BGR 轉 RGB

            img_rgb.flags.writeable = False       # 提高處理速度
            results = hands.process(img_rgb)      # 執行手掌偵測
            img_rgb.flags.writeable = True        # 恢復可寫入狀態

            if results.multi_hand_landmarks:      # 如果有偵測到手掌
                for hand_landmarks in results.multi_hand_landmarks:

                    finger_points = []            # 儲存 21 個手部節點座標
                    fx = []                       # 儲存所有 x 座標
                    fy = []                       # 儲存所有 y 座標

                    for landmark in hand_landmarks.landmark:
                        x = int(landmark.x * WIDTH)           # 計算 x 座標
                        y = int(landmark.y * HEIGHT)          # 計算 y 座標
                        finger_points.append((x, y))          # 加入節點座標
                        fx.append(x)                          # 加入 x 座標
                        fy.append(y)                          # 加入 y 座標

                    gesture = hand_gesture(finger_points)# 偵測手勢方向

                    # 發送訊息到EV3
                    if gesture == "FOWARD":
                        robot.send_command('F')
                    elif gesture == "BACKWARD":
                        robot.send_command('B')
                    elif gesture == "RIGHT":
                        robot.send_command('R')
                    elif gesture == "LEFT":
                        robot.send_command('L')
                    else:
                        robot.send_command('S')

                    cv2.putText(
                        img,
                        gesture,
                        (30, 120),
                        fontFace,
                        5,
                        (255, 255, 255),
                        10,
                        lineType
                    )                                      # 顯示手勢文字

                    mp_drawing.draw_landmarks(
                        img,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS
                    )                                          # 繪製手掌骨架

            cv2.imshow('gesture sensor', img)   # 顯示結果畫面

            if cv2.waitKey(5) == ord('q'):
                break                            # 按下 q 離開程式
    finally:
        robot.close()
        cap.release()                                # 釋放攝影機資源
        cv2.destroyAllWindows()                      # 關閉所有視窗