FROM ubuntu:22.04

RUN apt-get update
RUN apt-get install -y git
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y mysql-server=8.0.36-0ubuntu0.22.04.1

#RUN apt-get install -y curl ffmpeg
#RUN apt-get install -y build-essential
#RUN git clone https://github.com/ggerganov/whisper.cpp.git
#WORKDIR whisper.cpp
#RUN make
#RUN bash ./models/download-ggml-model.sh base.en

RUN apt install -y python3 python3-pip
WORKDIR /src
#RUN ls
COPY * .
COPY my2.cnf my.cnf
#RUN pip install -r packages
#RUN python3 manage.py migrate
#CMD daphne -b 0.0.0.0 -p 8000 project.asgi:application
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/src/entrypoint.sh"]
#CMD mysqld --init-file=/src/mysql-init.txt --datadir=/data/mysql
CMD sleep 3555