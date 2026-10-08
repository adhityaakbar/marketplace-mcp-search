FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn beautifulsoup4 pydantic
COPY server.py .
EXPOSE 8095
CMD ["python", "server.py"]
