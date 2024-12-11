from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, RegisterForm
from .models import User
from django.core.mail import send_mail
import cv2
import speech_recognition as sr
import os
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib import messages
from django.contrib.auth.hashers import make_password

EXPECTED_SENTENCE = "123456"

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
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def verify(request, user_id):
    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        face_verification = request.POST.get("face-recognition")
        voice_verification = request.POST.get("voice-recognition")
        if face_verification == "True" and voice_verification == "True":
            
            return redirect('face_recognition:login')
        

    context = {"voice_auth_sentence": EXPECTED_SENTENCE}
    return render(request, 'verify.html', context)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

def generate_video_stream():
    video_capture = cv2.VideoCapture(0)
    blink_detected = False

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        # Detect faces
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5)

        # Draw rectangles around detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Focus on the face region to detect eyes
            face_region = gray_frame[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(face_region)

            # Check for blinking (simulate user behavior)
            if len(eyes) >= 2:
                blink_detected = True
            else:
                blink_detected = False

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
            print(f"\"{EXPECTED_SENTENCE}\"")
            try:
                audio = recognizer.listen(source, timeout=10)

                # Convert the audio to text
                print("Processing audio...")
                try:
                    spoken_text = recognizer.recognize_google(audio)
                    print(f"Recognized speech: {spoken_text}")

                    # Check if the spoken text matches the expected sentence
                    if spoken_text.lower().strip() == EXPECTED_SENTENCE.lower():
                        # Save the recorded audio in the media directory
                        media_path = os.path.join("media", 'voices')
                        os.makedirs(media_path, exist_ok=True)
                        voice_filename = os.path.join(media_path, 'user_voice.wav')
                        with open(voice_filename, "wb") as f:
                            f.write(audio.get_wav_data())

                        return JsonResponse({'message': 'Voice captured successfully', 'path': voice_filename})
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
    # if request.user.is_authenticated:
    #     logout_view(request)
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = make_password(form.cleaned_data.get('password'))
            mykad = form.cleaned_data.get('identity_number')
            print(username, password, mykad)
            # user = authenticate(request, username=username, password=password, identity_number=mykad)
            user = User.objects.get(username=username, identity_number=mykad, password=password)
            if user is not None:
                return redirect('face_recognition:home')  # Redirect to home page or any other page
            else:
                messages.error(request, "Invalid username or password.", extra_tags='danger')
        else:
            messages.error(request, "Invalid username or password.", extra_tags='danger')
    else:
        form = LoginForm()
    context = {"form": form}
    return render(request, 'login.html', context)

@login_required(login_url='face_recognition:login')
def home_view(request):
    context = {}
    return render(request, 'dashboard.html', context)

# def logout_view(request):
#     logout(request)
#     return redirect('user:login')

# def send_password_reset_email(request, user, to_email):
#     mail_subject = "Activate your user account."
#     message = render_to_string("password_reset_email.html", {
#         'user': user.username,
#         'domain': get_current_site(request).domain,
#         'uid': urlsafe_base64_encode(force_bytes(user.pk)),
#         'token': account_activation_token.make_token(user),
#         "protocol": 'https' if request.is_secure() else 'http'
#     })
#     email = EmailMessage(mail_subject, message, to=[to_email])
#     if email.send():
#         messages.success(request, f'Verification link has been sent to {user.username}', extra_tags = 'success')
#     else:
#         messages.error(request, f'Problem sending email to {to_email}, check if you typed it correctly.', extra_tags = 'danger')

# def activate(request, uidb64, token):
#     try:
#         uid = force_str(urlsafe_base64_decode(uidb64))
#         user = User.objects.get(pk=uid)
#     except (TypeError, ValueError, OverflowError, User.DoesNotExist):
#         user = None

#     if user is not None and account_activation_token.check_token(user, token):
#         return redirect('user:password', username=user.username)
#     else:
#         messages.error(request, "Activation link is invalid!")

#     return redirect('user:login')

# def set_password(request, username):
#     if request.method == 'POST':
#         form = PasswordForm(request.POST)
#         if form.is_valid():
#             password = form.cleaned_data.get('password')
#             user = User.objects.get(pk=username)
#             user.is_active = True
#             user.set_password(password)
#             user.save()
#             messages.success(request, "Password set successfully", extra_tags = 'success')
#             return redirect('user:login')
#         else:
#             messages.error(request, "Password do not match.", extra_tags = 'danger')
#     else:
#         form = PasswordForm()

#     context = {'form': form}
#     return render(request, 'password_reset_form.html', context)
