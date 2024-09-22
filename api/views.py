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
def add_base64_padding(base64_string):
    """Adds the required padding to a Base64 string."""
    missing_padding = len(base64_string) % 4
    if missing_padding:
        base64_string += '=' * (4 - missing_padding)
    return base64_string


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
            roll = serializer.validated_data['roll']
            image = serializer.validated_data['image']
            encodings_file = f"encodings/{roll}.pkl"

            # Ensure proper Base64 padding before decoding
            def add_base64_padding(base64_string):
                """Adds the required padding to a Base64 string."""
                missing_padding = len(base64_string) % 4
                if missing_padding:
                    base64_string += '=' * (4 - missing_padding)
                return base64_string

            image = add_base64_padding(image)

            try:
                # Check if the encoding file exists
                if not os.path.exists(encodings_file):
                    current_datetime = datetime.now()
                    date_time_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    json_file = "failed_result.json"

                    # Log the missing encoding file
                    print(f"Roll number '{roll}' does not exist ---- added to {json_file} file")
                    with open(json_file, 'a') as json_file:
                        data = {
                            "roll": roll,
                            "date_time": date_time_string,
                            "status": "PKL file does not exist"
                        }
                        json_file.write(json.dumps(data) + '\n')

                    with open('log.txt', 'a') as log_file:
                        log_file.write(f"PKL file missing for Roll {roll} at {date_time_string}\n")

                    return Response({'verified': False, 'message': 'Encoding file does not exist'}, status=status.HTTP_404_NOT_FOUND)

                # Decode the base64 image data
                decoded_image = base64.b64decode(image)
                nparr = np.frombuffer(decoded_image, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                # Check if the frame was decoded properly
                if frame is None:
                    return Response({'error': 'Invalid image data. Could not decode image.'}, status=status.HTTP_400_BAD_REQUEST)

                # Attempt color conversion only if frame is valid
                frame2 = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            except Exception as e:
                return Response({'error': f'Error processing image: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Call the verify method to match the face with the roll number
            result = self.verify(roll, frame)

            if result:
                # If verification is successful
                print(f"Request for Roll Number {roll} successfully verified.")
            else:
                # If verification fails, log and save the image
                print(f"Request for Roll Number {roll} verification failed.")
                current_datetime = datetime.now()
                date_time_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

                # Log failed verification in a JSON file
                json_file = "failed_result.json"
                with open(json_file, 'a') as json_file:
                    data = {
                        "roll": roll,
                        "date_time": date_time_string,
                        "status": "Image Not Matched"
                    }
                    json_file.write(json.dumps(data) + '\n')

                # Make sure the directory structure exists
                if not os.path.exists("false_results"):
                    os.makedirs("false_results")
                if not os.path.exists(f"false_results/{roll}"):
                    os.makedirs(f"false_results/{roll}")

                # Save the failed image with the timestamp
                output_filename = f"false_results/{roll}/{date_time_string}.jpg"
                output_filename = os.path.join(os.getcwd(), output_filename)
                img = Image.fromarray(frame2)
                img.save(output_filename)

                # Log the failure in a separate log file
                with open('log.txt', 'a') as log_file:
                    log_file.write(f"Verification failed for Roll {roll} at {date_time_string}\n")

            # Return the verification status
            return Response({'verified': result}, status=status.HTTP_200_OK)

        # If the serializer is invalid, return the errors
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
        # Ensure proper Base64 padding before decoding
        image_data = add_base64_padding(image_data)

        # Decode the base64 image data
        decoded_image = base64.b64decode(image_data)
        nparr = np.frombuffer(decoded_image, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Check if the frame was decoded properly
        if frame is None:
            return JsonResponse({'success': False, 'message': 'Invalid image data. Could not decode image.'}, status=400)

        # Convert to RGB and process
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        if face_encodings := face_recognition.face_encodings(rgb_frame, face_locations):
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
