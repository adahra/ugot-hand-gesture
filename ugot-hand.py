from ugot import ugot
import cv2
import mediapipe as mp
import time
import math
import threading
import atexit

# pip install ugot opencv-python mediapipe protobuf==3.20.3
# =====================================
# ID SERVO
# Ganti di sini SAJA kalau ID servo berubah lagi —
# semua bagian kode lain otomatis ikut menyesuaikan.
# =====================================
SERVO_PAN_ID = 51    # kanan-kiri (dulu 51)
SERVO_TILT_ID = 52   # atas-bawah (dulu 52)
SERVO_EXTRA_ID = 53  # tangan kiri (dulu 53)

# =====================================
# INIT UGOT
# =====================================
got = ugot.UGOT()

try:
    got.initialize('192.168.1.2')
except Exception as e:
    print(f"❌ Gagal inisialisasi robot: {e}")
    exit(1)

# ponytail: got.open_camera() tidak dipanggil; kamera display pakai webcam laptop.

print("📷 Kamera laptop digunakan")

# =====================================
# RESET ARM
# =====================================
print("🔄 restore arm")

# got.mechanical_arms_restory()
# (fitur dinonaktifkan — tidak ada yang dijalankan)

# =====================================
# POSISI AWAL SERVO
# =====================================
servo51 = 90
servo52 = -110
servo53 = -44

print("🏠 posisi default")

got.turn_servo_angle(SERVO_PAN_ID, servo51, 1000, True)
got.turn_servo_angle(SERVO_TILT_ID, servo52, 1000, True)
got.turn_servo_angle(SERVO_EXTRA_ID, servo53, 1000, True)

time.sleep(1)

# =====================================
# BUKA CAPIT
# =====================================
got.mechanical_clamp_release()

# =====================================
# BATAS SERVO
# =====================================
SERVO51_MIN = 40
SERVO51_MAX = 140

SERVO52_MIN = -140
SERVO52_MAX = -60

# servo 53 lebih bebas
SERVO53_MIN = -170
SERVO53_MAX = 40

# =====================================
# KAMERA LAPTOP
# =====================================
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# =====================================
# MEDIAPIPE
# =====================================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# =====================================
# STATUS CAPIT
# =====================================
clamp_closed = False

# =====================================
# ASYNC ROBOT COMMAND SENDER
# PENTING: SDK UGOT kemungkinan besar TIDAK thread-safe.
# Kalau dua thread berbeda memanggil got.xxx() bersamaan
# (misal servo_worker + clamp thread terpisah), response
# dari robot bisa saling tertukar dan bikin komunikasi
# "macet" tanpa error yang jelas — servo terlihat mati
# padahal sebenarnya socket-nya kacau.
#
# Makanya di versi ini SEMUA command (servo & clamp)
# dikirim lewat SATU thread saja secara berurutan, supaya
# tidak ada dua request yang tabrakan di socket yang sama.
# =====================================
robot_lock = threading.Lock()
target_servo = {SERVO_PAN_ID: None, SERVO_TILT_ID: None, SERVO_EXTRA_ID: None}
target_clamp = None  # None / "close" / "open"
stop_event = threading.Event()

# jeda minimum antar pengiriman command servo (detik)
# 0.08s = ~12x kirim per detik, cukup halus utk mata
# tapi tidak membanjiri robot dgn command
SERVO_SEND_INTERVAL = 0.08


def robot_worker():
    """Satu-satunya thread yang boleh bicara ke robot.
    Servo & clamp diproses berurutan di sini, tidak pernah
    dari thread lain, supaya socket tidak kacau."""
    last_sent = {SERVO_PAN_ID: None, SERVO_TILT_ID: None, SERVO_EXTRA_ID: None}
    last_clamp_sent = None

    while not stop_event.is_set():
        with robot_lock:
            servo_snapshot = dict(target_servo)
            clamp_snapshot = target_clamp

        # ---- kirim clamp dulu (prioritas, jarang berubah) ----
        if clamp_snapshot is not None and clamp_snapshot != last_clamp_sent:
            try:
                if clamp_snapshot == "close":
                    got.mechanical_clamp_close()
                    print("🤏 tutup capit (terkirim)")
                elif clamp_snapshot == "open":
                    got.mechanical_clamp_release()
                    print("🖐️ buka capit (terkirim)")
                last_clamp_sent = clamp_snapshot
            except Exception as e:
                print(f"⚠️ gagal kirim clamp: {e}")

        # ---- baru kirim servo ----
        for servo_id, angle in servo_snapshot.items():
            if angle is None:
                continue
            if last_sent[servo_id] != angle:
                try:
                    got.turn_servo_angle(
                        servo_id,
                        angle,
                        25,
                        False
                    )
                    last_sent[servo_id] = angle
                except Exception as e:
                    print(f"⚠️ gagal kirim servo {servo_id}: {e}")

        stop_event.wait(SERVO_SEND_INTERVAL)


