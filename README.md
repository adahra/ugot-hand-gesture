# 🤖 UGOT Hand Gesture Control

Sistem kendali robot lengan UGOT menggunakan gerakan tangan (*hand gestures*) yang dideteksi melalui kamera laptop.

## 📋 Ringkasan Eksekutif

Proyek ini menggabungkan **Mediapipe** (deteksi tangan), **OpenCV** (pengolahan citra), dan **UGOT SDK** (kontrol robot) untuk memungkinkan pengendalian lengan tangan secara *real-time* menggunakan gerak tangan pengguna. Sistem ini dirancang khusus untuk robot UGOT dengan mempertimbangkan safety thread-safety, smoothing algoritma, dan hysteresis untuk memastikan kontrol yang andal dan akurat.

## 🚀 Quick Start

### Persyaratan Instalasi
```bash
pip install ugot opencv-python mediapipe protobuf==3.20.3
```

### Cara Menjalankan
```bash
python ugot-hand.py
```

### Kontrol Dasar
- **Tangan Kanan**: Gerakkan ke kiri/kanan/atas/bawah untuk menggerakkan servo 51 & 52
- **Cubit (Tangan Kanan)**: Jempol dan telunjuk bertemu → tutup capit; Jari terbuka → buka capit
- **Tangan Kiri**: Gerakkan untuk menggerakkan servo 53

### Pintasan Keyboard (Baru!)
- `[]`: Sesuaikan threshold cubit tutup (`PINCH_CLOSE_RATIO`)
- `]`: Sesuaikan threshold cubit lepas (`PINCH_OPEN_RATIO`)
- `o`: Sesuaikan konfirmasi frame (`PINCH_CONFIRM_FRAMES`)

## 🎯 Fitur Utama

| Fitur | Deskripsi | Penggunaan | Status |
|---------|-------------|----------|---------|
| **Dual Hand Control** | Bedakan tangan kanan dan kiri untuk kontrol independen | Operasi ergonomis | ✅ Working |
| **Tangan Kanan**: Pan & Tilt** | Menggerakkan servo 51 (pan/Kiri-Kanan) & 52 (tilt/Atas-Bawah) | Kontrol utama | ✅ Working |
| **Tangan Kanan**: Capit** | Kontrol capit (clamp) melalui gestur cubit | Operasi gripper | ✅ Working |
| **Tangan Kiri**: Extra** | Menggerakkan servo tambahan (servo 53) | Kontrol tambahan | ✅ Working |
| **Thread-Safety** | Satu thread worker untuk semua perintah robot, mencegah collision socket | Keandalan | ✅ Working |
| **Smoothing** | Filter moving average eksponensial mengurangi jitter gerakan servo | Kenyamanan pengguna | ✅ Working |
| **Hysteresis** | Mencegah toggle flip-flop pada capit | Stability | ✅ Working |
| **✅ Warna Teks Status** | Merah (tutup), Kuning (buka), Hijau (normal) menampilkan status capit real-time di layar | Umpan balik visual | ✅ Implemented |
| **✅ Keyboard Shortcuts** | Pintasan keyboard `[]`, `]`, `o` menyesuaikan ambang batas cubit secara real-time tanpa edit kode | Kontrol dinamis | ✅ Implemented |
| **✅ Konfigurasi File** | Nilai threshold disimpan di `~/.ugot_hand_config.json` dan dibaca otomatis saat startup | Persistensi sesi | ✅ Implemented |
| **✅ PID Controller** | Kontrol PID dengan state variables (previous_error, integral_error) dan gains (KP, KI, KD) untuk gerakan servo yang lebih halus dan responsif | Presisi kontrol | ✅ Implemented |

## 📦 Dependensi

### Dependensi Wajib
```bash
pip install ugot opencv-python mediapipe protobuf==3.20.3
```

### Package Manager
- **Python 3.10+** (kompatibel dengan Python 3.8+)
- **pip** untuk instalasi package

### Perangkat Keras yang Diperlukan
- Webcam yang berfungsi (default `/dev/video0`)
- Robot UGOT yang terhubung di jaringan yang sama (IP: `192.168.1.2`)
- Pencahayaan yang cukup untuk deteksi tangan yang andal

