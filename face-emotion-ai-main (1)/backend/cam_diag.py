import cv2
import time

def try_open(index, backend=None, backend_name=""):
    try:
        cap = cv2.VideoCapture(index if backend is None else (index, backend))
        opened = cap.isOpened()
        ret, frame = (False, None)
        if opened:
            # give the camera a moment to warm up
            time.sleep(0.3)
            ret, frame = cap.read()
        if opened and ret and frame is not None:
            h, w = frame.shape[:2]
            print(f"[OK] index={index:<2} backend={backend_name:<8} -> frame {w}x{h}")
            # show a 1-second preview
            cv2.imshow(f"Preview idx {index} {backend_name} (closes in 1s)", frame)
            cv2.waitKey(1000)
            cv2.destroyAllWindows()
            cap.release()
            return True
        else:
            print(f"[--] index={index:<2} backend={backend_name:<8} -> opened={opened}, ret={ret}")
            cap.release()
            return False
    except Exception as e:
        print(f"[ERR] index={index:<2} backend={backend_name:<8} -> {e}")
        return False

print("Scanning camera indexes 0..5 with different backends...")
candidates = []
for idx in range(0, 6):
    # Default backend (let OpenCV decide)
    if try_open(idx, None, "AUTO"):
        candidates.append((idx, None, "AUTO"))
    # DirectShow backend (often best on Windows)
    if try_open(idx, cv2.CAP_DSHOW, "DSHOW"):
        candidates.append((idx, cv2.CAP_DSHOW, "DSHOW"))
    # Media Foundation backend (sometimes better on newer systems)
    if try_open(idx, cv2.CAP_MSMF, "MSMF"):
        candidates.append((idx, cv2.CAP_MSMF, "MSMF"))

print("\nDone.")
if candidates:
    print("Working options (pick the first):")
    for c in candidates:
        print(f"  index={c[0]} backend={c[2]}")
else:
    print("No working camera found. Make sure Windows Camera privacy is ON, other apps are closed, and try a reboot.")
