FROM python:3.11


WORKDIR /app

COPY . ./
COPY models/ /app/models/

RUN python -m pip install --upgrade pip && pip install -r requirements.txt


LABEL authors="enjoy@data-silence.com"
LABEL app_name='antiSMIbot'

ENTRYPOINT ["python3", "antiSMIbot.py"]