# Use an official Python runtime as a parent image
FROM python:3.10.15

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 80 (or modify it as per your app's needs)
EXPOSE 80


# Run the app
CMD ["python", "srv/main.py"]
