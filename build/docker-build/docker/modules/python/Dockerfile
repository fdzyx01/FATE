# runtime envrionment
ARG PREFIX=prefix
ARG BASE_TAG=tag
FROM ${PREFIX}/base-image:${BASE_TAG} as builder

WORKDIR /data/projects/fate/

COPY fate.tar.gz .
COPY fateflow.tar.gz .
COPY examples.tar.gz .
COPY conf.tar.gz .
COPY fate.env .
COPY hadoop-2.7.4.tar.gz .
COPY spark-2.4.1-bin-hadoop2.7.gz .

RUN tar -xzf fate.tar.gz; \
    tar -xzf fateflow.tar.gz; \
    tar -xzf examples.tar.gz; \
    tar -xzf conf.tar.gz; \
    tar -xf ./hadoop-2.7.4.tar.gz; \
    tar -xvf ./spark-2.4.1-bin-hadoop2.7.gz;

FROM ${PREFIX}/base-image:${BASE_TAG}

WORKDIR /data/projects/fate

COPY  --from=builder /data/projects/fate/fate /data/projects/fate/fate
COPY  --from=builder /data/projects/fate/fateflow /data/projects/fate/fateflow
COPY  --from=builder /data/projects/fate/examples /data/projects/fate/examples
COPY  --from=builder /data/projects/fate/conf /data/projects/fate/conf
COPY  --from=builder /data/projects/fate/fate.env /data/projects/fate/
COPY  --from=builder /data/projects/fate/hadoop-2.7.4 /data/projects/hadoop-2.7.4
COPY  --from=builder /data/projects/fate/spark-2.4.1-bin-hadoop2.7 /data/projects/spark-2.4.1-bin-hadoop2.7

RUN rpm --rebuilddb && \
    rpm --import /etc/pki/rpm-gpg/RPM* && \
    yum install -y  which java-1.8.0-openjdk wget && \
    yum clean all

RUN mkdir -p ./fml_agent/data;

ENV JAVA_HOME=/usr/lib/jvm/jre-1.8.0-openjdk
ENV FATE_PROJECT_BASE=/data/projects/fate
ENV SPARK_HOME=/data/projects/spark-2.4.1-bin-hadoop2.7/
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/data/projects/hadoop-2.7.4/lib/native
ENV PATH=$PATH:/data/projects/spark-2.4.1-bin-hadoop2.7/bin:/data/projects/hadoop-2.7.4/bin

RUN pip install pyspark

CMD ["/bin/bash", "-c", "sleep 5 && python fateflow/python/fate_flow/fate_flow_server.py"]