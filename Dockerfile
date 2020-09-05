FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./*.py ./
COPY ./client_secret.json ./

CMD ["python", "./bot.py"]
