# Web Sediment Modeling Demo

This is a proof of feasibility application for a web-accessible geological modeling tool for the [CHYN](https://www.unine.ch/chyn).

![Screenshot](app/assets/img/screenshot.png)


# Installation

```
git clone https://github.com/TimoBl/Web-Sediment-Modeling.git
cd Web-Sediment-Modeling
```


# Local 

If you want to run the flask application locally (without computing) create an environement.
```
conda env create -n archpy_env -f req.txt
conda activate archpy_env
```
Then install [geone](https://github.com/randlab/geone.git) and [ArchPy](https://github.com/randlab/ArchPy.git). The application can than be run with:
```
export FLASK_APP=main.py
flask run
```


# Docker

The preferred way to run it is to install and build the app with Docker which takes care of all the dependencies
```
docker-compose build 
docker-compose up -d
```
Stopping the containers 
```
docker-compose down
```


# Ressources

## Useful links

* https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iii-web-forms
* https://testdriven.io/blog/asynchronous-tasks-with-flask-and-redis-queue/
* https://blog.abbasmj.com/implementing-redis-task-queues-and-deploying-on-docker-compose

## Credits

* Frontend: [Kimmy Costa](https://github.com/kimmyCosta)
