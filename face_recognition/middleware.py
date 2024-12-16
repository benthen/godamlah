import time
import random
import pickle
from .models import User

class UserBehaviorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start time
        start_time = time.time()

        # Process the request
        response = self.get_response(request)

        # Only log for authenticated users
        if request.user.is_authenticated:
            # Simulated user behavior data (replace with real tracking logic)
            typing_speed = random.uniform(70, 100)  # Characters per second
            mouse_speed = random.uniform(0.2, 1.0)  # Movement speed
            keystroke_interval = random.uniform(0.4, 1.0)  # Seconds
            time_spent = time.time() - start_time  # Time spent on the request
            geolocation_variance = random.uniform(0.8, 1.0)  # Simulated consistency

            # Evaluate user behavior
            features = [typing_speed, mouse_speed, keystroke_interval, time_spent, geolocation_variance]
            is_anomalous = evaluate_behavior(features)

            # Save the log
            User.objects.create(
                user=request.user,
                typing_speed=typing_speed,
                mouse_speed=mouse_speed,
                keystroke_interval=keystroke_interval,
                time_spent=time_spent,
                geolocation_variance=geolocation_variance,
                is_anomalous=is_anomalous,
            )

        return response

def evaluate_behavior(features):
    # Load the model and scaler
    with open('anomaly_model.pkl', 'rb') as f:
        model, scaler = pickle.load(f)

    # Preprocess the features
    features_scaled = scaler.transform([features])

    # Predict anomaly (-1 = anomaly, 1 = normal)
    prediction = model.predict(features_scaled)
    return prediction[0] == -1
