import cv2
import mediapipe as mp
import time

mp_face = mp.solutions.face_detection
mp_draw = mp.solutions.drawing_utils

# Force Windows to use DirectShow backend (very stable for laptops)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Give camera a moment to start
time.sleep(1.0)

with mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5) as detector:
    while True:
        ret, frame = cap.read()

        # If frame read fails, skip instead of quitting
        if not ret:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb)

        if results.detections:
            for detection in results.detections:
                mp_draw.draw_detection(frame, detection)

        cv2.imshow("Face Detection - Press Q to Quit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
