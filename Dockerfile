FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
COPY . /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
RUN sed -i 's/app.run(debug=True, port=5000)/app.run(host="0.0.0.0", debug=True, port=5000)/g' api_server.py
CMD ["python", "api_server.py"]
# docker build -t firewall_extent .
# docker run -p 5000:5000 firewall_extent