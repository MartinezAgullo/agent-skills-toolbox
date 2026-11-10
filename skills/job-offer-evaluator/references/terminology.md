# Terminology: employee, self-employed, freelance, B2B, autónomo

Recruiters, the CV and the tax code use different words for the same few situations. The tax maths only knows **two statuses**; everything else is a name for one of them.

| Status in the code | Who pays your taxes and social security | Spain | United States | Other names you will hear |
|---|---|---|---|---|
| `employee` | The employer withholds income tax and pays your social security from your gross salary | Trabajador por cuenta ajena (indefinido, temporal) | W-2 employee | Salaried, payroll, "full-time", EOR / umbrella (a third party employs you on paper) |
| `self_employed` | You, from what you invoice | Autónomo, registered in the RETA | 1099 / sole proprietor | Freelance, contractor, consultant, "B2B", "no empleado", "cooperation type: B2B contract" |

## Points that cause confusion
- **B2B** (business-to-business) says *how you bill*: you invoice a company instead of receiving a payslip. For tax it means `self_employed`. It does not tell you whether you invoice as a person (autónomo) or through your own company.
- **Autónomo** is the Spanish legal form of being self-employed. "Freelance" is the generic English word. In this skill `freelance`, `b2b`, `contractor`, `autonomo` and `1099` all map to `self_employed`; output always shows the country's own label.
- **Own company** (Spain: SL; US: LLC or S-corp) is a third case with different taxation. It is NOT modelled; if the user wants it, say the numbers do not apply and suggest a gestor.
- **Autónomo económicamente dependiente (TRADE)** is a Spanish legal figure for an autónomo who earns most of their income from one client. It adds obligations and is the legal risk behind "B2B for a long-term single-client role" (see `recruiter-signals.md`).
- **Hourly rate vs annual salary** is about how the pay is quoted, not about the status. An hourly rate is usually `self_employed`, but employees can be paid hourly too.

## Fiscal residence (Spain): which community's IRPF applies
Spanish IRPF has a state part (same everywhere) and an autonomic part that each autonomous community sets for itself. The community that counts is the one of **fiscal residence**: where the taxpayer habitually resides on 31 December of the tax year. It is **not** the place the job is located (office, client site) and **not** the registered seat of the employer or the recruiter's agency. Working remotely for a company in another community changes nothing: tax follows where the person lives. Foral regimes (País Vasco, Navarra) and Ceuta/Melilla have their own rules and are not modelled; the script falls back to the state scale with a visible warning.

## How to map what the user says
1. Ask which of the two statuses applies, using the user's own words ("indefinido", "autónomo", "B2B", "W-2", "1099").
2. Pass the matching value (or any alias) to `--current-contract` and `--offer-type`.
3. If it is neither (own company, EOR with special terms, cooperatives), say it is outside the model and give a rough estimate labelled as such.
