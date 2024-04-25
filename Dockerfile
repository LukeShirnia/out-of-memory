ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}-buster
RUN pip install pytest isort
# Only install black on Python 3.x as it doesn't exist on 2.x
RUN if [ $(echo ${PYTHON_VERSION} | cut -d. -f1) -ge 3 ]; then pip install black; fi
WORKDIR /app
