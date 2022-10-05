# Data and code from EuroCALL 2022 paper

Please contact Mircea Lungu (mlun@itu.dk) for access to the Zeeguu API environment and a copy of the DB dump.


## Anonymized Database Dump

* from the Zeeguu project
* in SQL format

### Main tables

* **user** - info about a user 
* **article** - info about an article, including fk_difficulty - the difficulty that's presented in the UI; language 
* **bookmark** - a word or group of words that has been translated by a user in an article together with the time when it was translated
* **user\_activity\_data** - logs events relevant for understanding users interaction with texts and exercises (and the platform in general)
	* interactions in the article reader are prefixed with UMR (e.g. UMR - TRANSLATE TEXT);

* **user\_reading\_session** - duration of a continuous interaction wit the reader; duration is in ms; sessions are closed if a user does not interact with a text for 2min
* **user\_exercise\_session** - same as reading session, but computed for exercises


### How to use

* Import to a local MySQL DB, and run queries on it. Some example SQL queries are available [in the Zeeguu-API repository](https://github.com/zeeguu-ecosystem/zeeguu-api/tree/master/tools/sql)
* To analyze the data from Python using the `zeeguu.core.model` [API](https://github.com/zeeguu-ecosystem/zeeguu-api/tree/master/zeeguu/core/model) see [PYTHON_ANALYSIS.md](./PYTHON_ANALYSIS.md). 


### Importing the DB dump on a Mac with Mysql Installed
````
unzip zeeguu_anonymized-2021-01-06.sql.zip
mysql -uroot -p -h localhost zeeguu_test < zeeguu_anonymized-2021-01-06.sql
````

### Set environment variable to config file
````
export ZEEGUU_CONFIG=./zeeguu-api/default_api.cfg
````


