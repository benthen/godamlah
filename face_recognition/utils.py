import cv2
import face_recognition
import numpy as np

def verify_face(uploaded_face, stored_face_path):
    uploaded_image = face_recognition.load_image_file(uploaded_face)
    uploaded_encoding = face_recognition.face_encodings(uploaded_image)

    stored_image = face_recognition.load_image_file(stored_face_path)
    stored_encoding = face_recognition.face_encodings(stored_image)

    if len(uploaded_encoding) > 0 and len(stored_encoding) > 0:
        return face_recognition.compare_faces([stored_encoding[0]], uploaded_encoding[0])[0]
    return False
