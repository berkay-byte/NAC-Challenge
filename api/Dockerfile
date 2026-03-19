#api/Dockerfile

FROM python:3.13-slim

#set working directory
WORKDIR /app

#Install operating system-level dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc curl && rm -rf /var/lib/apt/lists/*

#Copy Python dependencies and Install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copy applications codes
COPY . .

#Start FastAPI applications with Uvicorn

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

