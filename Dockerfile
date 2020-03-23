FROM python:3.6-slim
COPY app.py /usr/app/
COPY requirements.txt /usr/app/
WORKDIR /usr/app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8050
ENTRYPOINT ["python", "app.py"]