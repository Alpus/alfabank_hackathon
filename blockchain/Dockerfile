FROM ubuntu:16.04
MAINTAINER Alexander Pushin "work@apushin.com"
RUN apt update -y
RUN apt install -y curl  libssl-dev libzmq3-dev software-properties-common apt-transport-https git make build-essential python-dev

RUN /bin/sh -c "curl -sL https://deb.nodesource.com/setup_8.x | bash -"
RUN /bin/sh -c "curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -"
RUN /bin/sh -c "echo 'deb https://dl.yarnpkg.com/debian/ stable main' | tee /etc/apt/sources.list.d/yarn.list"
RUN apt update -y


RUN apt install -y yarn nodejs
COPY contracts /opt/contracts
WORKDIR /opt/contracts

RUN yarn install
ENTRYPOINT ["???"]

