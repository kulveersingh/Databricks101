# Blog 10 — Workflows: Replacing Your Cron Jobs for Good
# Exercise 3: Conditional publish gate
# Requires: All three exercises run locally in plain Python — no workspace, no cluster, no cron daemon.

class GatedWorkflow(RepairableWorkflow):
    def add_gated(self, task, gate_fn):
        task.gate_fn = gate_fn
        self.add(task)

    def run(self, resume=False):
        outputs, ok = {}, True
        self._log(f"[{self.name}] RUN started")
        for name in self._order():
            task = self.tasks[name]
            gate = getattr(task, "gate_fn", None)
            if gate and not gate(outputs):
                self._log(f"[{self.name}] GATE BLOCKED task={name}: condition not met, halting")
                ok = False
                break
            if not self._run_task(task, outputs):
                self.status[name] = "failed"
                ok = False
                break
            self.status[name] = "succeeded"
        self._log(f"[{self.name}] RUN {'succeeded' if ok else 'halted'}")
        return ok

def build_pipeline(auc_value):
    gwf = GatedWorkflow("nightly_feature_refresh")
    gwf.add(Task("ingest", lambda out: {"rows": 120_000}))
    gwf.add(Task("validate", lambda out: {"null_rate": 0.001}, depends_on=["ingest"]))
    gwf.add(Task("build_features", lambda out: {"features": 214}, depends_on=["validate"]))
    gwf.add(Task("train", lambda out: {"model": "gbm_v42"}, depends_on=["build_features"]))
    gwf.add(Task("evaluate", lambda out: {"auc": auc_value}, depends_on=["train"]))
    gwf.add_gated(Task("publish", lambda out: {"live": True}, depends_on=["evaluate"]),
                  gate_fn=lambda outputs: outputs["evaluate"]["auc"] >= 0.75)
    return gwf

print("--- passing metric ---")
build_pipeline(auc_value=0.81).run()
print("--- failing metric ---")
build_pipeline(auc_value=0.62).run()
