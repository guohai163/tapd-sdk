FROM python:3.8

MAINTAINER GUOHAI.ORG

WORKDIR /opt/g-tapd

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./

CMD ["python", "/opt/g-tapd/main.py"]