from django.http import JsonResponse
from django.shortcuts import render, HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import VerificationSerializer
from django.views.decorators.csrf import csrf_exempt

import cv2
import face_recognition
import pickle
import os
import numpy as np
import json
from datetime import datetime
from PIL import Image
import base64



class VerificationView(APIView):
    serializer_class = VerificationSerializer
            
    def match_student(self, frame_encoding,roll):
        encodings_file = f"encodings/{roll}.pkl"
        with open(encodings_file, 'rb') as f:
            student_data = pickle.load(f)
        for roll_number, known_encoding in student_data.items():
            matches = face_recognition.compare_faces([known_encoding], frame_encoding)
            if any(matches):
                return roll_number
        return None

    def recognize_face(self, frame,roll):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for encoding in face_encodings:
            roll_number = self.match_student(encoding,roll)
            if roll_number:
                return roll_number

        return None

    def verify(self, roll, frame):
        detect_roll = self.recognize_face(frame,roll)
        roll = str(roll)
        detect_roll = str(detect_roll)
        if detect_roll == roll:
            return True
        else:
            return False

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            json_file = "failed_result.json"
            roll = serializer.validated_data['roll']
            if not os.path.exists(f"encodings/{roll}.pkl"):
                current_datetime = datetime.now()
                date_time_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                print(f"Roll number '{roll}' does not exist ---- added to {json_file} file")
                with open(json_file, 'a') as json_file:
                    data = {
                        "roll": roll,
                        "date_time": date_time_string,
                        "status": "PKL file does not exist"
                    }
                    json_file.write(json.dumps(data) + '\n')
                with open('log.txt', 'a') as log_file:
                    log_file.write("maa ki aankh\n")
                return Response({'verified': False}, status=status.HTTP_200_OK)
            image = serializer.validated_data['image']
            decoded_image = base64.b64decode(image)
            nparr = np.frombuffer(decoded_image, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            frame2 = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.verify(roll, frame)
            if result:
                print(f"Request for Roll Number {roll} returns {result}")
            else:
                print(f"Request for Roll Number {roll} returns ---- {result} ---- added to {json_file} file")
                current_datetime = datetime.now()
                date_time_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                response=request.get(f"http://localhost:8000/api/v1/users/cheatAttempt?rollNumber={roll}")
                with open(json_file, 'a') as json_file:
                    data = {
                        "roll": roll,
                        "date_time": date_time_string,
                        "status" : " Image Not Matched"
                    }
                    json_file.write(json.dumps(data) + '\n')
                if not os.path.exists("false_results"):
                    os.makedirs("false_results")
                if not os.path.exists(f"false_results/{roll}"):
                    os.makedirs(f"false_results/{roll}")
                output_filename = f"false_results/{roll}/{date_time_string}.jpg"
                output_filename=os.path.join(os.getcwd(),output_filename)
                img=Image.fromarray(frame2)
                img.save(output_filename)
                with open('log.txt', 'a') as log_file:
                    log_file.write("maa ki chut\n")
            return Response({'verified': not result}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def index(request):
    return render(request,'index.html')
@csrf_exempt
def create_new_encoding(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

    if request.content_type == 'application/json':
        data = json.loads(request.body)
        roll = data.get('roll')
        image_data = data.get('image')
    else:
        roll = request.POST.get('roll')
        image_data = request.POST.get('image')
    if not roll:
        return JsonResponse(
            {'success': False, 'message': "No roll number provided."},
            status=400,
        )
    if image_data:
        # Decode the base64 image data
        decoded_image = base64.b64decode(image_data)
        nparr = np.frombuffer(decoded_image, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Convert to RGB and process
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        if face_encodings := face_recognition.face_encodings(
            rgb_frame, face_locations
        ):
            encoding = face_encodings[0]
            encodings_file = f"encodings/{roll}.pkl"

            # Ensure the directory exists
            os.makedirs(os.path.dirname(encodings_file), exist_ok=True)

            with open(encodings_file, 'wb') as f:
                pickle.dump({roll: encoding}, f)

            return JsonResponse({'success': True, 'message': 'Encoding created successfully.'}, status=201)
        else:
            return JsonResponse({'success': False, 'message': 'No face detected.'}, status=400)
    else:
        return JsonResponse({'success': False, 'message': 'No image data provided.'}, status=400)

