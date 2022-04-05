from fate_flow.db.db_models import DB, Job, Task


@DB.connection_context()
def insert_job(job_name, job_description,job_id):
    data = Job.update({Job.f_name:job_name, Job.f_description:job_description}).where(Job.f_job_id==job_id).execute()
