---
name: sk-help
description: Show available sk-harness skills and their purpose
argument-hint: "[command]"
---

```bash
sk --help
```

Also available as slash commands inside Claude Code:

| Command | Purpose |
|---------|---------|
| `/sk-init [name]` | Bootstrap .skspec/ |
| `/sk-constitution` | Ratify project principles |
| `/sk-specify [--accept\|--reject]` | PRD draft / amend / accept proposal |
| `/sk-clarify` | Clarify requirements via Q&A |
| `/sk-plan` | Draft ERD (architect) |
| `/sk-tasks [list\|show\|graph\|retry]` | Decompose or inspect tasks |
| `/sk-analyze` | Cross-doc consistency check |
| `/sk-checklist` | Generate validation checklist |
| `/sk-go [--until-pause]` | Start TPM loop |
| `/sk-pause` | Pause after current batch |
| `/sk-resume` | Clear pause flag |
| `/sk-step` | Run exactly one batch |
| `/sk-review` | Manual review trigger |
| `/sk-status` | Progress summary |
| `/sk-log [N]` | Tail decision log |
| `/sk-iteration <list\|complete>` | Iteration lifecycle |
| `/sk-agent <list\|add\|remove>` | Agent roster management |
| `/sk-tasks-retry <id>` | Reset failed task |
| `/sk-config <show\|set>` | View/edit configuration |
