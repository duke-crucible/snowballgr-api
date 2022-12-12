FROM image-mirror-prod-registry.cloud.duke.edu/library/python:3.8.11-slim-buster AS base
WORKDIR /app
ENV \ 
    # so logs are not buffered
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install -U pip

FROM base AS build
RUN apt-get update && apt-get install -y \
  gcc=4:8.3.0* \
  libffi-dev
RUN pip install poetry==1.1.6
RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH \
    VIRTUAL_ENV=/venv
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-root --no-dev --no-interaction
COPY . /app
RUN poetry build --format wheel

FROM build AS dev
RUN poetry install
# Keep in sync with prod CMD
EXPOSE 8000
ENV FLASK_APP ./run.py
CMD [ "gunicorn", \
  # See https://pythonspeed.com/articles/gunicorn-in-docker/ for worker settings.
  "--worker-tmp-dir=/dev/shm", \
  "--worker-class=gthread", \
  "--bind=0.0.0.0:8000", \
  "--threads=4", \
  "--workers=2", \
  "run:app"]

FROM base AS prod
COPY --from=build /venv /venv
COPY --from=build /app/dist/*.whl /app/dist/
RUN /venv/bin/pip install --no-deps /app/dist/*.whl
COPY --from=build /app/run.py /app/
# Keep in sync with dev CMD
EXPOSE 8000
ENV FLASK_APP ./run.py
CMD [ "/venv/bin/gunicorn", \
  # See https://pythonspeed.com/articles/gunicorn-in-docker/ for worker settings.
  "--worker-tmp-dir=/dev/shm", \
  "--worker-class=gthread", \
  "--bind=0.0.0.0:8000", \
  "--threads=4", \
  "--workers=2", \
  "run:app"]
