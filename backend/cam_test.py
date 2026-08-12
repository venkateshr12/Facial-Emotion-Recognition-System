import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Webcam not found. Try VideoCapture(1) if external camera.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Webcam Test - Press Q to quit", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
