FROM python:3.11.5-bookworm
WORKDIR /usr/src/app
RUN pip install fitparse pandas plotly geocoder django==4.2.7
COPY . .
CMD python3 manage.py runserver 0.0.0.0:8000