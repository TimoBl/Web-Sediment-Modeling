# we can specify the python version
FROM python:3.8

# set a directory for the app
WORKDIR /usr/src/app

# requirements
COPY req.txt req.txt
COPY run.py run.py
RUN pip install -r req.txt

# Geone
COPY geone geone
RUN cd geone && pip install .

# Archyp
COPY ArchPy ArchPy
RUN cd ArchPy && pip install .

# hotfix for issues
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
# RUN pip uninstall -y click
# RUN pip install click==7.1.2

# update app
COPY app app

# tell the port number the container should expose
EXPOSE 5000

# run the command
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]