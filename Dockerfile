# 1. Python 3.13 slim 버전 사용
FROM python:3.13-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 시스템 패키지 최소 설치 (옵션: gcc, build-essential 필요 시 추가)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 4. 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 복사
COPY . .

# 6. 환경 변수 (UTF-8, 로그 버퍼링 등)
ENV PYTHONUNBUFFERED=1

# 7. FastAPI 앱 실행 (개발/배포에 따라 CMD만 달라지면 됨)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
