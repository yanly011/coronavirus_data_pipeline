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

- `Amazon S3` for File Storage: Amazon Simple Storage Service (Amazon S3) is an object storage service that offers industry-leading scalability, data availability, security, and performance. This means customers of all sizes and industries can use it to store and protect any amount of data for a range of use cases, such as websites, mobile applications, backup and restore, archive, enterprise applications, IoT devices, and big data analytics. Amazon S3 provides easy-to-use management features so you can organize your data and configure finely-tuned access controls to meet your specific business, organizational, and compliance requirements. Amazon S3 is designed for 99.999999999% (11 9's) of durability, and stores data for millions of applications for companies all around the world. S3 can be used to store the original and cleaned data of coronavirus, and the ETL pipeline will connect to the bucket to load the data.
- `Amazon Redshift` for Data Storage: Amazon Redshift is a fully-managed petabyte-scale cloud based data warehouse product designed for large scale data set storage and analysis. It is also used to perform large scale database migrations. It is suitable for OLAP. For this project, we choose Redshift to store the cleaned data and make analysers can get data from different dimensions.
- `Apache Airflow` as an Orchestration Tool: Apache Airflow is an open-source workflow management platform. It is a solution to manage the company's increasing complex workflows. Creating Airflow allowed Airbnb to programmatically author and schedule their workflows and monitor them via the built-in Airflow user interface. 

Those tools are widely utilised and considered industry standards. The community is massive and the tools provide support to several features.

Apache Airflow, in special, gives freedom to create new plugins and adapt it to any needs that we might have. There are also several plugins available to use.

## Data Model
Here, we can assume analysis requirements of coronavirus cases.  
First, we needs a fact table to store information of each case and another one for store the time series cases number to analysis the trend of coronavirus in different regions.
As an analyser, the cases need to be analysis from the dimension of time period(month, day, etc.), and the location (country, city, etc.). Sometimes the source where the cases' information is come from is another dimension for data analysis. It is also very convenient if we want to add some addtional information about these dimension, for example, we can add latitude and longtitude of an region in the dimension table.
The final data model include six tables, four dimensions and two facts.

![Data Model](https://audacity-capstone-luke.s3-ap-southeast-2.amazonaws.com/ER.jpg)

The fact tables including:

- `fact_data` stores the number of confirmed cases, the number of recovered people and the number of death every day in each location.
- `fact_cases` has information about cases. 

The dimension tables including:

- `dim_location` stores information about the location of cases. Note: the red color means we can add these additional data to the model but we have not found these data yet
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

1. **The data was increased by 100x.**  Both the Redshift cluster and S3 bucket would have to grow to fufill this requirement, and they are scalable to satisify huge amount of data. 

2. **The pipelines would be run on a daily basis by 7 am every day.** Airflow `DAG`· definitions can be stetted to realise the scheduled trigger. And the Airflow runs very stable that can make sure the pipeline is running continuously. 

3. **The database needed to be accessed by 100+ people.** Redshift is scalable so that it can satisfy this scenario. With the Concurrency Scaling feature, it can support virtually unlimited concurrent users and concurrent queries, with consistently fast query performance. When concurrency scaling is enabled, Amazon Redshift automatically adds additional cluster capacity when we need it to process an increase in concurrent read queries. Write operations continue as normal on your main cluster. Users always see the most current data, whether the queries run on the main cluster or on a concurrency scaling cluster. You're charged for concurrency scaling clusters only for the time they're in use. 

## Data Pipeline
The Data pipeline is defined by the file of `/dags/etl.py`, including 11 steps:
1. `start_operator` and `end_operator` are just dummy tasks, starting and finishing the execution.
2. `clean_case_csv` is the task to clean the original csv files, including replacing 'NA' value to NULL and formatting date as "YYYY-mm-dd".
3. `stage_cases_to_redshift` are `SubDagOperator` tasks. The Subdag will copy the date from S3 to Redshift as staging tables.
4. `load_cases_table`, `load_patients_table`, `load_data_table`, `load_location_dimension_table`, `load_source_dimension_table` and `load_time_dimension_table` are tasks that will run  sql statement to create and populate the dimension tables and fact tables.
6. `run_quality_checks` will execute Data Quality against the data.

![DAG](https://audacity-capstone-luke.s3-ap-southeast-2.amazonaws.com/pipeline+structure.png)
### Data Clean
The first step is clean the original csv data. One problem of original data is the data formation is irregular and cannot identified as DATA type in Redshift. Another one is some values in the columns of data type are recorded as a string of 'NA' to represent null value. It is also need to be replaced. The file of `/plugins/operators/clean_csv_file.py` defines the logic of data clean:
```python
    def execute(self, context):
        self.log.info('Clean csv file starts')
        aws_hook = AwsHook(self.aws_credentials_id)
        credentials = aws_hook.get_credentials() 
        rendered_key = self.s3_key.format(**context)
        s3_path = "s3://{}/{}".format(self.s3_bucket, rendered_key)
        self.log.info("Download data from S3: " + str(s3_path))
        s3 = boto3.client('s3', aws_access_key_id=credentials.access_key, aws_secret_access_key=credentials.secret_key)
        obj = s3.get_object(Bucket=self.s3_bucket, Key=self.s3_key)
        df = pd.read_csv(io.BytesIO(obj['Body'].read()), index_col=False)
        df = df.replace(to_replace ="NA",  value ="")
        df = df.fillna(value="")
        for col in self.datecols:
            df[col] = df[col].apply(dateformatter) 
        
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        s3_resource = boto3.resource('s3', aws_access_key_id=credentials.access_key, aws_secret_access_key=credentials.secret_key)
        s3_resource.Object(self.s3_bucket, rendered_key).put(Body=csv_buffer.getvalue())
```
### Data Ingestion
The first step is read the data from S3 into Redshift. This is done through the `/plugins/operators/S3ToRedshiftOperator`. 
```python
     def execute(self, context):
        self.log.info('StageToRedshiftOperator starts')
        aws_hook = AwsHook(self.aws_credentials_id)
        credentials = aws_hook.get_credentials() 
        redshift = PostgresHook(postgres_conn_id=self.redshift_conn_id)
        
        self.log.info("Clearing data from destination Redshift table")
        redshift.run("DELETE FROM {}".format(self.table))
        
        self.log.info("Copying data from S3 to Redshift")
        rendered_key = self.s3_key.format(**context)
        s3_path = "s3://{}/{}".format(self.s3_bucket, rendered_key)
        formatted_sql = StageToRedshiftOperator.copy_sql.format(
            self.table,
            s3_path,
            credentials.access_key,
            credentials.secret_key,
            self.region
        )
        redshift.run(formatted_sql)
```
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
### Data Quality Check
The file of `/plugins/operators/data_quality.py` is responsible for data quality check. It will check how many records in the fact tables and dimension tables in Redshift database:
```python
    def execute(self, context):
        self.log.info('DataQualityOperator starts')
        redshift_hook = PostgresHook("redshift")
        for table in self.tables:
            records = redshift_hook.get_records(f"SELECT COUNT(*) FROM {table}")
            if len(records) < 1 or len(records[0]) < 1:
                raise ValueError(f"Data quality check failed. {table} returned no results")
            num_records = records[0][0]
            self.log.info(f"Data quality on table {table} check passed with {records[0][0]} records")
```

## Running the Project
It's assumed that there is an Airflow instance up and running.
- Copy `dags` and `plugins` files to Airflow work environment.
- Create AWS connection: Setup a new connection on Airflow called `aws_credentials` 
- Create Redshift Connection: Setup a new connection on Airflow called `redshift`
- Execute the DAG: Having the configuration finished, then just turn the DAG on and run it manually.

