from __future__ import absolute_import, unicode_literals

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators import BashOperator

# Following are defaults which can be overridden later on
default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'start_date': datetime(2022, 11, 1),
    'email': ['cahau1222@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'msg_for_failure': "DAG 'dummy_data_pipeline' has failed.",
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    dag_id='data_pipeline',
    default_args=default_args,
    schedule_interval="0 * * * *",
    dagrun_timeout=timedelta(minutes=1))

start = BashOperator(
    task_id="start",
    bash_command="echo 'Starting DAG data_pipeline'",
    dag=dag
)

end = BashOperator(
    task_id="end",
    bash_command="echo 'Ending DAG data_pipeline'",
    dag=dag
)

process = BashOperator(
    task_id="process",
    bash_command="echo 'python3 section1_manage.py --task-config section1_process.yaml'",
    dag=dag
)

start >> process >> end
