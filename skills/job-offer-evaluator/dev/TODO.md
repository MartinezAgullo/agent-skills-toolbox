# job-offer-evaluator: pending tasks

Ordered roughly by value. Tick items off as they are done.

## High
- [ ] **Regional IRPF scales** (Madrid, Cataluña, C. Valenciana, Andalucía, Cantabria) with a warning and state-scale fallback for any other region. Prompt ready in `dev/prompt-irpf-regional-scales.md`.
- [ ] **First end-to-end run on a real offer** with the real profile: fills `~/.claude/job-search/profile.md`, exercises the interview, the `last_verified` flow and the offers log. Use the Grid Dynamics message.
- [ ] **Close the unverified items** listed in `data/tax_es.json` (`unverified`): 2,000 EUR employee work-expenses deduction, employee MEI 0.15%, RETA rates read verbatim from the BOE order (art. 18 and 37), autonomic scale assumption.
- [ ] **Re-read the US figures not verified yet**: Additional Medicare Tax 0.9% and self-employment tax rules (see `data/tax_us.json` `verified_by`).

## Medium
- [ ] **Decide the sync mechanism** between `~/.claude/skills/` and the repo: launchd agent (blocked earlier, needs a Bash permission rule or a manual install), shell alias for `scripts/sync-from-claude.sh`, or a Claude Code hook.
- [ ] **Yearly refresh reminder** (January): create a scheduled task that opens a session running the "Yearly tax-data refresh" procedure in `SKILL.md`.
- [ ] **Automated tests for the tax modules**: known payslips / AEAT and IRS examples as fixtures, so a data refresh cannot silently break results.
- [ ] **Autónomo details not modelled**: reduced first-year cuota (tarifa plana), choosing a base above the tramo minimum, working through an own company (SL / LLC), quarterly IRPF instalments and cash flow.
- [ ] **US refinements**: filing status other than single, 401(k)/HSA contributions, QBI deduction for 1099, per-state tax instead of one average rate.
- [ ] **Use the profile's special regimes**: Beckham / impatriate regime, deductions and dependants are collected in the interview but not used by the script.
- [ ] **Non-EUR current job**: `--current-to-eur` exists, but the interview and docs do not cover it well.

## Low / ideas
- [ ] **More country modules** when offers arrive (Switzerland by canton, UK, Germany, Netherlands). Follow `references/adding-a-country.md`.
- [ ] **Cost-of-living / PPP adjustment** for cross-country offers, since net pay alone does not capture it.
- [ ] **Run the skill-creator evals** (test prompts, trigger-description optimisation) now that the skill is stable.
- [ ] **Validate LinkedIn best-effort fetch**: confirm it fails gracefully and never blocks the flow.
- [ ] **Offers log tooling**: a small script to list or summarise `offers_log.md` (average rate, verdicts per company).
- [ ] **Check the agent config folders** assumed in `SKILL.md` for Codex and Gemini (`~/.codex`, `~/.gemini`); only Claude Code is confirmed.
- [ ] **Spanish version of reply drafts** and CV-language handling, if recruiters write in Spanish.
