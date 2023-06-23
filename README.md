# ArchPy
This is the folder for our R&D project

# App Installation

We first have to install the dependencies with the command
```
conda env create -f env_linux.yml
```
Then we also have to install Geone 
```
git clone https://github.com/randlab/geone.git
cd geone
pip install .
```
And ArchPy
```
git clone https://github.com/randlab/ArchPy.git
cd ArchPy
pip install .
```

# Runining the project

To run the application, we simply need to go in the app directory, activate the environment and then run.
```
cd app
conda activate archpy_env
export FLASK_APP=main.py
flask run
```

```
cd app
conda activate archpy_env
rq worker submission-tasks
```

```
redis-server
```

# Docker

```
docker build --platform linux/amd64 -t timobl/archpy .
docker run -p 8888:5000 timobl/archpy
```

```
http://localhost:8888
```

# Ressources

* https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iii-web-forms
* https://blog.abbasmj.com/implementing-redis-task-queues-and-deploying-on-docker-compose
