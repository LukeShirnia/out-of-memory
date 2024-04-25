ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}-buster
WORKDIR /app
COPY . .
RUN pip install pytest
CMD ["pytest", "-v"]
