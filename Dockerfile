FROM python:3.7
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./
RUN pip install -r requirements.txt
CMD exec gunicorn --bind :3003 --workers 1 --threads 8 app.main:app
EXPOSE 3003