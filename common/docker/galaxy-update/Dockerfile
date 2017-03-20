# For updating Galaxy

FROM centos:6

MAINTAINER The Galaxy Project http://galaxyproject.org/

RUN yum groupinstall -y 'development tools'
RUN yum install -y git
RUN yum clean all
RUN groupadd -g 803372 G-803372
RUN useradd -u 819456 -c 'Galaxy Test' -g 803372 -d /home/g2test -s /bin/bash -m g2test
RUN useradd -u 819800 -c 'Galaxy Main' -g 803372 -d /home/g2main -s /bin/bash -m g2main

COPY condarc /home/g2test/.condarc
RUN chown g2test:803372 /home/g2test/.condarc
COPY condarc /home/g2main/.condarc
RUN chown g2main:803372 /home/g2main/.condarc
