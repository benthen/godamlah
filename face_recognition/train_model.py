import pickle
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np

# Sample training data: Normal user behaviors
# Features: Typing speed, mouse movement speed, keystroke interval, time spent, geolocation consistency
data = np.array([
    [80, 0.3, 0.5, 20, 0.9],  # Normal behavior
    [90, 0.4, 0.6, 18, 0.95], # Normal behavior
    [100, 0.35, 0.55, 19, 0.85], # Normal behavior
    [85, 0.33, 0.52, 21, 0.88], # Normal behavior
])

# Preprocess the data
scaler = StandardScaler()
data_scaled = scaler.fit_transform(data)

# Train Isolation Forest model
model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
model.fit(data_scaled)

# Save the model and scaler for later use
with open('anomaly_model.pkl', 'wb') as f:
    pickle.dump((model, scaler), f)

print("Model and scaler saved successfully!")
