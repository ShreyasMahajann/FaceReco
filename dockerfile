# Use the official Python base image
FROM python:3.8

# Install necessary dependencies
RUN apt-get update --fix-missing \
    && apt-get install -y libgl1 \
    && apt-get install -y cmake \
    && apt-get install -y build-essential \
    && apt-get install -y libjpeg-dev zlib1g-dev

# Install Python dependencies
# RUN pip install --upgrade pip
RUN pip install Django
RUN pip install djangorestframework
RUN pip install django-cors-headers
RUN pip install scikit-build
RUN pip install face-recognition

# Install OpenCV dependencies
RUN pip install opencv-python-headless
RUN pip install opencv-python

# Copy application code
COPY . .

# Expose necessary ports
EXPOSE 8888
EXPOSE 4444

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8888"]
