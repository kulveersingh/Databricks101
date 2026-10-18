# Blog 10 — Workflows: Replacing Your Cron Jobs for Good
# Exercise 2: Repair from the failed task
# Requires: All three exercises run locally in plain Python — no workspace, no cluster, no cron daemon.

class RepairableWorkflow(Workflow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = {}  # task name -> "succeeded" | "failed"

    def run(self, resume=False):
        outputs, ok = {}, True
        mode = "REPAIR" if resume else "RUN"
        self._log(f"[{self.name}] {mode} started")
        for name in self._order():
            task = self.tasks[name]
            if resume and self.status.get(name) == "succeeded":
                self._log(f"[{self.name}] SKIP task={name} (already succeeded)")
                outputs[name] = task.output  # reuse prior output
                continue
            if not self._run_task(task, outputs):
                self.status[name] = "failed"
                ok = False
                break
            self.status[name] = "succeeded"
        self._log(f"[{self.name}] {mode} {'succeeded' if ok else 'failed'}")
        return ok

    def repair(self):
        return self.run(resume=True)
# --- next cell ---

threshold = {"min_auc": 0.90}  # misconfigured: real AUC is 0.81

def evaluate(outputs):
    auc = 0.81
    if auc < threshold["min_auc"]:
        raise TaskFailed(f"auc {auc} below threshold {threshold['min_auc']}")
    return {"auc": auc}

rwf = RepairableWorkflow("nightly_feature_refresh")
rwf.add(Task("ingest", lambda out: {"rows": 120_000}))
rwf.add(Task("validate", lambda out: {"null_rate": 0.001}, depends_on=["ingest"]))
rwf.add(Task("build_features", lambda out: {"features": 214}, depends_on=["validate"]))
rwf.add(Task("train", lambda out: {"model": "gbm_v42"}, depends_on=["build_features"]))
rwf.add(Task("evaluate", evaluate, depends_on=["train"]))
rwf.add(Task("publish", lambda out: {"live": True}, depends_on=["evaluate"]))

rwf.run()                      # fails at evaluate
threshold["min_auc"] = 0.75    # the fix
rwf.repair()                   # resumes at evaluate; ingest..train skipped
