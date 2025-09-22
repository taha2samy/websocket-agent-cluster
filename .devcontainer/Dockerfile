FROM registry.access.redhat.com/ubi9/python-311

USER 0

RUN dnf install -y dnf-utils && \
    dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo && \
    dnf install -y docker-ce-cli --nobest && \
    dnf clean all

RUN pip3 install --no-cache-dir pipenv

WORKDIR /workspace

COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy

COPY . .