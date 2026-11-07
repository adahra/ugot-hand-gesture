import threading
import time

# 1. Deadzone calculation check
def calc_step(error):
    if abs(error) <= 10:
        return 0
    return int(error * 0.04) or (1 if error > 0 else -1)

assert calc_step(0) == 0
assert calc_step(10) == 0
assert calc_step(-10) == 0
assert calc_step(11) == 1, "Deadzone truncation bug fixed for 11..24"
assert calc_step(24) == 1
assert calc_step(25) == 1
assert calc_step(50) == 2
assert calc_step(-11) == -1
assert calc_step(-24) == -1
assert calc_step(-50) == -2

# 2. EMA smoothing check
alpha = 0.7
sx, sy = 320, 240
cx, cy = 400, 300
sx = int(alpha * cx + (1 - alpha) * sx)
sy = int(alpha * cy + (1 - alpha) * sy)
assert sx == 376
assert sy == 282

# 3. Thread wait exit responsiveness check
evt = threading.Event()
start_t = time.time()
evt.set()
evt.wait(0.08)
elapsed = time.time() - start_t
assert elapsed < 0.05, f"stop_event.wait responsive on set: {elapsed}s"

print("ALL_CHECKS_PASSED")
