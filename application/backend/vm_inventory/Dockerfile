FROM python:3.10.6-slim
COPY *.py /
COPY requirements.txt /
RUN apt-get update
RUN  pip3  install -r requirements.txt
ENTRYPOINT sh -c "python3 az_price.pyaws_price.py && \
                  python3 az_region.py && \
                  python3 aws_price.py && \
                  python3 az_price.py"