robot_thread = threading.Thread(target=robot_worker, daemon=True)
robot_thread.start()

# =====================================
# SMOOTH FILTER (posisi tracking tangan kanan)
# =====================================
smooth_x = 320
smooth_y = 240

alpha = 0.7

smooth_left_x = 320
smooth_left_y = 240
left_alpha = 0.7

# =====================================
# SMOOTH FILTER UNTUK PINCH RATIO
# (biar rasio cubit juga tidak jitter)
# =====================================
smooth_pinch_ratio = 1.0
pinch_alpha = 0.5

# =====================================
# THRESHOLD PINCH (RELATIF, BUKAN PIXEL TETAP)
# pinch_ratio = jarak(jempol,telunjuk) / ukuran_telapak_tangan
# Nilai ini TIDAK terpengaruh jarak tangan ke kamera
# =====================================
PINCH_CLOSE_RATIO = 0.35   # di bawah ini -> dianggap mencubit -> tutup capit
PINCH_OPEN_RATIO = 0.55    # di atas ini -> dianggap lepas cubit -> buka capit
# (ada gap antara 0.35 - 0.55 = hysteresis, mencegah toggle flip-flop)

# =====================================
# DEBOUNCE FRAME COUNTER
# capit hanya berubah status kalau kondisi
# bertahan beberapa frame berturut-turut
# =====================================
PINCH_CONFIRM_FRAMES = 4
pinch_close_counter = 0
pinch_open_counter = 0

print("🤖 DUAL HAND CONTROL READY")
print(f"👉 Tangan kanan = gerakkan servo {SERVO_PAN_ID} & {SERVO_TILT_ID}")
print(f"👈 Tangan kiri = gerakkan servo {SERVO_EXTRA_ID}")
print("👌 Cubit tangan kanan = capit")

