FROM python:3.12

WORKDIR /usr/src/app

COPY . .

RUN apt update
RUN apt install ffmpeg -y
RUN pip install --no-cache-dir -r requirements.txt

COPY objects.py /usr/local/lib/python3.12/site-packages/fakeyou/

CMD [ "python", "./main.py" ]