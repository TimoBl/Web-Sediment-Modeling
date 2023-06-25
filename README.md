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
You can view the application at [localhost:8888](http://localhost:8888).


# Docker Compose

Building the compose
```
docker-compose build
```

Running the containers
```
docker-compose up -d
```

Stopping the contains 
```
docker-compose down
```

# Ressources

* https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iii-web-forms
* https://testdriven.io/blog/asynchronous-tasks-with-flask-and-redis-queue/
* https://blog.abbasmj.com/implementing-redis-task-queues-and-deploying-on-docker-compose
