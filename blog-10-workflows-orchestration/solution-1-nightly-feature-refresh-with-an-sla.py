# Blog 10 — Workflows: Replacing Your Cron Jobs for Good
# Exercise 1: Nightly feature refresh with an SLA
# Requires: All three exercises run locally in plain Python — no workspace, no cluster, no cron daemon.

import random, time
from datetime import datetime, timedelta

class TaskFailed(Exception):
    pass

class Task:
    def __init__(self, name, fn, depends_on=None, max_retries=0,
                 retry_backoff_s=2, timeout_s=600):
        self.name = name
        self.fn = fn
        self.depends_on = depends_on or []
        self.max_retries = max_retries
        self.retry_backoff_s = retry_backoff_s
        self.timeout_s = timeout_s
        self.output = None

class Workflow:
    def __init__(self, name, sla_deadline=None):
        self.name = name
        self.tasks = {}
        self.sla_deadline = sla_deadline
        self.history = []  # run history: every attempt is recorded

    def add(self, task):
        self.tasks[task.name] = task

    def _log(self, msg):
        line = f"{datetime.now().isoformat(timespec='seconds')} {msg}"
        self.history.append(line)
        print(line)

    def _run_task(self, task, outputs):
        attempt = 0
        while True:
            attempt += 1
            self._log(f"[{self.name}] START task={task.name} attempt={attempt}")
            start = time.time()
            try:
                out = task.fn(outputs)
                elapsed = time.time() - start
                if elapsed > task.timeout_s:
                    raise TaskFailed(f"timeout after {elapsed:.1f}s (limit {task.timeout_s}s)")
                task.output = out
                outputs[task.name] = out
                self._log(f"[{self.name}] SUCCESS task={task.name} elapsed={elapsed:.1f}s")
                return True
            except TaskFailed as e:
                self._log(f"[{self.name}] FAILED task={task.name} attempt={attempt}: {e}")
                if attempt > task.max_retries:
                    return False
                wait = task.retry_backoff_s * attempt
                self._log(f"[{self.name}] RETRY task={task.name} in {wait}s")
                time.sleep(wait)

    def _order(self):
        ordered, visited = [], set()
        def visit(name):
            if name in visited:
                return
            for dep in self.tasks[name].depends_on:
                visit(dep)
            visited.add(name)
            ordered.append(name)
        for name in self.tasks:
            visit(name)
        return ordered

    def run(self):
        outputs, ok = {}, True
        self._log(f"[{self.name}] RUN started")
        for name in self._order():
            task = self.tasks[name]
            if not self._run_task(task, outputs):
                ok = False
                break  # downstream tasks never run on bad data
        if self.sla_deadline and datetime.now() > self.sla_deadline:
            self._log(f"[{self.name}] SLA MISS: finished after deadline {self.sla_deadline.isoformat(timespec='seconds')}")
        else:
            self._log(f"[{self.name}] SLA OK")
        self._log(f"[{self.name}] RUN {'succeeded' if ok else 'failed'}")
        return ok
# --- next cell ---

random.seed(7)

def flaky_bureau_api():
    if random.random() < 0.5:
        raise TaskFailed("bureau API transient timeout")
    return {"rows": 120_000}

wf = Workflow("nightly_feature_refresh",
              sla_deadline=datetime.now() + timedelta(seconds=60))
wf.add(Task("ingest", lambda out: flaky_bureau_api(),
            max_retries=3, retry_backoff_s=1))
wf.add(Task("validate", lambda out: {"null_rate": 0.001}, depends_on=["ingest"]))
wf.add(Task("build_features", lambda out: {"features": 214}, depends_on=["validate"]))
wf.add(Task("train", lambda out: {"model": "gbm_v42"}, depends_on=["build_features"]))
wf.add(Task("evaluate", lambda out: {"auc": 0.81}, depends_on=["train"]))
wf.add(Task("publish", lambda out: {"live": True}, depends_on=["evaluate"]))

wf.run()
# --- next cell ---

def slow_build(outputs):
    time.sleep(65)  # blows the 60s SLA deadline
    return {"features": 214}

wf2 = Workflow("nightly_feature_refresh_slow",
               sla_deadline=datetime.now() + timedelta(seconds=60))
for t in wf.tasks.values():
    fn = slow_build if t.name == "build_features" else t.fn
    wf2.add(Task(t.name, fn, depends_on=t.depends_on,
                 max_retries=t.max_retries, timeout_s=t.timeout_s))
wf2.run()  # watch for the SLA MISS line
