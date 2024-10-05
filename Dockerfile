FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN apt update
RUN apt install ffmpeg -y
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]