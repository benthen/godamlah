from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, RegisterForm
from .models import User, Question
import cv2
import speech_recognition as sr
import os
import json
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import random
import google.generativeai as genai
from django.views.decorators.csrf import csrf_exempt

VERIFICATION_SENTENCE = "I love to play badminton"
GEMINI_API_KEY = "AIzaSyCNC5a5OIm7Dx0S-wfEGgkT1wU0Ixe7Ijw"
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

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('haarcascade_eye_tree_eyeglasses.xml')

def generate_video_stream():
    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    # first_blink = False
    # second_blink = False
    # third_blink = False
    # counter = True
    blink_detected = False
    first_read = True
    
    if not video_capture.isOpened():
        print("Error: Camera could not be opened.")
        return

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Detect faces
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.bilateralFilter(gray_frame,5,1,1)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.3, minNeighbors=5)

        # Draw rectangles around detected faces
        if(len(faces)>0):
            for (x, y, w, h) in faces:
                img = cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                
                # Focus on the face region to detect eyes
                roi_face = gray_frame[y:y+h,x:x+w]
                eyes = eye_cascade.detectMultiScale(roi_face,1.3,5,minSize=(50,50))

                # Check for blinking (simulate user behavior)
                # print(first_blink, second_blink, third_blink)
                print(len(eyes)>=2)
                if(len(eyes)>=2):
                    #Check if program is running for detection 
                    if(first_read):
                        cv2.putText(img, 
                        "Eye detected press s to begin", 
                        (70,70),  
                        cv2.FONT_HERSHEY_PLAIN, 3,
                        (0,255,0),2)
                        first_read = False
                    else:
                        cv2.putText(img, 
                        "Eyes open!", (70,70), 
                        cv2.FONT_HERSHEY_PLAIN, 2,
                        (255,255,255),2)
                        print("open eyes")
                else:
                    if(first_read):
                        #To ensure if the eyes are present before starting
                        cv2.putText(img, 
                        "No eyes detected", (70,70),
                        cv2.FONT_HERSHEY_PLAIN, 3,
                        (0,0,255),2)
                        # first_read = True
                        # counter = True
                        print("no eyes detected")
                    else:
                        #This will print on console and restart the algorithm
                        print("Blink detected--------------")
                        cv2.waitKey(3000)
                        first_read=True
                        blink_detected = True
                        break

            # When a face is captured, stop streaming and send success message
            if blink_detected:
                _, buffer = cv2.imencode('.jpg', frame)
                save_captured_face(buffer)
                yield (b'--frame\r\n'
                    b'Content-Type: text/plain\r\n\r\n'
                    b'Face captured successfully\r\n')
                break

            # Stream the video frame
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            cv2.putText(frame,
            "No face detected",(100,100),
            cv2.FONT_HERSHEY_PLAIN, 3, 
            (0,255,0),2)
        
        #Controlling the algorithm with keys
        # cv2.imshow('img',img)

    video_capture.release()

def video_feed(request):
    # Stream the video feed as a multipart response
    return StreamingHttpResponse(generate_video_stream(),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

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
                        return JsonResponse({'message': 'Voice captured successfully', 'path': voice_filename})
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
            # user = User.objects.get(username=username, identity_number=mykad)
            # print(check_password(password, user.password))
            user = authenticate(request, username=username, password=password, identity_number=mykad)
            if user is not None:
                return redirect('face_recognition:home', user_id=user.pk)  # Redirect to home page or any other page
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
        
