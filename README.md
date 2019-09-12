# File upload service Capstone project

## Using Flask, PostgreSQL, and Docker

Developed a Containerized REST API server that can create, read, update, and delete files in a storage and metadata information in a database.  

### Prerequisites
1. Windows/Linux OS
2. Python 3
3. PostgreSQL database engine
4. Docker CE Engine
5. REST client

### Installation and Usage

#### 1. Building the image and creating the container:

##### The Dockefile
```
FROM python

ENV DB_TYPE postgresql
ENV ROOT_DIR /server
ENV LOG_DIR $ROOT_DIR/logs/
ENV DATA_DIR $ROOT_DIR/data/

ADD . $ROOT_DIR/fileupload
WORKDIR $ROOT_DIR/fileupload

RUN mkdir $LOG_DIR
RUN mkdir $DATA_DIR
RUN pip install -r requirements.txt
RUN pip install gunicorn
RUN pip install python-magic

EXPOSE 8000

CMD ["gunicorn","app_docker:connex_app","-b","0.0.0.0:8000"]
```
This is the ```Dockerfile``` that will be the basis of the image to be built.

##### Build the image
```$ docker image build -t <user>/<image_name>:<version> .```
##### Create the volumes
```
$ docker volume create log-volume
$ docker volume create data-volume
```
This is important for the persistent storage of file saving and logs recording.
##### Create the container 
```
$ docker container run -d -p 80:8000 \
--name <container_name> \
--env DB_USER="<user>" \
--env DB_PASSWORD="<password>" \
--env DB_HOST="<ip_address_or_domain>" \
--env DB_PORT=5432 \
--env DB_NAME="<database_name>" \
```
DB env variable summary:

```DB_TYPE``` - "postgresql" as default.

```DB_USER``` - The database user to authenticate.

```DB_PASSWORD``` - The password for the authenticated user.

```DB_HOST``` - Reachable host and engine for db transactions.

```DB_PORT``` - 5432 as default for postgres.

```DB_NAME``` - The database name and to be used for transactions.

**Note**: These env varables are very important to be defined with the proper value before running the container.

After this, it will automatically run the REST API server. It can be reachable to the default http port 80.
##### Test the connection
On the local machine

```$ curl localhost:8000/```


#### 2. Automated setup for the database
It is possible to create the database, table, and schema with a few simple commands.
As long as the database configurations provided are appropriate, authenticated, and reachable.

Apply the following changes before building the image:
```
- migrations
    - versions
        - (empty)
```
Make sure that there are no versions recorded in the migrations folder.

```migrations``` > ```env.py```
```
def run_migrations_offline():
    .......................................................................................
    .......................................................................................
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, 
>>>>>>  include_schemas=True
    )
```
```migrations``` > ```env.py```
```
    
def run_migrations_online():
    .................................................................
    .................................................................
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
>>>>>>>>>>  include_schemas=True,
            **current_app.extensions['migrate'].configure_args
        )

```
Check both functions above if they have **include_schemas=True** in its scope.


##### Apply the migrations
```
$ docker container exec -it <container_name> /bin/bash

root: /server # python manage.py migrate
root: /server # python manage.py upgrade
```
It will generate a new migration file to the ```migrations/versions``` folder and apply the changes to the database after.

#### 3. Using the REST API server
To use the server, you must have a REST client to send requests from it.
One example of them is the POSTMAN app. You can download the app on https://www.getpostman.com/.

Another feature of the project is that the endpoints are not manually programmed. It uses ```Connexion```, a Python framework compatible with Flask that can automatically handle requests defined using OpenAPI(Swagger).

The endpoints and its specifications can be found on the ```swagger.yml``` file under the ```app``` module.

##### Specification overview:

1. GET /
    - response: "File Upload service by Reagan Balongcas, GRID Trainee"
2. GET /service/fileupload
    - response: array(all files metadata object) , 200
3. GET /service/filupload/{file_hash}
    - response: 
        -   metadata_object, 200 
        -   404    
4. POST /service/fileupload
    - parameters: upfile(formData)
    - responses: 
        - metadata_object, 201
        - 403
5. PUT /service/filupload/{file_hash}
    - parameters: file_hash(path), file(body[file_name,file_type])
    - responses: 
        - metadata_object, 201
        - 403
6. DEL /service/filupload/{file_hash}
    - parameters: flie_hash(path)
    - responses: 
        - string, 201
        - 404

#### 4. Testing
```
tests
    -- functional
    -- unit
     __init__.py
     conftest.py
```
Testing files are located at the testing module. To make it work, install the ````pytest-cov```` library.

Run the tests:
```
$ pytest --cov=app --cov==fileupload --setup-show tests/
```


Result:
```
Name                     Stmts   Miss  Cover
--------------------------------------------
app/__init__.py             45     10    78%
app/config.py                6      0   100%
fileupload/__init__.py       0      0   100%
fileupload/models.py        14      0   100%
fileupload/views.py        179     28    84%
--------------------------------------------
TOTAL                      244     38    84%
```
The modules **app** and **fileupload** combined resulted to an 84% coverage for the testing.

