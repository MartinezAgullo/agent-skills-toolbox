# agent-skills-toolbox

A collection of reusable agent skills. Each skill lives in its own folder under `skills/` and is self-contained, so you can copy a single folder into your agent's skills directory without the rest of the repo.

## Skills

| Skill | What it does |
|---|---|
| [job-offer-evaluator](skills/job-offer-evaluator) | Triage a recruiter message or job offer: net take-home comparison (Spain and US), CV fit, conditions, recruiter questions and a reply draft. |

## Install

Clone the repo and symlink the skills you want into your agent's skills folder, for example for Claude Code: `ln -s "$PWD/skills/job-offer-evaluator" ~/.claude/skills/job-offer-evaluator`.

## Personal data

Skills that need personal data (for example salary figures) keep it outside this repo, in the user-level config folder of your agent or in the folder given by an environment variable. Each skill documents its own location in its `SKILL.md`.

## License

MIT, see [LICENSE](LICENSE).
