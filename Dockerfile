FROM python:3.7-slim
LABEL maintainer="yanyaoyu"
ENV WORKDIR /qa_api_server
WORKDIR $WORKDIR
EXPOSE 8000
CMD python3 main.py
#CMD bash -c bash
ADD . $WORKDIR
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && pip --no-cache-dir install -r $WORKDIR/requirements.txt