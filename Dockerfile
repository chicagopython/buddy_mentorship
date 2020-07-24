FROM python:3.7

RUN pip install pipenv

# The enviroment variable ensures that the python output is set straight
# to the terminal with out buffering it first
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . /app/

RUN pipenv install --system --deploy