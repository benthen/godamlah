from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, logout

from django_godamlah import settings
from .forms import LoginForm, RegisterForm
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.views.decorators.csrf import csrf_exempt
from django.utils.http import urlsafe_base64_encode
from .models import User, Question
from .utils import predict_anomalies
import speech_recognition as sr
import numpy as np
import cv2
import os
import json
import random
import dlib
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

VERIFICATION_SENTENCE = "I love to play badminton"
<<<<<<< HEAD
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
=======
GEMINI_API_KEY = "API_KEY"
>>>>>>> 3e01c49b7929fd0c77f421009a40c07ec9e30131
GEMINI_MODEL = "gemini-1.5-pro"
genai.configure(api_key=GEMINI_API_KEY)
MODEL = genai.GenerativeModel(GEMINI_MODEL)

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            print(request.POST)
            user = form.save()

            # # Capture typing speed and device type
            # start_time = time.time()
            # device_info = DeviceDetector(request.META['HTTP_USER_AGENT']).parse()
            # user.device_type = device_info.device_name
            # user.typing_speed = len(request.POST['username']) / (time.time() - start_time)

            # # Capture geolocation
            # geolocator = Nominatim(user_agent="healthcare")
            # location = geolocator.geocode("Your IP-based Location Here")
            # user.geolocation = f"{location.latitude}, {location.longitude}" if location else None
            # user.save()

            return redirect('face_recognition:verify', user_id=user.id)
        else:
            print(form.errors)
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def verify(request, user_id):
    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        face_verification = request.POST.get("face-recognition")
        voice_verification = request.POST.get("voice-recognition")
        if face_verification == "True" and voice_verification == "True":
            user.is_verified = True
            user.save()
            return redirect('face_recognition:otp', user_id=user.id)
        

    context = {"voice_auth_sentence": VERIFICATION_SENTENCE}
    return render(request, 'verify.html', context)

def otp_view(request, user_id):
    user = User.objects.get(id=user_id)
    otp = random.randint(100000, 999999)
    send_password_reset_email(request, user, user.email, otp)
    if request.method == 'POST':
        print(request.POST)
        return redirect('face_recognition:login')
    context = {"otp": otp}
    
    return render(request, 'otp.html', context)

def calculate_eye_aspect_ratio(eye):
    # Calculate the distances between the vertical landmarks
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])

    # Calculate the distance between the horizontal landmarks
    C = np.linalg.norm(eye[0] - eye[3])

    # Eye Aspect Ratio (EAR)
    ear = (A + B) / (2.0 * C)
    return ear

def generate_video_stream():
    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    EYE_AR_THRESHOLD = 0.18  # Lower the threshold slightly for better sensitivity
    EYE_AR_CONSEC_FRAMES = 2  # Increase to filter noise and make blinking consistent
    blink_count = 0
    global blink_detected
    blink_detected = False

    # Initialize the Dlib face detector and shape predictor
    detector = dlib.get_frontal_face_detector()
    predictor_path = os.path.join(settings.BASE_DIR, "face_recognition", "shape_predictor_68_face_landmarks.dat")
    predictor = dlib.shape_predictor(predictor_path)

    (left_eye_start, left_eye_end) = (42, 48)
    (right_eye_start, right_eye_end) = (36, 42)

    if not video_capture.isOpened():
        print("Error: Camera could not be opened.")
        return

    consecutive_frames = 0

    print("hello")
    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to grab frame")
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = detector(gray_frame)

        if len(faces) > 0:
            for face in faces:
                landmarks = predictor(gray_frame, face)
                landmarks = np.array([(landmarks.part(n).x, landmarks.part(n).y) for n in range(68)])

                left_eye = landmarks[left_eye_start:left_eye_end]
                right_eye = landmarks[right_eye_start:right_eye_end]

                # Calculate EAR for both eyes
                left_ear = calculate_eye_aspect_ratio(left_eye)
                right_ear = calculate_eye_aspect_ratio(right_eye)

                ear = (left_ear + right_ear) / 2.0

                # Display EAR for debugging
                # cv2.putText(frame, f"EAR: {ear:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                if ear < EYE_AR_THRESHOLD:
                    consecutive_frames += 1

                    if consecutive_frames >= EYE_AR_CONSEC_FRAMES:
                        blink_count += 1
                        print(f"Blink detected! Total blinks: {blink_count}")
                        cv2.putText(
                            frame, f"Blink detected! Blinks: {blink_count}", (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2
                        )
                        if blink_count == 2:
                            blink_detected = True
                        consecutive_frames = 0
                else:
                    consecutive_frames = 0

                # Draw the landmarks on the eyes
                # for (x, y) in np.concatenate((left_eye, right_eye), axis=0):
                #     cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
            if blink_detected:
                _, buffer = cv2.imencode('.jpg', frame)
                save_captured_face(buffer)
                yield (b'--frame\r\n'
                    b'Content-Type: text/plain\r\n\r\n'
                    b'Face captured successfully\r\n')
                break
            
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            )

        else:
            cv2.putText(
                frame, "No face detected", (100, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2
            )

    video_capture.release()
    print("stop")

def video_feed(request):
    # Stream the video feed as a multipart response
    return StreamingHttpResponse(generate_video_stream(),
                                 content_type='multipart/x-mixed-replace; boundary=frame')
    
def check_blick_detected(request):
    if blink_detected:  # Replace with actual condition
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "pending"})