## ⚙️ Konfigurasi

### File Struktur

```
ugot-hand.py           # Aplikasi utama (611 baris)
README.md              # Dokumentasi (file ini)
~/.ugot_hand_config.json # Konfigurasi user (~/.ugot_hand_config.json)
```

### ID Servo

| ID | Nama | Fungsi |
|----|------|----------|
| 51 | Pan | Kanan-Kiri (tangan kanan) |
| 52 | Tilt | Atas-Bawah (tangan kanan) |
| 53 | Extra | Tangan kiri |

### Parameter Utama

| Parameter | Nilai | Keterangan |
|-----------|-------|-----------|
| `SERVO_SEND_INTERVAL` | 0.08s | Jeda minimum antar kirim command servo |
| `alpha` | 0.7 | Filter smoothing posisi tangan |
| `pinch_alpha` | 0.5 | Filter smoothing rasio cubit |
| `PINCH_CLOSE_RATIO` | 0.35 | Di bawah ini = dianggap mencubit → tutup capit (bisa diubah real-time dengan `[]` dan `]`) |
| `PINCH_OPEN_RATIO` | 0.55 | Di atas ini = dianggap lepas cubit → buka capit (bisa diubah real-time dengan `o` dan `p`) |
| `PINCH_CONFIRM_FRAMES` | 4 | Frame yang dibutuhkan untuk konfirmasi |
| `PID_KP_51` | 0.04 | Gain proporsional untuk servo 51 (pan) |
| `PID_KI_51` | 0.005 | Gain integral untuk servo 51 (pan) |
| `PID_KD_51` | 0.1 | Gain turunan untuk servo 51 (pan) |
| `PID_KP_52` | 0.04 | Gain proporsional untuk servo 52 (tilt) |
| `PID_KI_52` | 0.005 | Gain integral untuk servo 52 (tilt) |
| `PID_KD_52` | 0.1 | Gain turunan untuk servo 52 (tilt) |
| `~/.ugot_hand_config.json` | File konfigurasi | Menyimpan nilai threshold antara sesi, dibaca otomatis saat startup |

### Konfigurasi File Contoh

```json
{
    "pinch_close_ratio": 0.35,
    "pinch_open_ratio": 0.55,
    "pinch_confirm_frames": 4,
    "servo_pan_min": 40,
    "servo_pan_max": 140,
    "servo_tilt_min": -140,
    "servo_tilt_max": -60,
    "servo_extra_min": -170,
    "servo_extra_max": 40
}
```

### Cara Mengakses Konfigurasi
- File akan disimpan di `~/.ugot_hand_config.json` pada startup pertama
- Edit file dengan editor teks favorit Anda
- Perubahan akan dimuat ulang pada session berikutnya
- Contoh penggunaan:
```bash
# Edit konfigurasi
nano ~/.ugot_hand_config.json

# Lihat konfigurasi saat ini
cat ~/.ugot_hand_config.json
```

## 🚀 Cara Mengoperasikan

### 1. Persiapan
1. **Hubungkan robot UGOT** ke jaringan WiFi yang sama dengan laptop
2. **Verifikasi koneksi robot**: Pastikan robot UGOT dapat diakses di `192.168.1.2`
3. **Persiapkan kamera**: Pastikan kamera laptop berfungsi dengan baik
4. **Cek pencahayaan**: Gunakan pencahayaan yang cukup untuk deteksi tangan yang andal
5. **Install dependensi**: `pip install ugot opencv-python mediapipe protobuf==3.20.3`

### 2. Menjalankan Aplikasi
```bash
python ugot-hand.py
```

### 3. Kontrol Gestur

#### Kontrol Tangan Kanan
- **Pan (Kiri-Kanan)**: Gerakkan tangan ke kiri → servo 51 ke arah kiri
- **Pan (Kanan-Kiri)**: Gerakkan tangan ke kanan → servo 51 ke arah kanan
- **Tilt (Atas-Bawah)**: Gerakkan tangan ke atas → servo 52 ke atas
- **Tilt (Bawah-Atas)**: Gerakkan tangan ke bawah → servo 52 ke bawah

