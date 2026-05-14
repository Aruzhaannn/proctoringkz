import cv2

# Загрузка готовой модели детекции лиц (встроена в OpenCV)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Открываем веб-камеру (0 = первая камера)
cap = cv2.VideoCapture(0)

print("Камера запущена. Нажмите Q для выхода.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Камера не найдена")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Ищем лица на кадре
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

    # Рисуем рамку вокруг каждого лица
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, "Face", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Показываем статус
    face_count = len(faces)
    if face_count == 0:
        status = "NO FACE DETECTED"
        color = (0, 0, 255)  # красный
    elif face_count == 1:
        status = "OK - 1 face"
        color = (0, 255, 0)  # зелёный
    else:
        status = f"WARNING - {face_count} faces!"
        color = (0, 165, 255)  # оранжевый

    cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    cv2.imshow("ProctorAI - Face Detection Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()