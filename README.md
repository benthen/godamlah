# AuthentiCare

## Overview of the AuthentiCare
The purpose of AuthentiCare is to provide an authentication system to healthcare companies that provide remote consultations services. AuthentiCare focuses on "Secure Health, Secure You", which secures the verification of patient identities. 

## What are the problems that AuthentiCare solves?
The problem statements are 
- how can health care prevent patient information from being leaked?
- how can health care ensure the right patient is authenticated?
- how can health care strengthen the security of authentication process?

## What are the solutions proposed by AuthentiCare?
The solutions proposed by AuthentiCare:
- multi factor authentication which combines face recognition, voice recognition and otp sent to patient email
- integrate with Gemini AI API to detect password hygiene to ensure the password does not contain much personal information, and implement the knowledge-based verification
- capture the patient behaviour:
    - typing speed
    - mouse movement
    - geolocation
    - device type
    - time spent
    - keystroke interval
- the patient behaviour is used to train a machine learning model to detect the anomalies when the user is logging in or is using the system

## What are the technologies used in AuthentiCare?
- Django
    - Django template - responsible for front end
    - Django view - responsible for business logic
- Gemini AI API
    - to detect password hygiene
    - analyse for knowledge-based verification
- Machine learning
    - train the model to detect the anomalies
- Multi Factor Authentication
    - OpenCV - face recognition
    - SpeechRecognition - voice recognition
    - OTP - self generated number sent to patient email using Django built in functions
- Database
    - Sqlite - used to store the patient data and patient behaviour

## What are the impacts of AuthentiCare?
### Health care industries
- Save the cost of data breaching
- Enhance the accuracy to identify the patient
- Scalable and adoptable to be used by various health care industries

### Patient
- Patient builds trust with the health care system as they know their identity is securely protected
- Enhance user satisfaction score

# Python Setup

## Install Python
- https://www.python.org/downloads/

## Install package virtualenv
- ```python
    pip install virtualenv

## Create a virtual environment
  - ```python
    python -m venv venv
  
  - Use the virtual environment to install the required packages
      ```python
      .\venv\Scripts\activate

## Install the required packages
  - ```python
    pip install -r requirements.txt

## Project Structure

- **django_godamlah** 
  - the main project in django project
  - the backend settings are configured here
- **face_recognition**
  - contains all the required business logic and front end templates
  - models and forms are defined here
- **media**
  - used to store the face and voice of the patient
- **db.sqlite3**
  - used to store the patient personal information and patient behaviour
- **manage.py**
  - used to run the web server
- **requirements.txt**
  - Lists all required dependencies for the project.
- **README.md**:
  - This is the documentation file.

## Run the server
  - ```python
    python manage.py runserver

