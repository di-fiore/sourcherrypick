# Ubuntu 22.04 LTS
FROM ubuntu:jammy

# For db authentication
ARG username=monetdb
ARG password=monetdb

# Ensures color output for things that generate it (e.g. ansible).
ENV TERM xterm-256color

RUN apt-get -y update && apt-get -y upgrade

# Installing bison here (although it is installed in the exec.sh file), in
# order for the environment to be properly setup before using cmake.
# Not doing this, breaks cmake compilation step in exec.sh.
RUN apt-get -y install vim python3 python3-pip build-essential cmake bison

COPY . .

WORKDIR "/YeSQL"
RUN echo "user=${username}\npassword=${password}" > .monetdb
RUN sed -i "s/sudo //g" exec.sh
RUN sh exec.sh

WORKDIR "/"
ENTRYPOINT ["./entrypoint.sh"]
