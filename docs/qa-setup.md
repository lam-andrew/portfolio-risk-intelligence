# Enable grounded filing questions with a free Gemini API key

US-12 handoff, September 26, 2026. Implementation: [draft PR #92](https://github.com/lam-andrew/portfolio-risk-intelligence/pull/92).
This guide enables the candidate provider for evaluation; it does not establish model quality
or mark the story accepted. Architecture: [ADR 0022](adr/0022-grounded-filing-questions.md).

## 1. Create a project key

1. Open [Google AI Studio API keys](https://aistudio.google.com/api-keys). Sign in with
   `orbitprjct@gmail.com` if you want the dedicated project account to own the key.
2. Select or create a dedicated Orbit project. New AI Studio users may already have a default
   project; existing Cloud users may need to import one from the Projects page.
3. Confirm that project's tier is **Free** and Cloud Billing is **not enabled/linked**.
   Do not choose an existing paid project, activate a trial, add payment details or upgrade.
   If a payment step appears mandatory, stop and ask for help with the free setup.
4. Create an API key in that project and copy it privately. Newly created AI Studio keys
   are restricted to the Gemini API by default. Orbit sends the key in a server-side header.

The key's project controls billing. Orbit cannot inspect or enforce its billing tier.
The local quota counters are a second guard, not a substitute for billing being disabled.
Google documents [key creation](https://ai.google.dev/gemini-api/docs/api-key) and
[free/paid billing](https://ai.google.dev/gemini-api/docs/billing). Checked September 26, 2026;
UI labels and availability can change. The selected models are `gemini-3.8-flash` and
`gemini-embedding-2`; confirm their availability in your project's model/rate-limit view.
Do not substitute a paid model if one is unavailable.

## 2. Save it locally

Open the existing `.env` file in the repository root. On Andrew's machine it is:
`/Users/andrewlam/Documents/portfolio-risk-intelligence/.env`.
Edit the three entries below, or add them if absent. Keep only one entry per name.
Preserve the existing SEC contact, market-data token and database settings.

```dotenv
APP_GEMINI_API_KEY=replace_this_with_your_actual_key
APP_QA_PROVIDER=gemini
APP_QA_ENABLED=false
```

Do not overwrite `.env` by copying `.env.example` over it. Do not paste the key into chat,
a screenshot, a GitHub issue or a `VITE_*` frontend variable. `.env` is ignored by Git.

**Assisted handoff:** leave `APP_QA_ENABLED=false` and tell Codex:
“Key saved; Orbit project is Free tier and billing is disabled.” No key text is needed.
Codex can then enable the feature, restart services and run the live checks.

## 3. Enable it yourself (optional)

After confirming the free project, set `APP_QA_ENABLED=true` in `.env`. From the repository
folder, run:

```bash
docker compose up -d --build backend embedding-worker
docker compose ps
```

Recreating services applies environment changes; a plain restart does not update their
configured environment. Enabling starts background preparation of public filings for all
currently held/watched issuers. The key is available only to the backend and embedding worker.

Open [Orbit SEC filings](http://localhost:5173/filings), sign in, and select a company.
Reload the page after enabling. The question card should change from disabled to preparation
counts, then enable **Ask question** when every cached passage for that company is ready.

Preparation is deliberately bounded: at most 16 passages per batch, one batch every
30 seconds, with at most 200 embedding calls per UTC day shared with questions. That is at
most 3,200 passages/day before query calls or failed requests. The September 26 local snapshot
has 6,522 tracked passages, so preparing the whole existing corpus requires at least three
UTC quota days at these settings. Individual companies can become ready earlier; Google
quotas may take longer. Progress persists through restarts. Do not delete counters to rush it.

## 4. First live check

1. Select a prepared company and ask: “What supply chain risks does the company disclose?”
2. Expect either claims with expandable exact quotes and SEC links, or an explicit statement
   that supporting evidence could not be found. A service/quota error is a blocked attempt,
   not a successful abstention.
3. Open each cited filing. Confirm company, filing date, quote and whether it actually supports
   the claim. Check the reporting period when numbers are involved.
4. After at least 30 seconds, ask: “What exact closing stock price will this company have one
   year from today?” Expect an insufficient-evidence response without claims or citations.

Google's [free-tier pricing/data-use terms](https://ai.google.dev/gemini-api/docs/pricing)
allow product-improvement use. Only enter nonconfidential questions. Orbit sends the question,
public filing excerpts and source labels; it does not attach account details or portfolio
quantities. It stores no conversation history.

## 5. When something is unavailable

- **Still disabled:** check the three local entries, recreate both services, and reload the page.
- **No passages:** ingestion must finish first. Some holdings have no supported issuer filings;
  choose a company with indexed 10-K/10-Q/8-K sources.
- **Progress pauses:** check AI Studio's project quota and the embedding worker's recent logs:
  `docker compose logs --tail=30 embedding-worker`. Do not share configuration dumps or keys.
- **Quota message:** Orbit permits 10 questions/account/day, 20 across the deployment/day and
  40 generation calls/day. Supported answers use two generation calls. Space questions by at
  least 30 seconds. Failed admitted requests consume reservations too. Google quota failures
  pause the affected operation for ten minutes; Google's own reset may take longer.
- **Daily cap:** Orbit resets daily counts at midnight UTC (5 p.m. Pacific daylight time;
  4 p.m. Pacific standard time). Provider quotas have their own schedule. Restarting containers
  preserves Orbit's counters and prepared passages.
- **Service error:** this can mean a rejected key, unavailable model, invalid model output or
  provider outage. Check project/model access in AI Studio; never enable payment to fix it.
- **Stop model usage:** set `APP_QA_ENABLED=false` and recreate backend + embedding-worker.
  This stops new work after restart; a previously transmitted request cannot be recalled.
  Source search and cached filings remain available.

## 6. What happens after the key handoff

Codex will confirm configuration without printing the key, enable/recreate the services,
verify real embedding and generation calls, then run the [20-case evaluation plan](us12-live-evaluation.md)
and browser checks. Ten questions/account/day means at least two UTC quota days for 20
completed cases, possibly more after failures or smoke checks. We will keep the existing
budgets, report actual failures and fix them before seeking final acceptance.

US-12 stays In Progress and PR #92 stays draft until live grounding, citation, abstention,
quota behavior and user acceptance are verified. Andrew reviews the experience before merge.
