#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

from fate_flow.db.db_models import DB, Job, Task

@DB.connection_context()
def insert_job(job_name, job_description,job_id):
    data = Job.update({Job.f_name:job_name, Job.f_description:job_description}).where(Job.f_job_id==job_id).execute()


# @DB.connection_context()
# def list_job_intersection(page, page_length):
#     jobs = Job.select().paginate(int(page), int(page_length))
#     inter_list = []
#     for job in jobs:
#         if list(job.f_dsl["components"].keys())[-1] == "intersection_0":
#             inter_list.append(job)
#     return inter_list

@DB.connection_context()
def list_job_intersection(page, page_length):
    jobs = Job.select().order_by(Job.f_create_time.desc())
    inter_list = []
    for job in jobs:
        if list(job.f_dsl["components"].keys())[-1] == "intersection_0":
            inter_list.append(job)
    a=paginate_data(int(page), int(page_length), inter_list)
    return a

@DB.connection_context()
def list_job_intersection_count():
    jobs = Job.select()
    inter_list = []
    for job in jobs:
        if list(job.f_dsl["components"].keys())[-1] == "intersection_0":
            inter_list.append(job)
    count=len(inter_list)
    return count

def paginate_data(page_num, per_page_data,inter_list):
    view_data = []
    view_data_count = 0
    stat_index = (page_num - 1) * per_page_data
    end_index = page_num * per_page_data
    for inter in inter_list:
        if stat_index <= view_data_count < end_index:
            view_data.append(inter)
        if view_data_count >= end_index:
            break
        view_data_count += 1
    return view_data