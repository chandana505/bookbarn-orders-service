FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY app ./app
COPY start.sh .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8001
CMD ["./start.sh"]
