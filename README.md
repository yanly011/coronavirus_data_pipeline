# Udacity Data Engineering Nanodegree - Capstone Project

## Introduction
This is the final project for the Data Engineer Nanodegree. Udacity gives us the option to use their suggested project or pick one dataset and scope it by ourselves. For the current special period, I decide to choose a dataset about Coronavirus cases and other types of data about that. The dataset was provided by on [Kaggle](https://www.kaggle.com) and contains two original data files: [COVID19_line_list_data.csv](https://docs.google.com/spreadsheets/d/e/2PACX-1vQU0SIALScXx8VXDX7yKNKWWPKE1YjFlWc6VTEVSN45CklWWf-uWmprQIyLtoPDA18tX9cFDr-aQ9S6/pubhtml) and [covid_19_data.csv](https://www.kaggle.com/sudalairajkumar/novel-corona-virus-2019-dataset#covid_19_data.csv). 

COVID19_line_list_data.csv includes the records of 1085 cases of coronavirus. covid_19_data.csv is the time series data of each day for each city from 22/Jan/2020 to 28/March/2020. 

The files has been uploaded to a [S3 bucket](s3://audacity-capstone-luke/), which  public accessible. 


## Project Objective
The objective of this project is to read data from Amazon S3, clean it and load it on Amazon Redshift, then transfer the data to a pre-defined fact tables and dimension tables. Finally, data quality checks are applied.

The idea is to create dimensions and facts following the `Snowflake` schema as some of the relationships are many-to-many which is not supported by Star Schema.

The outcome is a set of tables that make easier complex queries and at the same time tidy the data.


## Tooling
The tools utilised on this project are the same as we have been learning during the course of this Nanodegree.

- `Amazon S3` for File Storage
- `Amazon Redshift` for Data Storage
- `Apache Airflow` as an Orchestration Tool

Those tools are widely utilised and considered industry standards. The community is massive and the tools provide support to several features.

Apache Airflow, in special, gives freedom to create new plugins and adapt it to any needs that we might have. There are also several plugins available to use.

## Data Model
The final data model include six tables, four dimensions and two facts.

![Data Model](https://audacity-capstone-luke.s3-ap-southeast-2.amazonaws.com/ER.jpg)

The fact tables including:

- `fact_data` stores the number of confirmed cases, the number of recovered people and the number of death every day in each location.
- `fact_cases` has information about cases. 

The dimension tables including:

- `dim_location` stores information about the location of cases.
- `dim_times` has information about times. It makes easier to process aggregation by time.
- `dim_sources` stores information about the source of case information coming from.
- `Patient-Info` has information about the patient in a case.

### Data Dictionary

`dim_location`

Field | Type | PK | FK
------| ----- | ---- | ----
locationid | varchar | Yes
location | varchar
country | varchar | | 

`dim_sources`

Field | Type | PK | FK
------| ----- | ---- | ----
sourceid | varchar | Yes
sourcename | varchar
link | varchar

`dim_times`

Field | Type | PK | FK
------| ----- | ---- | ----
datetime | timestamp | Yes
day | int
month | varchar
year | int
weekday | varchar

`patient_info`

Field | Type | PK | FK
------| ----- | ---- | ----
patientid | varchar | Yes
age | int
gender | varchar
locationid|int||Yes

`fact_data`

Field | Type | PK | FK
------| ----- | ---- | ----
sno| varchar|Yes
observationdate|date
locationid|int||Yes
confirmednumber|int
deathnumber|int
recoverednumber|int

`fact_cases`

Field | Type | PK | FK
------| ----- | ---- | ----
caseid|varchar|Yes|Yes
caseincountry|int
symptoms|varchar
symptonsonsite|date
reportdate|date
hospvisitdate|date
exposurestart|date
exposureend|date
visitingwuhan|varchar
fromwuhan|varchar
death|varchar
recovered|varchar
summary|varchar
sourceid|varchar||Yes


## Scenarios
The following scenarios were requested to be addressed:

1. **The data was increased by 100x.**  Both the Redshift cluster and S3 bucket would have to grow to fufill this requirement.

2. **The pipelines would be run on a daily basis by 7 am every day.** Airflow `DAG`· definitions can be stetted to realise the scheduled trigger.

3. **The database needed to be accessed by 100+ people.** Redshift is scalable so that it can satisfy this scenario.

## Data Pipeline
The Data pipeline is spread into twelve tasks, being:
1. `start_operator` and `end_operator` are just dummy tasks, starting and finishing the execution.
2. `clean_case_csv` is the task to clean the original csv files, including replacing 'NA' value to NULL and formatting date as "YYYY-mm-dd".
3. `stage_cases_to_redshift` are `SubDagOperator` tasks. The Subdag will copy the date from S3 to Redshift as staging tables.
4. `load_cases_table`, `load_patients_table`, `load_data_table`, `load_location_dimension_table`, `load_source_dimension_table` and `load_time_dimension_table` are tasks that will run  sql statement to create and populate the dimension tables and fact tables.
6. `run_quality_checks` will execute Data Quality against the data.

![DAG](https://audacity-capstone-luke.s3-ap-southeast-2.amazonaws.com/pipeline+structure.png)
### Data Clean
The first step is clean the original csv data. One problem of original data is the data formation is irregular and cannot identified as DATA type in Redshift. Another one is some values in the columns of data type are recorded as a string of 'NA' to represent null value. It is also need to be replaced.
### Data Ingestion
The first step is read the data from S3 into Redshift. This is done through the `S3ToRedshiftOperator`. 



That SubDag is dynamically generated according to the configuration file `/dags/configuration/copy_from_s3_to_redshift.py`. It means that if more tasks are needed then all that is required is to add new details to that file.

### Data Processing

The data processing is made exclusively through SQL statements, which is located in`dags/create_tables.sql`  and  `plugs/helplers/sql_queries.sql`. The SQL script will follow the same pattern.
1. Drop the table if exists
2. Create the table
3. Insert the data from a select statement.
One example of sql statement is following:
```sql
CREATE TABLE IF NOT EXISTS public.fact_cases (
    caseid         varchar(256) NOT NULL,
    caseincountry  INT8,
	symptoms       varchar(512),
    symptonsonsite DATE,
    reportdate     DATE,
	hospvisitdate  DATE,
	exposurestart  DATE,
    exposureend    DATE,
	visitingwuhan  varchar(10),
    fromwuhan      varchar(10),
    death          varchar(10),
    recovered      varchar(10),
    summary        varchar(65535),
	sourceid       varchar(256)
);
```
```python
fact_data_table_insert = ("""
        SELECT
                datastage.sno,
                TO_DATE(datastage.observationdate, 'DD/MM/YYYY'),
                locations.locationid,
                CAST(TRIM(datastage.confirmednumber) AS FLOAT8),
                CAST(TRIM(datastage.deathnumber) AS FLOAT8),
                CAST(TRIM(datastage.recoverednumber) AS FLOAT8)
        FROM staging_data AS datastage
        LEFT JOIN dim_locations locations
          ON datastage.state = locations.location
         AND datastage.country = locations.country
    """)
```

## Running the Project
It's assumed that there is an Airflow instance up and running.
- Copy `dags` and `plugins` files to Airflow work environment.
- Create AWS connection: Setup a new connection on Airflow called `aws_credentials` 
- Create Redshift Connection: Setup a new connection on Airflow called `redshift`
- Execute the DAG: Having the configuration finished, then just turn the DAG on and run it manually.

