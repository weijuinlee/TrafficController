1. FROM python:3.6.1-alpine

2. WORKDIR /app

3. ADD . /app

4. RUN pip install -r requirements.txt
5. 
CMD ["python","app.py"]