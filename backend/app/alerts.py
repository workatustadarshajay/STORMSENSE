"""Demo storm email, sent by Databricks: the button starts a small job, and the job's success email goes to the alert address.

No mail server or password is needed here. The job (`StormSense - Demo storm alert`) only runs when someone clicks,
so it costs nothing otherwise.
"""

from __future__ import annotations


class JobMissing(Exception):
    pass


def start_demo_email(workspace, job_name: str) -> int:
    """Starts the demo email job and returns the run id. Raises JobMissing if the bundle has not been deployed."""
    job = next(iter(workspace.jobs.list(name=job_name)), None)
    if job is None:
        raise JobMissing()
    waiter = workspace.jobs.run_now(job_id=job.job_id)
    return waiter.run_id
