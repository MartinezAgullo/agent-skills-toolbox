---
name: job-offer-evaluator
description: Evaluate a job offer or recruiter message (LinkedIn, email, headhunter) for the user. Interviews them about their current package, estimates NET take-home pay for the current job and the offer (local social security, income tax, autónomo costs for B2B), checks fit against their CV, scores conditions (remote, benefits, career trajectory), proposes the 2-3 recruiter questions that matter, and drafts the reply (decline or ask for details). Use whenever the user pastes a recruiter message, a job description, or asks "is this role worth it / I got an offer / LinkedIn message", even if they do not say "evaluate".
---

# Job offer evaluator

The user gets recruiter messages regularly and wants the same triage each time: is the role a fit, are the real (net) conditions better than what they have, what should they ask, and what should they reply. Gross figures across contract types and countries mislead, so the core of this skill is a net take-home comparison built from facts the user gives you, never from facts you remember or assume.

## Step 0: Load context

Personal data lives outside the skill, so updating, copying or publishing the skill never exposes or overwrites it. Resolve the data folder `<data_dir>` once, in this order:

1. `$JOB_SEARCH_DIR`, if set.
2. `job-search/` inside the user-level config folder of the agent you are running in: `~/.claude/job-search/` for Claude Code, `~/.codex/job-search/` for Codex CLI, `~/.gemini/job-search/` for Gemini CLI. For any other agent, use the equivalent user-level folder.

Never use a folder inside the skill or inside a project repo. If `<data_dir>` does not exist, create it, copy `templates/profile.md` and `templates/offers_log.md` from this skill into it, and tell the user which path you used.

1. **CV.** Read `cv_path` from `<data_dir>/profile.md`. If it is `?`, missing, or the file is not found, ask the user for a CV (path or pasted text) and store the path in the profile; do not evaluate fit without one. The CV is the source of truth for skills and seniority; do not invent experience.
2. **LinkedIn (optional, best effort).** LinkedIn usually blocks automated reads behind a login wall, so try the `linkedin` URL from the profile once if there is one, and if it is blocked, skip it silently. Only ask the user for a pasted profile or PDF export when something in the offer depends on it (e.g. recruiter claims about their profile, or the CV lacks something the role needs). The CV stays primary; LinkedIn is only a cross-check of what the recruiter saw.
3. **Profile.** Read `<data_dir>/profile.md` (see Step 1).
4. **Past offers.** Skim `<data_dir>/offers_log.md`. Mention it if the same company or recruiter appears again, or if the pay compares usefully with earlier offers.

## Step 1: Confirm or interview (ask, don't assume)

Salary figures and conditions change, and a wrong assumption silently ruins the comparison.

- **Profile has values and `last_verified` exists:** show a compact summary of the stored details and ask the user to confirm them or say what changed. Ask a question only for fields marked `?` or that they correct. If `last_verified` is older than 6 months, say so and walk through the fields more carefully.
- **Profile is empty or missing (first run):** run the full interview below, then write the answers to `<data_dir>/profile.md` and set `last_verified` to today.
- After any change, update `profile.md` (keep the existing layout) so the next run is a quick confirmation.

Send questions as one grouped message (use your structured-question tool if the agent has one), together with any offer details that are missing.

**1. Financial baseline and contract structure**
- Current gross base salary and annual target bonus/variable (and how reliably it pays out).
- Contract type, in their own words (indefinido, autónomo, B2B, W-2, 1099, EOR...). Map it to one of the two statuses in `references/terminology.md`: `employee` or `self_employed`. Read that file when the wording is unclear; "B2B", "freelance", "contractor" and "autónomo" are all `self_employed`.
- Payment installments (12 or 14). This changes monthly cash flow, not annual net, but matters when comparing monthly figures.

**2. Location and tax context**
- Country and city/region where they are taxed now, and where they would be taxed under the offer (rates differ by Spanish autonomous community, Swiss canton, US state, etc.).
- **Spain: ask for the community of FISCAL RESIDENCE**, i.e. where they live on 31 December (the one that sets the IRPF autonomic scale). It is NOT where the job is located nor where the employer is registered: a Madrid-based company hiring someone who lives in Cantabria is taxed with Cantabria's scale. Ask it separately for the current job and for the offer, and if the offer means moving, use the community they would live in. If they only name a city, map it to its community and say so. A remote job does not change the rule.
- Any special regime or deduction (Beckham/impatriate regime, disability, dependents, mortgage, regional deductions).

**3. Benefits and out-of-pocket costs**
- Non-cash benefits now: private health insurance, pension matching, meal vouchers, transport subsidy, stock, training budget, each with an approximate yearly EUR value.
- Work-related costs they pay themselves: uncompensated commuting, equipment, coworking.

**4. Work style and cost impact**
- Current work model (100% remote, hybrid with days per week, in-office) and their preferred model with how much office they would tolerate.
- If hybrid or in-office: monthly commuting cost and weekly commuting time.