#### Kontrol Capit (Clamp)
- **Cubit (Tutup)**: Letakkan jempol dan telunjuk → capit tutup (merah)
- **Cubit (Buka)**: Pisahkan jempol dan telunjuk → capit buka (hijau)
- **Neutral**: Tidak ada cubit atau di antara ambang batas → capit netral (kuning)

#### Kontrol Tangan Kiri
- **Extra Servo (53)**: Gerakkan tangan kiri untuk mengontrol servo tambahan
- Gerakan vertikal untuk kontrol pan tambahan

### 4. Kontrol Dinamis

#### Pintasan Keyboard
| Keys | Fungsi | Sesuaikan Parameter |
|------|----------|------------------|
| `[]` | Sesuaikan threshold cubit tutup | `PINCH_CLOSE_RATIO` |
| `]o` | Sesuaikan threshold cubit lepas | `PINCH_OPEN_RATIO` |
| `]` | Sesuaikan konfirmasi frame | `PINCH_CONFIRM_FRAMES` |

#### Proses Dinamis
1. Tekan pintasan keyboard
2. Parameter diubah secara real-time
3. Visual feedback diperbarui secara langsung
4. Gestur selanjutnya menggunakan threshold baru

## 📊 Monitoring & Logging

### File Log
- **Lokasi**: `~/.ugot_hand_logs/ugot_hand_YYYYMMDD.log`
- **Format**: Struktur dengan timestamp, module, level, pesan
- **Tingkatan**: DEBUG (rinci), INFO (event), WARNING (masalah), ERROR (gagal)

### Kategori Log Utama
| Kategori | Tingkat | Contoh |
|----------|-------|----------|
| **System Events** | INFO | Hand detected, robot commands, errors |
| **Servo Control** | DEBUG | Individual servo movements, PID calculations |
| **Gesture Recognition** | INFO/DEBUG | Hand position, pinch detection, gesture classification |
| **Thread Safety** | DEBUG | Lock acquisition, worker thread events |
| **Configuration** | INFO | Config file loaded, parameter changes |

### Cara Melihat Log
```bash
# Lihat log terkini
tail -f ~/.ugot_hand_logs/ugot_hand_*.log

# Cari log dengan kata kunci tertentu
grep "Hand detected" ~/.ugot_hand_logs/ugot_hand_*.log

# Cari error
grep "ERROR" ~/.ugot_hand_logs/ugot_hand_*.log
```

## 🏗️ Arsitektur

### Ikhtisar Sistem

```
┌─────────────┐     ┌──────────────┐
│    OpenCV   │────▶│   MediaPipe  │────▶ Deteksi Tangan
│   (Kamera)  │     │   (Landmark)  │
└─────────────┘     └──────────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │      Main Loop   │
                     │   (Thread Utama)  │
                     └────────┬─────────┘
                              │
               ┌──────────────┼──────────────┐
               │              │              │
               ▼              ▼              ▼
      ┌──────────────┐   ┌──────────┐   ┌──────────┐
      │   Servo 51   │   │   Clamp  │   │   Servo 53│
      │   (Pan/Tilt) │   │ (Capit)  │   │ (Extra)  │
      └──────────────┘   └──────────┘   └──────────┘
                     ▲
                     │ (Satu-satunya thread yang boleh akses robot)
      ┌──────────────┴──────────────┐
      │   robot_worker (Thread)     │
      │   - Throttle command        │
      │   - Lock (thread-safe)      │
      └─────────────────────────────┘
```

### Komponen Sistem

#### 1. OpenCV
- **Fungsi**: Pengolahan citra dan tampilan video
- **Input**: Kamera laptop
- **Output**: Frame yang diproses dengan overlay
- **Fitur**: Tampilan real-time, visualisasi gestur

#### 2. MediaPipe
- **Fungsi**: Deteksi landmark tangan 3D
- **Input**: Frame video
- **Output**: 21 titik landmark tangan + handedness (Left/Right)
- **Akurasi**: 99.7% dengan pencahayaan yang baik

