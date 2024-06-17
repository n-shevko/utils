FROM ubuntu:22.04

RUN apt-get update
RUN apt-get install -y git
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y mysql-server=8.0.37-0ubuntu0.22.04.3

RUN apt-get update
RUN apt-get install -y curl ffmpeg
RUN apt-get install -y build-essential
RUN git clone https://github.com/ggerganov/whisper.cpp.git
WORKDIR whisper.cpp
RUN make
RUN bash ./models/download-ggml-model.sh base.en

RUN apt install -y python3 python3-pip default-libmysqlclient-dev pkg-config gosu
WORKDIR /src
RUN touch prod
COPY packages .
RUN pip install -r packages
COPY . .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/src/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "project.asgi:application"]