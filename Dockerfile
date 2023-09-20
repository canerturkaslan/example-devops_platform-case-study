FROM ubuntu:latest
RUN apt-get update \
        && apt-get install default-jdk unzip wget -y
RUN wget 
http://h2o-release.s3.amazonaws.com/h2o/rel-3.42.0/3/h2o-3.42.0.3.zip \
  && unzip h2o-3.42.0.3.zip
ENV H2O_VERSION 3.42.0.3
COPY ojdbc11.jar .
CMD java -cp h2o-3.42.0.3/h2o.jar:ojdbc11.jar water.H2OApp