# =====================================
# LOOP
# =====================================
while True:

    ret, img = cap.read()

    if not ret:
        continue

    # mirror natural
    img = cv2.flip(img, 1)

    if img.shape[1] != 640 or img.shape[0] != 480:
        img = cv2.resize(img, (640, 480))

    rgb = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2RGB
    )

    # =====================================
    # DETEKSI TANGAN
    # =====================================
    rgb.flags.writeable = False
    results = hands.process(rgb)
    rgb.flags.writeable = True

    h, w = img.shape[:2]

    center_x = w // 2
    center_y = h // 2

    # titik tengah layar
    cv2.circle(
        img,
        (center_x, center_y),
        5,
        (255, 255, 255),
        -1
    )

    text = "NORMAL"

    # kalau di frame ini tidak ada tangan kanan sama sekali,
    # jangan biarkan counter nyangkut dari frame sebelumnya
    right_hand_detected = False
    left_hand_detected = False

    # =====================================
    # ADA TANGAN
    # =====================================
    if results.multi_hand_landmarks and results.multi_handedness:

        for handLms, handedness in zip(
            results.multi_hand_landmarks,
            results.multi_handedness
        ):

            label = handedness.classification[0].label

            # =====================================
            # DRAW HAND
            # =====================================
            mp_draw.draw_landmarks(
                img,
                handLms,
                mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(
                    color=(0, 255, 0),
                    thickness=2,
                    circle_radius=3
                ),
                mp_draw.DrawingSpec(
                    color=(255, 0, 255),
                    thickness=2
                )
            )

            # =====================================
            # TITIK JARI
            # =====================================
            thumb_tip = handLms.landmark[4]
            index_tip = handLms.landmark[8]

            tx = int(thumb_tip.x * w)
            ty = int(thumb_tip.y * h)

            ix = int(index_tip.x * w)
            iy = int(index_tip.y * h)

            # =====================================
            # TANGAN KANAN
            # GERAKKAN SERVO 51 & 52
            # =====================================
            if label == "Right" and not right_hand_detected:

                right_hand_detected = True

                # =====================================
                # JARAK CUBIT (RAW, DALAM PIXEL)
                # =====================================
                pinch_distance = math.hypot(
                    tx - ix,
                    ty - iy
                )

                # =====================================
                # UKURAN TANGAN (REFERENSI SKALA)
                # pakai jarak wrist(0) -> pangkal jari tengah(9)
                # supaya tidak berubah walau jari dibuka/ditutup
                # =====================================
                wrist = handLms.landmark[0]
                middle_mcp = handLms.landmark[9]

                wx, wy = wrist.x * w, wrist.y * h
                mx, my = middle_mcp.x * w, middle_mcp.y * h

                hand_size = math.hypot(mx - wx, my - wy)

                # jaga-jaga supaya tidak dibagi nol
                if hand_size < 1:
                    hand_size = 1

                # =====================================
                # PINCH RATIO (SUDAH TERNORMALISASI)
                # tidak lagi tergantung jarak tangan ke kamera
                # =====================================
                raw_pinch_ratio = pinch_distance / hand_size

                # smooth pinch ratio (redam jitter)
                # gunakan round bukan int() agar tidak truncate ke bawah
                smooth_pinch_ratio = round(
                    (pinch_alpha * raw_pinch_ratio +
                     (1 - pinch_alpha) * smooth_pinch_ratio),
                    3
                )

                cx = int((tx + ix) / 2)
                cy = int((ty + iy) / 2)

                # smooth tracking posisi
                smooth_x = int(
                    alpha * cx +
                    (1 - alpha) * smooth_x
                )

                smooth_y = int(
                    alpha * cy +
                    (1 - alpha) * smooth_y
                )

                # =====================================
                # BOLA MERAH
                # =====================================
                cv2.circle(
                    img,
                    (smooth_x, smooth_y),
                    14,
                    (0, 0, 255),
                    -1
                )

                cv2.putText(
                    img,
                    "TRACK",
                    (smooth_x - 20, smooth_y - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    2
                )

                # garis tracking
                cv2.line(
                    img,
                    (center_x, center_y),
                    (smooth_x, smooth_y),
                    (255, 0, 0),
                    2
                )

                # =====================================
                # ERROR
                # =====================================
                error_x = smooth_x - center_x
                error_y = smooth_y - center_y

                # =====================================
                # SERVO 51
                # KANAN KIRI
                # =====================================
                if abs(error_x) > 10:

                    # ponytail: step integer linier, ganti PID controller jika butuh respon kurva halus
                    servo51 += int(error_x * 0.04) or (1 if error_x > 0 else -1)

                    servo51 = max(
                        SERVO51_MIN,
                        min(SERVO51_MAX, servo51)
                    )

                    # tidak lagi kirim langsung ke robot di sini.
                    # cukup update target, robot_worker thread
                    # yang akan mengirimnya secara throttled &
                    # berurutan (satu-satunya thread yg boleh
                    # bicara ke robot).
                    with robot_lock:
                        target_servo[SERVO_PAN_ID] = servo51

                # =====================================
                # SERVO 52
                # ATAS BAWAH
                # =====================================
                if abs(error_y) > 10:

                    # ponytail: step integer linier, ganti PID controller jika butuh respon kurva halus
                    servo52 += int(error_y * 0.04) or (1 if error_y > 0 else -1)

                    servo52 = max(
                        SERVO52_MIN,
                        min(SERVO52_MAX, servo52)
                    )

                    with robot_lock:
                        target_servo[SERVO_TILT_ID] = servo52

                # =====================================
                # CUBIT TANGAN KANAN
                # pakai ratio ternormalisasi + hysteresis + debounce
                # =====================================
                if smooth_pinch_ratio < PINCH_CLOSE_RATIO:
                    pinch_close_counter += 1
                    pinch_open_counter = 0
                elif smooth_pinch_ratio > PINCH_OPEN_RATIO:
                    pinch_open_counter += 1
                    pinch_close_counter = 0
                else:
                    # di zona abu-abu (antara close & open ratio)
                    # tidak menambah counter mana pun -> status tetap
                    pinch_close_counter = 0
                    pinch_open_counter = 0

                if pinch_close_counter >= PINCH_CONFIRM_FRAMES:
                    text = "TUTUP CAPIT"

                    if not clamp_closed:
                        print("🤏 tutup capit (diminta)")
                        with robot_lock:
                            target_clamp = "close"
                        clamp_closed = True
                        # reset counter agar debounce berjalan lagi
                        # untuk aksi berikutnya
                        pinch_close_counter = 0

                elif pinch_open_counter >= PINCH_CONFIRM_FRAMES:
                    text = "BUKA CAPIT"

                    if clamp_closed:
                        print("🖐️ buka capit (diminta)")
                        with robot_lock:
                            target_clamp = "open"
                        clamp_closed = False
                        # reset counter agar debounce berjalan lagi
                        # untuk aksi berikutnya
                        pinch_open_counter = 0

                cv2.putText(
                    img,
                    f"RATIO:{smooth_pinch_ratio:.2f}",
                    (10, 210),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )

            # =====================================
            # TANGAN KIRI
            # CONTROL SERVO 53
            # =====================================
            elif label == "Left" and not left_hand_detected:

                left_hand_detected = True

                # titik tangan kiri
                left_cx = int((tx + ix) / 2)
                left_cy = int((ty + iy) / 2)

                # smooth posisi tangan kiri (EMA, sama seperti servo51/52)
                smooth_left_x = int(
                    left_alpha * left_cx +
                    (1 - left_alpha) * smooth_left_x
                )
                smooth_left_y = int(
                    left_alpha * left_cy +
                    (1 - left_alpha) * smooth_left_y
                )

                # =====================================
                # BOLA BIRU
                # =====================================
                cv2.circle(
                    img,
                    (smooth_left_x, smooth_left_y),
                    14,
                    (255, 0, 0),
                    -1
                )

                cv2.putText(
                    img,
                    "SERVO53",
                    (smooth_left_x - 35, smooth_left_y - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 0, 0),
                    2
                )

                # garis visual
                cv2.line(
                    img,
                    (center_x, center_y),
                    (smooth_left_x, smooth_left_y),
                    (255, 0, 0),
                    2
                )

                # =====================================
                # TRACKING SERVO53
                # MODEL TALI KARET
                # =====================================
                error_left_y = smooth_left_y - center_y

                servo53 = int(
                    -44 + (error_left_y * 0.25)
                )

                # limit servo
                servo53 = max(
                    SERVO53_MIN,
                    min(SERVO53_MAX, servo53)
                )

                # update target, dikirim oleh robot_worker thread
                with robot_lock:
                    target_servo[SERVO_EXTRA_ID] = servo53

    # kalau tangan kanan hilang dari frame, reset counter
    # supaya tidak "nyangkut" separuh jalan
    if not right_hand_detected:
        pinch_close_counter = 0
        pinch_open_counter = 0

    # =====================================
    # INFO
    # =====================================
    cv2.putText(
        img,
        text,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.putText(
        img,
        f"S{SERVO_PAN_ID}:{servo51}",
        (10, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.putText(
        img,
        f"S{SERVO_TILT_ID}:{servo52}",
        (10, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.putText(
        img,
        f"S{SERVO_EXTRA_ID}:{servo53}",
        (10, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    # =====================================
    # DISPLAY
    # =====================================
    cv2.imshow(
        "UGOT DUAL HAND CONTROL",
        img
    )

    # ESC keluar
    key = cv2.waitKey(1)

    if key == 27:
        break

# =====================================
# CLEANUP
# =====================================
_cleaned_up = False

def cleanup():
    global _cleaned_up
    if _cleaned_up:
        return
    _cleaned_up = True
    stop_event.set()
    robot_thread.join(timeout=1)
    if cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()
    print("Program selesai")

atexit.register(cleanup)
cleanup()