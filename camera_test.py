import cv2

url = "http://192.168.1.7:8080/video"   # Change if IP changes

cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("❌ Cannot open RTSP stream")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("❌ Frame not received")
        break

    cv2.imshow("Phone CCTV Feed", frame)

    if cv2.waitKey(1) & 0xFF == 27:   # ESC
        break

cap.release()
cv2.destroyAllWindows()
