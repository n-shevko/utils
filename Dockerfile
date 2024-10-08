FROM ubuntu:22.04

RUN apt-get update
RUN apt-get install -y git
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y mysql-server

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
RUN apt-get install -y libpango1.0-dev pkg-config python3-dev
RUN pip install meson ninja
RUN pip install wheel
RUN pip install -r packages
RUN python3 -m spacy download en_core_web_md
COPY . .
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/src/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "project.asgi:application"]