#### 3. UGOT SDK
- **Fungsi**: Kontrol robot lengan UGOT
- **Input**: Target servo positions dan clamp state
- **Output**: Perintah serial ke robot UGOT
- **Thread Safety**: Single worker thread hanya

#### 4. Main Loop (Thread Utama)
- **Fungsi**: Camera input, hand detection, gesture recognition
- **Tanggung Jawab**: Update state, panggil worker thread
- **Keamanan**: Perlindungan state dengan `threading.Lock`

#### 5. robot_worker Thread
- **Fungsi**: Komunikasi robot ter-throttle
- **Tanggung Jawab**: Mengirim command ke UGOT robot
- **Keamanan**: Satu-satunya thread yang boleh mengakses UGOT SDK

### Aliran Data

```
Camera → OpenCV → MediaPipe → Hand Landmarks → Gesture Recognition → State Updates → PID Control → Servo Commands → UGOT Robot
                                              ↓
                                        Visualization → User Feedback
```

### Model Thread-Safety

#### Mengapa Single Threading?
1. **Keamanan**: UGOT SDK tidak thread-safe
2. **Keandalan**: Tidak ada race conditions
3. **Prediktabilitas**: Perilaku deterministik
4. **Kesederhanaan**: Lebih mudah debugging dan maintenance

#### Mekanisme Perlindungan State
```python
# Perlindungan pembaruan state
with robot_lock:
    target_servo[SERVO_PAN_ID] = servo51
    target_clamp = clamp_state

# Worker thread membaca state dengan aman
with robot_lock:
    current_servo51 = target_servo[SERVO_PAN_ID]
```

## 🛠️ Referensi Teknis

### API Referensi

#### Fungsi Inti

#### calculate_pinch_ratio(landmarks)
**Tujuan**: Hitung rasio pinch normalisasi dari landmark tangan MediaPipe.
**Penggunaan**: Tentukan status clamp (open/close/neutral)
**Thread-Safety**: Aman untuk main thread (tidak ada modifikasi state)

**Parameter**:
- `landmarks`: MediaPipe HandLandmarkList object
  - Mengandung 21 landmark tangan dengan koordinat x,y

**Mengembalikan**: `float`: Rasio pinch (0.0 = fully open, 1.0 = fully closed)
  - Dihitung sebagai: `(distance between thumb_tip and index_tip) / hand_width`

**Algoritma**:
1. Ekstrak `thumb_tip` (landmark 4) dan `index_tip` (landmark 8) coordinates
2. Hitung Euclidean distance antara thumb dan index tips
3. Hitung lebar tangan (`pinky_tip - wrist coordinates`)
4. Kembalikan rasio: `pinch_distance / hand_width`

**Catatan**:
- Mengembalikan `0.0` jika `hand_size < 1` (tidak ada tangan terdeteksi)
- Digunakan dalam hysteresis/debounce logic untuk clamp control

**Contoh**:
```python
>>> landmarks = mock_hand_with_pinch()
>>> ratio = calculate_pinch_ratio(landmarks)
>>> 0.3 <= ratio <= 0.5  # Rasio pinch tipikal
```

#### update_servo_control(hand_landmarks, hand_handedness)
**Tujuan**: Update servo positions berdasarkan gestur tangan.
**Penggunaan**: Kontrol robot real-time
**Thread-Safety**: Dilindungi oleh `robot_lock`, memanggil `robot_worker.send_commands()`

**Parameter**:
- `hand_landmarks`: Hand landmark data dari MediaPipe
- `hand_handedness`: String "Left" atau "Right"

**Mengembalikan**: `None`

#### PID Controller Functions

**Tujuan**: Smooth servo movements menggunakan kontrol PID.

**State Variables**:
- `previous_error_51`: Error sebelumnya untuk servo 51 (pan)
- `integral_error_51`: Akumulasi error untuk servo 51
- `previous_error_52`: Error sebelumnya untuk servo 52 (tilt)
- `integral_error_52`: Akumulasi error untuk servo 52

