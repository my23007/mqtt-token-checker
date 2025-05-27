FROM python:3.12-alpine
RUN apk add gcc python3-dev musl-dev linux-headers
WORKDIR /app
# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the app
COPY app/ ./app
COPY black.csv .
CMD ["python", "app/main.py"]

