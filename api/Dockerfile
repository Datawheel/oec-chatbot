# building stage
FROM python:3.11-slim as build

# update prerequisites
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
  build-essential \
  gcc \
  libpq-dev

# working directory
WORKDIR /usr/app

# create virtual environment
RUN python -m venv /usr/app/venv

# load virtual environment
ENV PATH="/usr/app/venv/bin:$PATH"

# install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# initializing stage
FROM python:3.11-slim as deploy
WORKDIR /usr/app

# update prerequisites
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
  build-essential \
  gcc \
  libpq-dev

# copy app files
COPY --from=build /usr/app/venv ./venv
COPY . .

ENV PATH="/usr/app/venv/bin:$PATH"

# Run the app
CMD [ "uvicorn", "src.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80", "--timeout-keep-alive", "120" ]