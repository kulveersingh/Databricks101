# AI Agents on Databricks: Tools, Memory, and Governance That Holds Up

An LLM that can only talk is a chatbot. In this post you'll learn how to turn one into an agent that plans, calls tools, and acts on your data — built on Unity Catalog functions so every tool call inherits permissions, gets audited, and stays inside a governed sandbox. Through a concrete example (a weekly sales-report agent), you'll see the plan → tool call → observe loop, how memory works across and within runs, and the guardrails — sandboxed tools, loop caps, audit logs — that make an agent production-safe.

![Architecture diagram](./diagram.png)

The diagram shows the agent loop: a user request enters the loop, the LLM plans the next action, invokes a Unity Catalog function tool (`sales.weekly_by_segment`, `sales.vs_forecast`, `reports.draft_section`, `reports.save_draft`), observes the result, and either loops or produces the final answer — running until the answer is ready or the iteration cap hits. Around the loop sit three pillars: memory (short-term run context plus long-term facts in Delta/Vector Search, read as just another tool call), tools (Unity Catalog functions), and governance (permission inheritance so the agent can't exceed the user's grants, sandboxed read-only tools with human approval for writes, and loop caps plus audit logs) — enforcing the loop so the constraints become the feature.

## Concepts covered

1. **The agent loop: plan → tool call → observe.** Every agent runs the same cycle: the LLM decides the next action, a tool executes it (the LLM never touches data directly), the output returns to context, and the agent repeats or answers. The loop is simple — the engineering is in the tools, memory, and guardrails around it.
2. **Unity Catalog functions as tools.** Register the agent's tools as SQL/Python functions in Unity Catalog with explicit grants. The LLM decides *when* to call a function; Unity Catalog decides *whether it's allowed to* — buying permission inheritance, audit logging, and versioning for free.
3. **Permission inheritance.** The agent never has more access than the human driving it: if the caller lacks SELECT on a table, the tool call fails exactly like a direct query would. This single property eliminates an entire class of "agent exfiltrated data" incidents.
4. **Short-term vs. long-term memory.** Short-term memory is the current run's context — requests, tool calls, observations — kept within context limits by summarizing older steps rather than blindly appending. Long-term memory is facts that persist across sessions (e.g., "Midwest means these 12 states"), stored in a Delta table or Vector Search index and read as just another tool call.
5. **Sandboxing the blast radius.** Tools are read-only by default; anything that writes, sends, or changes state gets narrower grants, argument validation, and ideally a human-approval step for irreversible actions. The Northwind agent can *draft* reports but can't *send* them — that one missing tool does enormous safety work.
6. **Loop caps and audit logs.** Cap tool-call iterations (10–15 is plenty) and set timeouts so a stuck agent becomes a failed run you investigate, not an infinite loop burning tokens at 3 AM. Log reasoning traces to a Delta table and review samples weekly — this is how you catch bad habits before they become expensive ones.
7. **Evaluate the agent, not just the model.** An agent is a system — model + tools + prompts + memory. Test it end-to-end on realistic tasks with expected tool-call sequences. "The model is smart" tells you nothing about whether the agent reliably picks the right tool.
8. **When agents are the wrong call.** Fixed pipelines with unchanging steps belong in Workflows, not agents. Anything consequential and irreversible needs a human in the loop until evals are overwhelming. And if your tables and functions lack proper grants, an LLM on top multiplies the mess — fix Unity Catalog first, then add the agent.

## Hands-on exercises

These three build Northwind's report agent at small scale on Free Edition. Unity Catalog functions work on serverless compute, but the `system.access` audit tables are premium — so exercise 3 has you keep your own trace log, which is the habit that matters anyway.

1. **Build the governed tool.** Create a `sales` schema with a synthetic `customer_monthly` table, register `sales.weekly_by_segment` as a Unity Catalog function, grant EXECUTE to the `analysts` group, and use `SHOW GRANTS` to verify exactly who can execute it — then call it through a small agent step for the Midwest.
2. **Run the loop with memory and a missing tool.** Build a retail ops agent for store 42 with three tools — `stock_level`, `read_memory` (long-term memory in a Delta table), and `draft_note` — and deliberately *no* ordering tool. Implement the loop with a 10-iteration cap and step-history summarization, draft reorder notes for below-threshold SKUs, and log every step to a trace table.
3. **Red-team the sandbox.** Probe the agent with three attacks: ask it to email a report (no such tool), pull West-coast numbers (no grant), and answer a query with no tool available (verify the loop cap stops it). Every step goes to the trace table, and each refusal must state a reason.

## Solutions

- `solution-1-the-governed-tool-py.py` — Generates the synthetic sales table in Python and runs the agent's tool-call step for the Midwest region.
- `solution-1-the-governed-tool-sql.sql` — Creates `sales.weekly_by_segment`, grants EXECUTE to `analysts`, and verifies the security boundary with `SHOW GRANTS`.
- `solution-2-the-loop-memory-and-the-missing-tool.py` — Implements the plan → tool call → observe loop with an iteration cap, short-term memory summarization, Delta-backed long-term memory, and full trace logging — with no ordering tool in the sandbox.
- `solution-3-red-teaming.py` — Runs the three red-team probes (missing email tool, denied West-coast grant, unanswerable query against the loop cap) and prints the logged refusals with reasons.

## Prerequisites

- Databricks Free Edition — Unity Catalog functions work on serverless compute; all data is synthetic and generated in the notebook.
- Note: the `system.access` audit tables are a premium feature, so the exercises keep their own `agent.trace_log` Delta table instead — the habit that matters anyway.
- Familiarity with Unity Catalog grants and schemas (blog 5), since the grant — not the prompt — is the security boundary here.