def save_captured_face(frame_buffer):
    # Save the captured face in the media storage directory
    output_path = os.path.join("media", 'faces')

    # Ensure the directory exists
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Save the face as a JPEG file
    file_name = 'captured_face.jpg'
    file_path = os.path.join(output_path, file_name)

    with open(file_path, 'wb') as f:
        f.write(frame_buffer.tobytes())

def capture_voice_view(request):
    if request.method == "POST":
        
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            print("Recording voice... Please speak the following sentence:")
            # print(f"\"{otp}\"")
            try:
                audio = recognizer.listen(source, timeout=10)

                # Convert the audio to text
                print("Processing audio...")
                try:
                    spoken_text = recognizer.recognize_google(audio)
                    print(f"Recognized speech: {spoken_text}")

                    # Check if the spoken text matches the expected sentence
                    message = json.loads(request.body.decode("utf-8")).get("message")
                    if message == "sentence":
                        if spoken_text.lower().strip() == VERIFICATION_SENTENCE.lower():
                            # Save the recorded audio in the media directory
                            media_path = os.path.join("media", 'voices')
                            os.makedirs(media_path, exist_ok=True)
                            voice_filename = os.path.join(media_path, 'user_voice.wav')
                            with open(voice_filename, "wb") as f:
                                f.write(audio.get_wav_data())
                        # return JsonResponse({'message': 'Voice captured successfully', 'path': voice_filename})
                        return JsonResponse({'message': 'Voice captured successfully'})
                    elif message == "otp":
                        otp = json.loads(request.body.decode('utf-8')).get('otp')
                        if spoken_text.lower().strip() != str(otp):
                            return JsonResponse({'error': 'OTP is incorrect'})
                        return JsonResponse({'message': 'OTP is correct'})
                        
                    else:
                        return JsonResponse({'error': 'The spoken sentence did not match the expected sentence'})
                except sr.UnknownValueError:
                    return JsonResponse({'error': 'Unable to understand the audio. Please try again.'})
                except sr.RequestError as e:
                    return JsonResponse({'error': f"Error with speech recognition service: {e}"})
            except sr.WaitTimeoutError:
                return JsonResponse({'error': 'No voice detected within the timeout'})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
def login_view(request):
    if request.user.is_authenticated:
        logout_view(request)
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            mykad = form.cleaned_data.get('identity_number')
            password = form.cleaned_data.get('password')
            typing_speed = float(request.POST.get('typing_speed'))
            mouse_movements = float(request.POST.get('mouse_movements'))
            time_spent = float(request.POST.get('time_spent'))
            
            print(typing_speed)
            print(mouse_movements)
            print(time_spent)
            
             # Predict anomaly
            is_anomalous = predict_anomalies(typing_speed, mouse_movements, time_spent)
            
            user = authenticate(request, username=username, password=password, identity_number=mykad)
            if user is not None and is_anomalous == 0:
                return redirect('face_recognition:home', user_id=user.pk)  # Redirect to home page or any other page
            elif user is not None and is_anomalous == 1:
                return redirect('face_recognition:question_page', user_id=user.pk, question_id=1)
            else:
                messages.error(request, "Invalid username or password.", extra_tags='danger')
        else:
            messages.error(request, "Invalid username or password.", extra_tags='danger')
    else:
        form = LoginForm()
    context = {"form": form}
    return render(request, 'login.html', context)

# @login_required(login_url='face_recognition:login')
def home_view(request, user_id):
    context = {}
    return render(request, 'dashboard.html', context)

def logout_view(request):
    logout(request)
    return redirect('user:login')

