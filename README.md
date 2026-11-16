# 🤖 UGOT Hand Gesture Control

Sistem kendali robot lengan UGOT menggunakan gerakan tangan (*hand gestures*) yang dideteksi melalui kamera laptop.

## 📋 Deskripsi

Proyek ini menggabungkan **Mediapipe** (deteksi tangan), **OpenCV** (pengolahan citra), dan **UGOT SDK** (kontrol robot) untuk memungkinkan pengendalian lengan tangan secara *real-time* menggunakan gerak tangan pengguna.

### 🎯 Fitur Utama
- **Dual Hand Control** — bedakan tangan kanan dan kiri
- **Tangan Kanan**: menggerakkan servo *pan* (kanan-kiri) & *tilt* (atas-bawah), sekaligus mengontrol capit (*clamp*) melalui gestur cubit
- **Tangan Kiri**: menggerakkan servo tambahan (servo 53)
- **Thread-Safety**: Satu *worker thread* untuk semua perintah ke robot, mencegah *socket* collision
- **Smoothing Filter**: Mengurangi jitter gerakan servo
- **Hysteresis & Debounce**: Mencegah toggle flip-flop pada kapit
✅ **Warna Teks Status**: Warna merah (tutup), kuning (buka), hijau (normal) menampilkan status kapit secara real-time di layar
✅ **Keyboard Shortcuts**: Pintasan keyboard `[]`, `]`, `o`, `p` untuk menyesuaikan ambang batas cubit (*PINCH_CLOSE_RATIO* dan *PINCH_OPEN_RATIO*) secara real-time tanpa perlu edit kode
✅ **Konfigurasi File**: Nilai threshold disimpan di file *~/.ugot_hand_config.json* dan dibaca otomatis saat startup
✅ **PID Controller**: Kontrol PID dengan state variables (previous_error, integral_error) dan gains (KP, KI, KD) untuk gerakan servo yang lebih halus dan responsif

## 📦 Dependencies

```bash
pip install -r requirements.txt
```

## ⚙️ Konfigurasi

### ID Servo

| ID | Nama | Fungsi |
|----|------|--------|
| 51 | Pan | Kanan-Kiri (tangan kanan) |
| 52 | Tilt | Atas-Bawah (tangan kanan) |
| 53 | Extra | Tangan kiri |

### Parameter Utama

| Parameter | Nilai | Keterangan |
|-----------|-------|-----------|
| `SERVO_SEND_INTERVAL` | 0.08s | Jeda minimum antar kirim command servo |
| `alpha` | 0.7 | Filter smoothing posisi tangan |
| `pinch_alpha` | 0.5 | Filter smoothing rasio cubit |
| `PINCH_CLOSE_RATIO` | 0.35 | Di bawah ini = dianggap mencubit → tutup kapit (bisa diubah real-time dengan `[]` dan `]`) |
| `PINCH_OPEN_RATIO` | 0.55 | Di atas ini = dianggap lepas cubit → buka kapit (bisa diubah real-time dengan `o` dan `p`) |
| `PINCH_CONFIRM_FRAMES` | 4 | Frame yang dibutuhkan untuk konfirmasi |
| `PID_KP_51` | 0.04 | Gain proporsional untuk servo 51 (pan) |
| `PID_KI_51` | 0.005 | Gain integral untuk servo 51 (pan) |
| `PID_KD_51` | 0.1 | Gain turunan untuk servo 51 (pan) |
| `PID_KP_52` | 0.04 | Gain proporsional untuk servo 52 (tilt) |
| `PID_KI_52` | 0.005 | Gain integral untuk servo 52 (tilt) |
| `PID_KD_52` | 0.1 | Gain turunan untuk servo 52 (tilt) |
| `~/.ugot_hand_config.json` | File konfigurasi | Menyimpan nilai threshold antara sesi, dibaca otomatis saat startup |

### Batas Gerak Servo

| Servo | Min | Max |
|-------|-----|-----|
| 51 | 40 | 140 |
| 52 | -140 | -60 |
| 53 | -170 | 40 |

## 🚀 Cara Mengjalankan

```bash
python ugot-hand.py
```

**Persyaratan:**
- Robot UGOT terhubung ke jaringan WiFi yang sama dengan laptop (IP: `192.168.1.2`)
- Kamera laptop berfungsi dengan baik

## 🎥 Cara Mengontrol

1. **Tangan Kanan** — gerakkan ke kiri/kanan/atas/bawah untuk menggerakkan servo 51 & 52
2. **Cubit (Tangan Kanan)** — jempol dan telunjuk bertemu → tutup capit; jari terbuka → buka capit
3. **Tangan Kiri** — gerakkan untuk menggerakkan servo 53

## 🏗️ Arsitektur

```
┌─────────────┐     ┌──────────────┐
│  OpenCV     │────▶│  MediaPipe   │────▶ Deteksi Tangan
│  (Kamera)   │     │  (Landmark)  │
└─────────────┘     └──────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Main Loop       │
                    │  (Thread Utama)  │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌──────────────┐ ┌──────────┐ ┌──────────┐
     │  Servo 51/52 │ │  Clamp   │ │ Servo 53 │
     │  (Pan/Tilt)  │ │  (Capit) │ │ (Extra)  │
     └──────────────┘ └──────────┘ └──────────┘
                    ▲
                    │ (Satu-satunya thread yang boleh akses robot)
     ┌──────────────┴──────────────┐
     │   robot_worker (Thread)     │
     │   - Throttle command        │
     │   - Lock (thread-safe)      │
     └─────────────────────────────┘
```

## ⚠️ Catatan Penting

- SDK UGOT kemungkinan besar **tidak thread-safe**. Semua perintah ke robot dikirim melalui satu thread (`robot_worker`) untuk mencegah tabrakan *socket*.
- Gunakan kamera dengan pencahayaan yang cukup agar deteksi tangan stabil.
- Pastikan tangan terlihat jelas oleh kamera (tanpa penghalang).

## 📝 License

Dibuat untuk keperluan proyek UGOT Hand Gesture.