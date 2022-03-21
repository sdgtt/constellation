FROM python:3.8
LABEL maintainer "Travis F. Collins <travis.collins@analog.com>"
USER root
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
RUN git clone -b artifacts-support https://github.com/sdgtt/telemetry.git
RUN cd telemetry && pip install -r requirements.txt && python setup.py install && cd ..
RUN chmod u+x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
EXPOSE 5000