def send_password_reset_email(request, user, to_email, otp):
    # Email subject
    mail_subject = "Your OTP for Password Reset"
    
    # Render the email message using a template
    message = render_to_string("email_otp.html", {
        'user': user.username,
        'otp': otp,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        "protocol": 'https' if request.is_secure() else 'http',
    })
    
    # Create the email object
    email = EmailMessage(
        subject=mail_subject,
        body=message,
        to=[to_email],
    )
    
    # Attempt to send the email and handle potential exceptions
    try:
        email.send()
        print("success")
    except Exception as e:
        print("fail")
        
def check_password_hygiene(request):
    
    if request.method == "POST":
        data = json.loads(request.body)
        password = data.get("password")
        personalInfo = data.get("personalInfo")
        print(password, personalInfo)

        if not password:
            return JsonResponse({"is_strong": False, "message": "Password is required."})

        try:
            # Define prompt to check password hygiene
            prompt = f"""
            Analyse the following password based on the personal information of the user
            Personal information: {personalInfo}
            Password: {password}
            Produce only one output, whether True or False
            If the password does not contain much information about the overall personal information, then return True
            If the password contains a lot of information about the overall personal information, then return False
            """
            print("generating content...")
            response = MODEL.generate_content(prompt)

            return JsonResponse({"is_strong": eval(response.text)})
        except Exception as e:
            print(e)
            return JsonResponse({"is_strong": False, "message": f"Error analyzing password: {str(e)}"})

    return JsonResponse({"is_strong": False, "message": "Invalid request method."})

@csrf_exempt
def question_page(request, user_id, question_id):
    display_question = None
    last_question = Question.objects.all().last()
    if request.method == "POST":
        current_question = Question.objects.get(id=question_id)
        display_question = Question.objects.filter(id__gt=current_question.id).first()
        
        data = json.loads(request.body)
        question_id = data.get('question_id')
        answer_text = data.get('answer_text')
        
        answers = request.session.get('answers', [])
        answers.append({'question_id': question_id, 'answer_text': answer_text})
        request.session['answers'] = answers
        if display_question and display_question.id == last_question.id:
            return JsonResponse({'id': display_question.id, 'text': display_question.text, "is_last": True})
        elif display_question:
            return JsonResponse({'id': display_question.id, 'text': display_question.text, "is_last": False})
        else:
            return JsonResponse({'id': "", 'text': 'Thank you for completing the questions!', "is_last": True})
    # Load the first question
    display_question = Question.objects.first()
    request.session['answers'] = []
    context = {"user_id": user_id, 'question': display_question}
    return render(request, 'knowledge_based.html', context)

@csrf_exempt
def submit_answers(request):
    if request.method == 'POST':
        actual_answers = {
            1: "27/1/2025",
            2: "Dr Bennedict, Specialty in Liver",
            3: "Hospital of Universiti Putra Malaysia",
            4: 9
        }
        description = {
            1: "The date format of the user answer and the correct answer might be different, hence just check the date in different format",
            2: "The user might not be able to remember the full name and the specialty of the doctor, so make sure that it is similar to the doctor's correct name and specialty",
            3: "The user might not be able to remember the exact name of the hospital or clinic, so make sure that it is similar to the hospital's or clinic's correct name",
            4: "The user might not be able to remember the exact number of remote consulations did before, so make sure the user answer does not deviate very far from the actual number of remote consulations",
        }
        
        question_and_answer = []
        data = json.loads(request.body)
        question_id = data.get('question_id')
        answer_text = data.get('answer_text')
        user_id = data.get('user_id')
        
        # Get all answers from the session
        answers = request.session.get('answers', [])
        answers.append({'question_id': question_id, 'answer_text': answer_text})
        
        for answer in answers:
            question_and_answer.append({
                "user_answer": answer['answer_text'], 
                "correct_answer": actual_answers[int(answer['question_id'])],
                "description": description[int(answer['question_id'])]
        })
            
        prompt = f"""
            Analyse the following answers, which have the user answer and correct answer, and finally return only either True or False
            The purpose of the analysis is to detect whether the user is an unauthorised user
            The correct answer is to check whether the user is able to answer the questions correctly
            The user answer is the answer provided by the user
            The answers with the description for analysis guidance: {question_and_answer}
            If the value of the user answer is very near to the value of the correct answer, then return True
            If the value of the user answer is very different than the value of the correct answer, then return False
            The user answer may not be exactly the same as the correct answer syntactically, as long as the meaning of the user answer is near to the correct answer
            Give me the final oervall output, after you have analysed all the answers, whether it is True or False
            Just return either True or False
        """
        print("generating content...")
        response = MODEL.generate_content(prompt)
        
        if eval(response.text):
            return redirect('face_recognition:home', user_id=user_id)
        else:
            return redirect('face_recognition:verify', user_id=user_id)
        
