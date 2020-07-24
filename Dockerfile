FROM python:3.7

RUN pip install pipenv

# The enviroment variable ensures that the python output is set straight
# to the terminal with out buffering it first
ENV PYTHONUNBUFFERED 1

ENV PORT=8000

WORKDIR /app

COPY . /app/

RUN pipenv install --system --deploy

RUN useradd -m chipyuser

USER chipyuser

CMD gunicorn buddy_mentorship.wsgi:application -w 4 --bind 0.0.0.0:$PORT