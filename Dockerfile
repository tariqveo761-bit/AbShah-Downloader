FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install --no-cache-dir flet yt-dlp imageio-ffmpeg
EXPOSE 8560
CMD ["python", "main.py"]
