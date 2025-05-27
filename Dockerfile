FROM python:3.10-slim
RUN apt-get update && apt-get upgrade -y && apt-get install gcc
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY app/ ./app
COPY black.csv .

CMD ["python", "app/main.py"]

