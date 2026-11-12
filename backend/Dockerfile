FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
COPY alembic.ini .
COPY migrations ./migrations
RUN python -m compileall -q /app
USER 1001
EXPOSE 8080
# Free Render instances do not provide a pre-deploy command. Apply safe, versioned
# Alembic migrations at container start before serving requests.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
