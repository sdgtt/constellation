FROM python:3.10
LABEL maintainer "Travis F. Collins <travis.collins@analog.com>"
USER root
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
RUN git clone https://github.com/sdgtt/telemetry.git
RUN cd telemetry && pip install -r requirements.txt && pip install . && cd ..
RUN chmod u+x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
EXPOSE 5000
