from fer import FER
import cv2

emotion_detector = FER()
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # detect emotions in the frame
    emotions = emotion_detector.detect_emotions(frame)

    if emotions:
        face = emotions[0]
        (x, y, w, h) = face["box"]
        scores = face["emotions"]
        dominant = max(scores, key=scores.get)

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
        cv2.putText(frame, dominant, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 2)

    cv2.imshow("Emotion Detection (Press Q)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
