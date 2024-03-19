FROM ubuntu:22.04

RUN apt-get update
RUN apt-get install -y git
RUN apt-get install -y curl ffmpeg
RUN apt-get install -y build-essential
RUN git clone https://github.com/ggerganov/whisper.cpp.git
WORKDIR whisper.cpp
RUN make
RUN bash ./models/download-ggml-model.sh base.en

RUN apt install -y python3 python3-pip
WORKDIR /
RUN git clone https://github.com/n-shevko/utils.git
WORKDIR utils
RUN pip install -r packages
#CMD python3 install.py && daphne project.asgi:application
CMD sleep 99999