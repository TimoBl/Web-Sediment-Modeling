# we can specify the python version
FROM python:3.8

# set a directory for the app
WORKDIR /usr/src/app

# requirements
COPY req.txt req.txt
COPY run.py run.py
RUN pip install -r req.txt

# Geone, downloads the latest version (be careful -> no versioning)
RUN git clone https://github.com/randlab/geone.git && cd geone && pip install .

# Archyp, downloads the latest version (be careful -> no versioning)
RUN git clone https://github.com/randlab/ArchPy.git && cd ArchPy && pip install .

# hotfix for issues
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# update app
COPY app app
COPY working_dir working_dir

# tell the port number the container should expose
EXPOSE 5000

# run the command
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]