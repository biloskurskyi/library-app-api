FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1

ARG DEV=false

COPY ./app/requirements.txt /tmp/requirements.txt
COPY ./app/requirements.dev.txt /tmp/requirements.dev.txt

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; then \
        /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm /tmp/requirements.txt /tmp/requirements.dev.txt && \
    adduser \
    --disabled-password \
    --no-create-home \
    django-user

COPY ./app /app
WORKDIR /app
EXPOSE 8000

ENV PATH="/py/bin:$PATH"

USER django-user

CMD ["sh", "-c", "python manage.py wait_for_db && python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
