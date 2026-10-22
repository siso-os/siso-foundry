# Research questions

Use `foundry ask <words>` before starting research; it searches questions and domain notes.
Create a question with `foundry question new "<question>" --domain D --asked-by NAME`.
Each `<slug>.md` has `key: value` lines between `---` fences; use `_template.md` as a guide.
Keys: question, domain, asked_by, status, answered, recheck, sources.
Status is `open` or `answered`; dates use YYYY-MM-DD; sources is a comma-separated list.
Write the decision in `## Answer`, citations in `## Evidence`, and gaps in `## Unknown`.
Set recheck when the answer should be revisited; `ask` flags past dates as RECHECK DUE.