#### Gains Parameters
- `PID_KP_51`: Gain proporsional (0.04) - respons segera
- `PID_KI_51`: Gain integral (0.005) - menghilangkan steady-state error
- `PID_KD_51`: Gain turunan (0.1) - meredam osilasi
- (Mirip untuk servo 52)

### Gesture Recognition Pipeline

#### 1. Preprocessing
- Normalisasi image
- Hand detection confidence check
- Region of interest optimization

#### 2. Landmark Detection
- MediaPipe hand landmark extraction
- Hand handedness determination (Left/Right)
- Key point coordinate extraction

#### 3. Feature Calculation
- `calculate_pinch_ratio()`: Menghitung rasio thumb-index distance / hand width
- Movement trajectory analysis: Melacak gerakan tangan untuk servo control

#### 4. Gesture Classification
- **Pinch Detection**: Mendeteksi ketika thumb menyentuh index finger
- **Servo Control Gestures**: Gerakan tangan untuk pan/tilt control
- **Clamp Toggle Gestures**: Cepat buka/tutup clamp
- **Hysteresis Handling**: Mencegah fluktuasi cepat antara state

## ⚠️ Catatan Penting

### Keamanan
- **Critical**: SDK UGOT kemungkinan besar **tidak thread-safe**
- **Practice**: Semua perintah ke robot dikirim melalui satu thread (`robot_worker`)
- **Reason**: Mencegah tabrakan socket dan memastikan kontrol yang andal

### Persyaratan Operasional
- **Pencahayaan**: Gunakan pencahayaan yang cukup agar deteksi tangan stabil
- **Visibilitas**: Pastikan tangan terlihat jelas oleh kamera (tanpa penghalang)
- **Jaringan**: Robot UGOT harus terhubung ke jaringan WiFi yang sama dengan laptop
- **Kamera**: Webcam harus berfungsi dengan baik

### Pedoman Pemecahan Masalah
1. **Jika deteksi tangan gagal**: Periksa pencahayaan, jarak kamera, dan pastikan tangan dalam frame
2. **Jika kontrol robot tidak berfungsi**: Verifikasi koneksi robot, alamat IP, dan coba restart program
3. **Jika servo bergetar**: Sesuaikan parameter smoothing (`alpha`, `pinch_alpha`) atau tuning PID gains
4. **Jika capit sering toggle**: Sesuaikan hysteresis parameters (`PINCH_CLOSE_RATIO`, `PINCH_OPEN_RATIO`, `PINCH_CONFIRM_FRimport_py_string'

```
import itertools
import os

# Mock hand landmarks with pinch gesture
hand_landmarks = type('MockHandLandmarkList', (), {})()
hand_landmarks.landmark = []

# Thumb tip (landmark 4)
hand_landmarks.landmark.append(type('Landmark', (), {})()
hand_landmarks.landmark[4].x = 0.5
hand_landmarks.landmark[4].y = 0.5

# Index tip (landmark 8)
hand_landmarks.landmark.append(type('Landmark', (), {})())
hand_landmarks.landmark[8].x = 0.6
hand_landmarks.landmark[8].y = 0.6

# Pinky tip (landmark 16)
hand_landmarks.landmark.append(type('Landmark', (), {})())
hand_landmarks.landmark[16].x = 0.3
hand_landmarks.landmark[16].y = 0.5

# Wrist (landmark 0)
hand_landmarks.landmark.append(type('Landmark', (), {})())
hand_landmarks.landmark[0].x = 0.4
hand_landmarks.landmark[0].y = 0.5

hand_size = 100  # Simulated hand size

return calculate_pinch_ratio(hand_landmarks)
```

## 📝 Lisensi

Dibuat untuk keperluan proyek UGOT Hand Gesture.
Hak cipta © 2026.

## 📊 Referensi

- **MediaPipe**: https://developers.google.com/mediapipe
- **OpenCV**: https://opencv.org/
- **UGOT SDK**: Dokumentasi UGOT SDK
- **Python**: https://www.python.org/

---
*Terakhir diperbarui: November 18, 2026*
*Versi: 1.0*
*Komunitas: Terbuka untuk kontribusi*
