from flask import Flask
from flask import render_template

import simcloud
import os, logging
import arrow

logging.basicConfig(format='[%(asctime)s] %(levelname)s %(lineno)d %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


app = Flask(__name__)

cache_jifs = None

@app.route('/')
def hello_world():
    return render_template("index.html")


@app.route('/jobs')
def list_jobs():
    client = simcloud.new_client('simcloud-mr2')

    logging.info('[check_jobs] ======= getting job from simcloud =======')
    jifs = client.get_jobs(username=client.get_user_quota().username)

    # sort jobs by created time
    jifs.sort(key=lambda x: arrow.get(x.times.created).timestamp, reverse=True)

    date_format = 'YY-MM-DD HH:mm:ss A'
    for job in jifs:
        # format created, started and completed time
        job.times.created = arrow.get(job.times.created).to('US/Pacific').format(date_format)
        if job.times.get("started", None):
            job.times.started = arrow.get(job.times.started).to('US/Pacific').format(date_format)
        if job.times.get("completed", None):
            job.times.completed = arrow.get(job.times.completed).to('US/Pacific').format(date_format)

        # job finished, add more info to job dict
        if job.times.get("started", None) and job.times.get("completed", None):
            # add total_time to job dict
            job.total_time = arrow.get(job.times.completed, date_format).timestamp - arrow.get(job.times.started, date_format).timestamp
            job.total_time = str(round(job.total_time / 60.0, 2)) + ' minutes'

            # append all exit code to the job.all_exit_code
            job.all_exit_code = []
            for task in job.tasks:
                job.all_exit_code.append(task.exit_code)

            # if any exit code evaluate to be true(!=0), show it, else hide the actual code and show "0".
            if any(job.all_exit_code):
                pass
            else:
               job.all_exit_code = "0"

    return render_template('jobs.html', jobs=jifs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

