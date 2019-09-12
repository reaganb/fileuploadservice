FROM python

ENV DB_PORT 5432
ENV DB_TYPE postgresql
ENV DB_USER postgres
ENV DB_HOST "10.0.2.2"
ENV DB_PASSWORD nopassword
ENV DB_NAME fileservice_db

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
EXPOSE 5000

#CMD ["gunicorn","app_docker:connex_app","-b","0.0.0.0:8000"]