**5. Decision threshold**
- The minimum net uplift that would make a move worth it, e.g. "+15% effective net" (suggest around +15-20% for a job change, higher for B2B or less stable offers, and let them override it). Ask about hard dealbreakers (on-site, contractor-only, specific sector).

Per offer (never stored in the profile): for self-employed/hourly offers (often called B2B), realistic billable hours per year and expected gaps between contracts; for non-EUR pay, the FX rate (Step 2 fetches it).

## Step 2: Net take-home comparison

Compare net, not gross, for the current job and the offer. Net means after social security, income tax, and for self-employed work the self-employment costs (cuota de autónomos, gestor, insurance). Then add the yearly value of non-cash benefits and subtract out-of-pocket work costs to get an **effective net**.

- **FX:** for non-EUR offers run `python3 scripts/fetch_fx.py USD` (ECB rate via frankfurter.dev) and use that rate, quoting the date. If the lookup fails, ask the user for a rate.
- **Run the script:** `python3 scripts/net_compare.py` (see `--help`). The current job is taxed in `--country`, the offer in `--offer-country` (default: the same). It takes the current contract type, gross (including expected variable), benefits, extra costs, regional adjustment and offer details, and prints net, effective net (in EUR), delta and, with `--threshold`, whether the uplift clears the bar. For Spain, `--region` is the community of fiscal residence of the current job and `--offer-region` the one under the offer (default: same as `--region`). `--irpf-shift` (alias `--region-adjust`) and `--offer-region-adjust` are optional manual adjustments for the current and offer country (see below); say what you passed.
  - **Spain (ES):** IRPF is the state scale (art. 63 Ley 35/2006) plus the community's own autonomic scale, from `data/tax_es_regions.json`. Real 2026 scales exist for `madrid`, `cataluna`, `comunitat_valenciana`, `andalucia` and `cantabria` (accents and common aliases such as "Catalunya", "Valencia" or "Comunidad Valenciana" are accepted), including the community's own general personal minimum where it sets one. Regional deductions (rent, children, etc.) are NOT modelled; each region's `notes` lists what is left out. `--irpf-shift` is now only an OPTIONAL manual tweak: percentage points added to every rate of the autonomic scale on top of `--region` (e.g. -0.005); leave it at 0 when the region has data.
  - **Spain, community without data:** any other community, the foral regimes (País Vasco, Navarra), Ceuta, Melilla, or no `--region` at all do not fail. The script uses the state scale doubled as the combined scale (the old approximation) and prints a visible `WARNING` such as "No hay datos de la comunidad '<X>'. Se usa la escala estatal sin los detalles específicos de la comunidad (tramos, tipos y deducciones autonómicas); el resultado es una aproximación." Always repeat that warning to the user next to the numbers and label the Spanish net an approximation; if the community matters for the decision, say the real scale is missing and offer to add it (see the refresh procedure).
  - **United States (US):** federal only, single filer, standard deduction, no 401(k)/HSA, no QBI deduction. The adjustment is the user's average state income tax rate (0 for TX/FL/WA, ask for the state otherwise). For 1099 work include self-paid health insurance in `--expenses`; for W-2 offers put the employer's health coverage and 401(k) match into `--offer-benefits`.
  - **Currencies:** offer amounts are in the offer country's currency. `--fx` converts the pay currency into that currency (USD pay taxed in Spain: `--fx 0.89`), and `--to-eur` converts the offer country's currency to EUR (USD pay taxed in the US: `--fx 1 --to-eur 0.89`). Benefits and extra costs are always EUR.
- **Tax modules:** country rules live in `scripts/tax/<cc>.py` with their numbers in `data/tax_<cc>.json`; Spain (ES) and the United States (US) exist. For other countries (Switzerland, UK, etc.) estimate net manually from current tax bands and social-security rules (web search for current-year figures), show the main steps, and label it a rough estimate. If offers from that country keep coming, suggest building a module (`references/adding-a-country.md`).
- **Staleness check:** `net_compare.py` prints a `WARNING` when the tax data is out of date or unverified, including items still unverified for the chosen Spanish community (or its scale being for an earlier year). When you see it, tell the user and offer the refresh procedure below before relying on the numbers.
- Always state the assumptions used: FX rate, billable hours, expenses, community of fiscal residence (or that none was available), tax year. Say the result is an estimate and a gestor/tax advisor should confirm it for a real decision.
- For self-employed (B2B) offers, the net still ignores what an employee gets for free: paid vacation, paid sick leave, unemployment protection, pension accrual, employer contributions. Give the "equivalent employee gross" and flag contract risks (single client, notice terms, false self-employment risk, exclusivity).

## Step 3: Fit and conditions

