import joblib
import face_recognition
import pandas as pd

def verify_face(uploaded_face, stored_face_path):
    uploaded_image = face_recognition.load_image_file(uploaded_face)
    uploaded_encoding = face_recognition.face_encodings(uploaded_image)

    stored_image = face_recognition.load_image_file(stored_face_path)
    stored_encoding = face_recognition.face_encodings(stored_image)

    if len(uploaded_encoding) > 0 and len(stored_encoding) > 0:
        return face_recognition.compare_faces([stored_encoding[0]], uploaded_encoding[0])[0]
    return False


# Load the model
model = joblib.load('xgboost_model.pkl')
scaler = joblib.load('scaler.pkl')

def predict_anomalies(typing_speed, mouse_speed, session_duration):
    """
    Predict if the user behavior is anomalous based on input features.

    Parameters:
    - typing_speed (float): User's typing speed (ms per keystroke).
    - mouse_speed (float): User's mouse speed (pixels per second).
    - session_duration (float): Session duration (seconds).

    Returns:
    - int: 1 if anomalous, 0 otherwise.
    """
    # Create a DataFrame with the correct column names
    input_data = pd.DataFrame({
        'typing_speed': [typing_speed],
        'mouse_speed': [mouse_speed],
        'session_duration': [session_duration]
    })
    
    # Scale the input features
    scaled_features = scaler.transform(input_data)
    
    # Make a prediction
    prediction = model.predict(scaled_features)
    return prediction[0]