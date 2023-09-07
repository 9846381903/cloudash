FROM python:3.8-slim
COPY *.py /
RUN apt-get update
COPY requirements.txt /
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3", "module.py"]