**Fit (CV vs role).** Score out of 10 with one line of why. List matches (with CV evidence), gaps (real vs merely unlisted), and the likely real day-to-day and seniority versus their current role. Recruiter job titles often hide narrower work than they advertise, so say what the role probably is.

**Conditions** (priority: net pay > remote > trajectory). Use `references/benefits-checklist.md` for the benefits list, and mark each item stated / statutory default / unknown:
- Pay and benefits (health, retirement matching, paid time off, sick leave, parental leave), especially for roles outside Spain where statutory defaults differ.
- Work mode against their stated preference, plus timezone overlap and travel.
- Career trajectory: growth path, ownership, company and client reputation, whether the work builds toward the `target_roles_and_topics` in the profile or away from them, stability of the engagement.

**Recruiter-side signals.** Read the message itself using `references/recruiter-signals.md` (hidden end client, templated outreach, "up to" salaries, contract form vs role, scope vs title) and list the flags and good signs found. Optionally search the web for the company and end client reputation.

## Step 4: Verdict, questions, reply

- **Verdict**: Pursue, Ask first, or Decline, with the 2-3 reasons that decided it, explicitly checked against their threshold and dealbreakers.
- **Questions for the recruiter**: only the 2-3 whose answers could flip the decision (usually real pay structure and paid-time-off terms, actual scope and team, contract duration and termination terms). No generic filler.
- **Reply draft**, once the decision is clear or the user states it, in the recruiter's language, short, in the user's voice. Decline: thank them, optionally one line of reason. Ask for details: conditional interest plus the questions; do not reveal their current salary (offer a target range instead if useful). If still undecided, offer both drafts briefly. One paragraph is one line (no hard wraps) and use dashes sparingly.

## Step 5: Log the offer

After the verdict, append one row to `<data_dir>/offers_log.md` (Date, Company and end client, Role, Contract, Pay offered, Effective net delta, Fit, Verdict, Outcome/comments). Ask before writing if the user has not said to log it. Later, when they tell you what happened (replied, declined, interview), update that row's Outcome.

## Yearly tax-data refresh

Each `data/tax_<cc>.json` holds that country's income tax scale, social-security or payroll rates and caps, and deductions (Spain also the autónomo cuota table), with `tax_year`, `verified_on` and `verified_by`. For Spain the state scale is in `data/tax_es.json` (`irpf_state_scale`) and each community's autonomic scale, personal minimum, sources, `unverified` list and `notes` (what is not modelled) are in `data/tax_es_regions.json`. Numbers go stale every January, so refresh when the script warns, when the calendar year exceeds `tax_year`, or when the user asks. Procedure:

1. Search the official sources listed in the file's `sources`. Spain: AEAT for the IRPF scale and personal minimum, Seguridad Social for the RETA cuota table, the maximum contribution base and the employee rates incl. MEI. US: IRS inflation-adjustment Rev. Proc. for the brackets and standard deduction, SSA for the Social Security wage base; re-read the Additional Medicare Tax and self-employment tax rules, which the first version took from general knowledge.
   - **Spanish communities:** take the scale only from the community's official gazette (BOCM, DOGC, DOGV, BOJA, BOC) or its tax authority, the BOE consolidated text, or the AEAT manual and Hacienda's "Tributación Autonómica. Medidas <year>" report; never from blogs or aggregators. Check that the "cuota íntegra" column matches the rates, cross-check with the AEAT Manual de Renta, and record in `unverified` anything read only as a summary. To add a community, add an object with the same fields and a lowercase id without accents, and put its expected quotas in `scripts/tests/test_es_regions.py`. Run `python3 -m unittest discover -s scripts/tests` after every refresh.
2. Show the user a before/after diff of every changed value with its source link. Do not overwrite silently: a wrong tax number quietly corrupts every future comparison, so they confirm first.
3. On their approval, edit the JSON, set `tax_year`, `verified_on` to today, and `verified_by` to the sources actually read (drop the "NOT checked" wording only if you really verified against official pages).
4. Rerun a sample comparison to check nothing broke.

A scheduled nudge is optional: if the user wants a real reminder in January, offer to set one up with whatever scheduling mechanism the agent or the OS provides (cron, a scheduled agent task, a calendar event) that opens a session running this refresh.

## Output format

Keep it scannable, not an essay. Use exactly these sections, in this order:

1. **TL;DR** (2 lines): verdict, fit score, effective-net delta vs threshold.
2. **Net comparison**: a table with rows Gross, Social security / cuota, Income tax, Net, Benefits, Out-of-pocket costs, Effective net, and columns Current / Offer / Delta; below it the assumptions list.
3. **Fit**: score, matches, gaps, likely real scope.
4. **Conditions**: short table for remote, benefits, trajectory, risks.
5. **Recruiter signals** (one short line each) and **Questions for the recruiter**: 2-3 numbered items.
6. **Reply draft**.
7. **Assumed or unverified**: bullet list.

Do not produce prose paragraphs where a table or bullets will do.
