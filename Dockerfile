FROM python:3.10
LABEL maintainer "Travis F. Collins <travis.collins@analog.com>"
USER root
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
RUN git clone https://github.com/sdgtt/telemetry.git
RUN cd telemetry && pip install -r requirements.txt && pip install . && cd ..
# Copy SSL certificates
COPY cos_analog_com.crt ./ssl/cos_analog_com.crt 
COPY cos_analog_com.key ./ssl/cos_analog_com.key
RUN chmod u+x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
EXPOSE 5000
