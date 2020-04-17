from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators import (StageToRedshiftOperator, LoadFactOperator,
                                LoadDimensionOperator, DataQualityOperator, CleanCsvOperator, PostgresOperator)
from helpers import SqlQueries

# AWS_KEY= os.environ.get('AWS_KEY')
# AWS_S ECRET = os.environ.get('AWS_SECRET')


default_args = {
    'owner': 'udacity',
    'start_date': datetime(2020, 3, 28),
    'depends_on_past': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
    'email_on_retry': False
}

dag = DAG('udac_capstone_project',
          default_args=default_args,
          description='Load and transform data in Redshift with Airflow',
          start_date=datetime.now(),
          schedule_interval='0 * * * *'
        )

start_operator = DummyOperator(task_id='Begin_execution',  dag=dag)

clean_data_csv = CleanCsvOperator(
    task_id="clean_data_csv",
    dag=dag,
    aws_credentials_id='aws_credentials',
    s3_bucket='audacity-capstone-luke',
    s3_key='covid_19_data.csv',
    region='ap-southeast-2',
    datecols=[]
)

clean_case_csv = CleanCsvOperator(
    task_id="clean_case_csv",
    dag=dag,
    aws_credentials_id='aws_credentials',
    s3_bucket='audacity-capstone-luke',
    s3_key='COVID19_line_list_data.csv',
    region='ap-southeast-2',
    datecols=['reporting date', 'symptom_onset', 'hosp_visit_date', 'exposure_start', 'exposure_end']
)

create_tables = PostgresOperator(
    task_id="create_tables",
    dag=dag,
    postgres_conn_id="redshift",
    sql="create_tables.sql"
)


stage_cases_to_redshift = StageToRedshiftOperator(
    task_id='Stage_cases',
    dag=dag,
    redshift_conn_id='redshift',
    aws_credentials_id='aws_credentials',
    table='staging_cases',
    s3_bucket='audacity-capstone-luke',
    s3_key='COVID19_line_list_data.csv',
    region='ap-southeast-2' 
)

stage_data_to_redshift = StageToRedshiftOperator(
    task_id='Stage_data',
    dag=dag,
    redshift_conn_id='redshift',
    aws_credentials_id='aws_credentials',
    table='staging_data',
    s3_bucket='audacity-capstone-luke',
    s3_key='covid_19_data.csv',
    region='ap-southeast-2'
)


load_cases_table = LoadFactOperator(
    task_id='Load_cases_fact_table',
    dag=dag,
    redshift_conn_id='redshift',
    table='fact_cases',
    select_sql=SqlQueries.fact_cases_table_insert
)

load_patients_table = LoadFactOperator(
    task_id='Load_patients_fact_table',
    dag=dag,
    redshift_conn_id='redshift',
    table='patientinfo',
    select_sql=SqlQueries.patient_info_table_insert
)

load_data_table = LoadFactOperator(
    task_id='Load_data_fact_table',
    dag=dag,
    redshift_conn_id='redshift',
    table='fact_data',
    select_sql=SqlQueries.fact_data_table_insert
)

load_location_dimension_table = LoadDimensionOperator(
    task_id='Load_location_dim_table',
    dag=dag,
    redshift_conn_id='redshift',
    table='dim_locations',
    cols='(location, country)',
    select_sql=SqlQueries.dim_location_table_insert
)

load_source_dimension_table = LoadDimensionOperator(
    task_id='Load_source_dim_table',
    dag=dag,
    redshift_conn_id='redshift',
    table='dim_sources',
    cols='(sourcename, link)',
    select_sql=SqlQueries.dim_sources_table_insert
)

load_time_dimension_table = LoadDimensionOperator(
    task_id='Load_time_dim_table',
    dag=dag,
    redshift_conn_id='redshift',
    table='dim_times',
    cols='',
    select_sql=SqlQueries.time_table_insert
)

run_quality_checks = DataQualityOperator(
    task_id='Run_data_quality_checks',
    dag=dag,
    redshift_conn_id='redshift',
    tables=["fact_cases", "fact_data", "patientinfo", "dim_locations", "dim_times", "dim_sources"]
)

end_operator = DummyOperator(task_id='Stop_execution',  dag=dag)
 
start_operator >> create_tables
create_tables >> clean_case_csv >> stage_cases_to_redshift 
create_tables >> clean_data_csv >> stage_data_to_redshift 
stage_cases_to_redshift >> load_location_dimension_table 
stage_data_to_redshift >> load_location_dimension_table
stage_cases_to_redshift >> load_source_dimension_table
load_location_dimension_table >> load_patients_table
load_source_dimension_table >> load_cases_table
load_location_dimension_table >> load_data_table
load_data_table >> load_time_dimension_table
load_cases_table >> load_time_dimension_table
load_patients_table >> load_time_dimension_table
load_time_dimension_table >> run_quality_checks
run_quality_checks >> end_operator
