# TheatreL33t

_Christmas assignment for COMP66 (2018), created by Akash Bhattacharya._

### Usage
Please note that this app has only been tested on Mac OS, and therefore is guaranteed to work in any UNIX-based environment. 

If you have the .zip file, then first decompress the archive. A virtual environment is included here.

If you don't have the .zip file, then you'll need to create a virtual environment and possibly start up the DB and Flask app manually.

From the command line, run the following command: 

```bash run.sh``` 

This should start the Neo4j DB, and serve up the Flask app.

In short, the bash script does the following key commands:

```./neo4j/bin/neo4j console &``` - starts DB and runs process in background.
```export FLASK_APP=app.py``` - sets source Flask file.
```flask run``` - start webserver.

To close the webserver and DB, simply kill the process (Ctrl + C from the terminal window).

### Location
The website is hosted on a Google Compute instance: [landing page](http://35.234.129.165/). To log in as admin, please visit the [admin login page](http://35.234.129.165/admin).

Please find the requested video here: [link]()

### Resources
This project is coded in Python 3, and uses the Flask library as the web framework. 

The Database used was [Neo4j](https://neo4j.com/), a Graph DB. 

The website is hosted on Google Cloud Platforms (simply because it was free).

