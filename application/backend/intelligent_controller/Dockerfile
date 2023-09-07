FROM python:3.10.6-slim
COPY *.py /
COPY requirements.txt /
RUN apt-get update
RUN apt install curl -y
RUN  pip3  install -r requirements.txt
ENTRYPOINT ["python3", "module.py"]
