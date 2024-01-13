FROM python:3.8

RUN pip install pipenv

# The enviroment variable ensures that the python output is set straight
# to the terminal with out buffering it first
ENV PYTHONUNBUFFERED 1

# ENV PORT=8000

WORKDIR /app

COPY . /app/

RUN pipenv install --dev --system --deploy

RUN useradd -m chipyuser

# RUN chown -R chipyuser:chipyuser /app
RUN ["chmod", "+x", "/app/start.sh"]

USER chipyuser

CMD bash /app/start.sh