# set base image (host OS)
FROM python:3.8

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY ./requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY ./ .
COPY ./scripts/start.sh .
RUN chmod 755 ./start.sh

# command to run on container start
CMD ["./start.sh"]
#CMD ["tail -f /dev/null"]
#CMD ["tail", "/dev/null"]