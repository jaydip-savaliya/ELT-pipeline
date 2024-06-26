from datetime import datetime, timedelta
from docker.types import Mount
from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.docker.operators.docker import DockerOperator


from datetime import datetime, timedelta
from airflow import DAG
from docker.types import Mount
from airflow.operators.python_operator import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
import subprocess

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
}

def run_elt_script():
    script_path = "/opt/airflow/elt_script/elt_script.py"
    result = subprocess.run(["python", script_path],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Script failed with error: {result.stderr}")
    else:
        print(result.stdout)

dag = DAG(
    'elt_and_dbt',
    default_args=default_args,
    description='An ELT workflow with dbt',
    start_date=datetime(2024, 6, 26),
    catchup=False,
)

t1 = PythonOperator(
    task_id='run_elt_script',
    python_callable=run_elt_script,
    dag=dag,
)

t2 = DockerOperator(
    task_id='dbt_run',
    image='ghcr.io/dbt-labs/dbt-postgres:latest',
    command=[
        "run",
        "--profiles-dir",
        "/root",
        "--project-dir",
        "/opt/dbt",
        "--full-refresh"
    ],
    auto_remove=True,
    docker_url="tcp://docker-proxy:2375",
    network_mode="bridge",
    mounts=[
        Mount(source='/home/jaydeep/Downloads/dbt/activate_postgres',
              target='/opt/dbt', type='bind'),
        Mount(source='/home/jaydeep/.dbt', target='/root', type='bind'),
    ],
    dag=dag
)

t3 = BashOperator(
    task_id="Final_task",
    bash_command="echo ELT pipeline build completed",
    dag=dag
)
t1 >> t2 >> t3