FROM python:3.11


WORKDIR /app

COPY . /app
COPY models/ /app/models/
COPY scripts/ /app/scripts/
COPY imports/ /app/imports/


RUN python -m pip install --upgrade pip && pip install -r requirements.txt


LABEL authors="enjoy@data-silence.com"
LABEL app_name='antiSMIbot'

ENTRYPOINT ["python3", "antiSMIbot.py"]