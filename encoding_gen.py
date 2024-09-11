import os
import face_recognition
import pickle
student_images_folder = os.getcwd()




for filename in os.listdir(student_images_folder):
    if filename.endswith(('.jpg', '.png', '.jpeg')):
        student_data = {}
        roll_number = os.path.splitext(filename)[0]
        image_path = os.path.join(student_images_folder, filename)
        image = face_recognition.load_image_file(image_path)
        encoding = face_recognition.face_encodings(image)[0]
        student_data[roll_number] = encoding
        encodings_file = f"{roll_number}.pkl"
        with open(encodings_file, 'wb') as f:
            pickle.dump(student_data, f)




