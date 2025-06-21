FROM python:3.10-slim

WORKDIR /app

# -- 1️⃣ system packages -------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential binutils && \
    rm -rf /var/lib/apt/lists/*

# -- 2️⃣ python deps -----------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -- 3️⃣ app code --------------------------------------------------------
COPY . .

# Build the executable
RUN pyinstaller --onefile --name fastapi_app app/main.py

# Output folder is /app/dist
CMD ["cp", "/app/dist/fastapi_app.exe", "/output/"]

# Expose & run
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

