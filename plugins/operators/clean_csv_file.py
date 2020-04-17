from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.contrib.hooks.aws_hook import AwsHook
import io
import boto3
import pandas as pd
from io import StringIO
import time
import datetime

def dateformatter(unformatteddate):
    timestring = unformatteddate.strip()
    if(unformatteddate == ''):
        return ''
    else:
        try:
            timeArray = time.strptime(timestring, "%Y-%m-%d")
            return timestring
        except ValueError:
            if(len(timestring.split('/')[-1]) > 2):
                try:
                    timeArray = time.strptime(timestring, "%m/%d/%Y")
                except ValueError:
                    return ''
            else:
                try: 
                    timeArray = time.strptime(timestring, "%m/%d/%y")
                except ValueError:
                    return ''    
            return time.strftime("%Y-%m-%d", timeArray) 
        
class CleanCsvOperator(BaseOperator):
    ui_color = '#358140'
   
    @apply_defaults
    def __init__(self,
                 # Define your operators params (with defaults) here
                 # Example:
                 # redshift_conn_id=your-connection-name
                 aws_credentials_id="",
                 s3_bucket="",
                 s3_key="",
                 region="",
                 datecols = [],
                 *args, **kwargs):

        super(CleanCsvOperator, self).__init__(*args, **kwargs)
        # Map params here
        # Example:
        # self.conn_id = conn_id
        self.aws_credentials_id = aws_credentials_id
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.region = region
        self.datecols = datecols
        
        
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
