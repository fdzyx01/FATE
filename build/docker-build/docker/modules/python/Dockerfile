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

RUN tar -xzf fate.tar.gz; \
    tar -xzf fateflow.tar.gz; \
    tar -xzf examples.tar.gz; \
    tar -xzf conf.tar.gz;

FROM ${PREFIX}/base-image:${BASE_TAG}

WORKDIR /data/projects/fate

COPY  --from=builder /data/projects/fate/fate /data/projects/fate/fate
COPY  --from=builder /data/projects/fate/fateflow /data/projects/fate/fateflow
COPY  --from=builder /data/projects/fate/examples /data/projects/fate/examples
COPY  --from=builder /data/projects/fate/conf /data/projects/fate/conf
COPY  --from=builder /data/projects/fate/fate.env /data/projects/fate/

RUN mkdir -p ./fml_agent/data; 

ENV FATE_PROJECT_BASE=/data/projects/fate

CMD ["/bin/bash", "-c", "sleep 5 && python fateflow/python/fate_flow/fate_flow_server.py"]