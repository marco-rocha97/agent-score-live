# SPEC: Agent Score Live

> If there's no clear pain, there's no SPEC. There's just an idea.
> The SPEC answers: what problem, for whom, and how do we know it worked?
> Stack, architecture, APIs, and databases live in the Tech Spec — not here.

> **Context:** Demonstrable MVP (3 days), built as an interview deliverable for the AI Engineer (FDE) role at Khal.ai. Source briefing: PRD — Agent Score Live v1.0.

---

## Problem Definition

- **Concrete pain:** Khal sells four post-go-live promises (15 days to production, up to 65% cost reduction per ticket, rising NPS, SLA compliance). All of them depend on agent quality that keeps improving *after* go-live. Today that "after" is covered by a manual weekly report the FDE assembles by hand (4–6 hours/week, biased toward the agent's creator), quarterly QBR meetings that lag the iteration speed AI allows, and metrics scattered across logs, CRM, and the FDE's spreadsheet. The client loses the felt sense of continuous ROI, the FDE becomes a human bridge between raw data and narrative, and Khal carries as headcount a problem that is structurally a product problem.
- **Affected persona(s):**
  - **Ana — FDE (primary user, daily operator).** 28, 4 years in software/AI engineering, embedded in a large enterprise account. Measures her success by the Agent Score rising. Daily pain: 4–6 hours/week assembling the client report. Structural pain: she could be building new use cases instead of reporting on old ones.
  - **Bruno — Customer Success Manager (secondary user, renewal narrator).** 34, from consulting, renews and expands 6–10 enterprise accounts. Pain: when something degrades between QBRs, he is the last to know.
  - **Camila — CX Director at the client (viewing stakeholder).** 42, Hapvida-like enterprise, reports to the COO, approved Khal against internal resistance. Won't touch a panel daily, but opens it Monday morning to answer "am I making money with this, and is it getting better or worse?"
  - **Daniel — Head of Operations / CRO at Khal (business decision-maker).** 38, watches NRR, gross margin, time-to-value. Doesn't use the product; consumes the portfolio meta-view.
- **Current behavior:** The FDE manually compiles a weekly quality report per account from scattered sources. CS walks into quarterly QBRs with a hand-built deck. The client has no self-serve, always-current view of quality. Quality regressions surface late — often only at the next QBR.

---

## Success Metrics

- **Observable change in user behavior:** The FDE stops assembling the weekly report by hand and instead opens a panel that already shows the quality trend, the segments that dropped, the root cause, and a concrete next iteration — turning report-writing time into improvement-engineering time. CS and the client open a single shared, always-current view instead of waiting for a quarterly deck.
- **Anchor metric:** **The full quality cycle is navigable end-to-end in under 4 minutes.** A reviewer can walk all five screens on plausible synthetic data and follow one illustrative case from quality drop → root cause → recommendation → applied iteration → pre/post comparison, with every screen functional. This anchors the actual MVP objective (the interview demo). Secondary product metrics — % of recommendations accepted, North Star (% of accounts with avg Score ≥80 and non-negative weekly trend), Score↔NPS correlation ≥0.7 — are tracked as long-horizon hypotheses, not as the anchor for this deliverable.

---

## User Stories

> Format: As [persona], I want [observable action] so that [clear benefit].

- As **Ana (FDE)**, I want to open the panel and immediately see the account's weekly quality trend so that I can spot a degrading agent without compiling anything by hand.
- As **Ana (FDE)**, I want to drill from a dropped score into the specific dimension, the affected conversations, and the dominant root-cause pattern so that I debug from evidence instead of guessing.
- As **Ana (FDE)**, I want a concrete suggested iteration for each root cause that I can accept as a tracked task so that I know exactly what to change next.
- As **Ana (FDE)**, I want the system to mark a pre/post window when I apply an iteration so that I can prove the change worked.
- As **Ana (FDE)**, I want to mark a score as a false positive on a conversation so that I can flag where the engine got it wrong.
- As **Bruno (CS)**, I want to generate a quarterly executive summary so that I walk into the QBR with an automatically built, on-brand one-pager instead of a hand-made deck.
- As **Camila (CX Director at the client)**, I want a read-only view with three cards — accumulated projected savings, average Score with a simple trend, and attention points in plain language — so that in 30 seconds I know whether the investment is paying off and improving.
- As **Daniel (CRO)**, I want a portfolio meta-view so that I can see at a glance which accounts are healthy and which need intervention. *(Static mock in this MVP — see Out of Scope.)*
- As **Ana (FDE)**, I want the system to surface a drop even when the affected segment is small, clearly labeled as a limited-data hypothesis, so that I'm not blind to early signals but I'm also not misled by thin data.

---

## Expected Behaviors

> Describe what users see and do — nothing about internal architecture.

### Feature: Conversation ingestion and scoring

```gherkin
Scenario: A batch of synthetic conversations is loaded and scored
  Given a batch of 100–200 synthetic conversations across 3 agents (Support, Collections, Retention) and 2 channels (Voice, WhatsApp), distributed over 7 simulated days
  When the batch is ingested
  Then every conversation has a 0–100 score on each of the 5 dimensions (Resolution, Guardrail Adherence, Clarity & Context, Customer Sentiment, Efficiency)
  And each conversation has a consolidated score computed as the weighted average of its dimensions
  And each dimension score exposes its 2–4 sub-signals and a textual justification referencing a specific turn

Scenario: Score is explainable down to the turn
  Given a scored conversation
  When the FDE opens its turn-by-turn timeline
  Then each turn shows the per-dimension score and the reason for it (e.g. "context break at turn 4")
  And the textual evidence behind a reason is highlighted in the turn
```

### Feature: Dashboard and drop detection

```gherkin
Scenario: FDE sees the account quality trend
  Given scored conversations across the 7-day window
  When the FDE opens the Overview screen
  Then the top KPIs show average Score (week), delta vs. previous week, conversations analyzed, and active alerts
  And a weekly trend line shows the consolidated Score and per-dimension scores
  And distribution bars break Score down by agent, channel, and intention

Scenario: A relevant drop raises an alert
  Given a dimension whose score fell by 5 or more absolute points in a segment, comparing the rolling 7-day window to the previous 7 days
  When the dashboard renders
  Then the segment appears in the "attention points" list
  And a subtle red alert badge appears at the top
  And the system attributes the drop to the most specific segment it can (channel, agent, or intention)

Scenario: Drop in a thin segment is surfaced as a limited-data hypothesis
  Given a dimension drop in a segment with fewer than 20 conversations
  When the dashboard renders
  Then the drop is still surfaced
  And it is visibly labeled as a limited-data hypothesis rather than a confirmed alert

Scenario: FDE filters the view
  Given the Overview screen
  When the FDE applies filters for time window, agent, channel, intention, or client segment
  Then all KPIs, the trend line, the distribution bars, and the attention list update to reflect the filtered set
```

### Feature: Root cause and recommendation

```gherkin
Scenario: System identifies a dominant root-cause pattern
  Given a set of low-scoring conversations on a dropped dimension within a segment
  When the FDE opens the root-cause view
  Then the system shows the dominant pattern — a shared attribute (same intention, channel, failure type, or client segment) covering 60% or more of the affected conversations
  And it presents 3 representative example conversations

Scenario: No attribute reaches the dominance threshold
  Given a set of affected conversations where no shared attribute reaches 60% coverage
  When the FDE opens the root-cause view
  Then the system shows the strongest available attribute as the leading hypothesis
  And it is visibly labeled as a leading hypothesis rather than a confirmed root cause

Scenario: FDE accepts a recommendation
  Given a root cause with a concrete suggested action (e.g. "add inline CPF-collection fallback to the Collections agent")
  When the FDE accepts the recommendation
  Then a tracked task is created with status "accepted"
  And a confirmation toast appears stating that pre/post will be tracked over the next 7 days
  And the system marks a pre/post comparison window

Scenario: FDE marks a false positive
  Given a conversation the FDE believes was scored incorrectly
  When the FDE marks it as a false positive
  Then the conversation is flagged as a false positive and the flag is retained as a signal
```

### Feature: Client screen

```gherkin
Scenario: Client opens the read-only view
  Given a client (Camila) opening her saved link
  When the Client screen loads
  Then she sees exactly three cards — accumulated projected savings (R$), average Score with a simple trend, and attention points in plain language ("No critical points this week.")
  And there is no technical drill-down available on this screen

Scenario: Client screen shows no unaccompanied bad news
  Given an active attention point exists
  When the Client screen renders it
  Then the attention point is shown alongside its mitigation, never as a raw negative number on its own
```

### Feature: QBR executive summary

```gherkin
Scenario: CS generates a quarterly summary
  Given Bruno on the QBR screen with a selected quarter window
  When he triggers "Generate quarterly summary"
  Then a loading state communicates that generation is in progress
  And on completion a one-pager is produced covering Score evolution, key improvements, peak cases, estimated ROI, and next recommendations
  And the one-pager can be exported as a PDF

Scenario: Summary generation fails
  Given Bruno triggered summary generation
  When generation fails
  Then an error state explains what went wrong and offers a retry
  And no partial or corrupted document is presented as final
```

### Feature: Iteration pre/post tracking

```gherkin
Scenario: FDE marks an iteration as applied
  Given a recommendation the FDE has accepted
  When the FDE marks the iteration as "applied"
  Then the system begins comparing the pre-window and post-window scores for the affected segment
  And the Iterations screen shows the iteration's status and its pre/post metrics as they accumulate
```

---

## Experience Design

- **User journey:**
  1. **Overview (Ana, ~5 min Monday morning):** open panel → see weekly trend → spot an agent down ~6 points → click into the dropped dimension.
  2. **Drill-down (Ana):** see the affected conversations → open a conversation's turn timeline → see per-turn scores and highlighted evidence → open root cause → see the dominant pattern and 3 examples.
  3. **Iterations (Ana):** read the concrete recommendation → accept it as a tracked task → later mark it "applied" → watch pre/post comparison populate.
  4. **Client (Camila, ~30 sec):** open saved link → read three cards → close, reassured.
  5. **QBR (Bruno, ~10 min):** open QBR tab → select last quarter → generate summary → export PDF.
  6. **Meta-view (Daniel, ~2 min):** open portfolio view (static mock) → scan account health.
- **Interface states:**
  - **Empty state:** Not required for the core dashboard/drill-down screens — they render from pre-loaded, pre-scored synthetic data and are never empty in the demo. Filtered views that return no results show a plain "no conversations match these filters" message.
  - **Loading state:** Required where work is genuinely asynchronous — QBR summary/one-pager generation. A clear in-progress indicator must show while the summary is being generated.
  - **Success state:** Accepting a recommendation shows a confirmation toast ("Iteration marked for implementation. We'll track pre/post over the next 7 days."). Completed QBR generation presents the finished one-pager ready to export.
  - **Error state:** Required on async actions (QBR summary generation). On failure, the user sees what went wrong and a retry affordance; no partial document is presented as final.
- **Non-negotiable principles:**
  - **Opinionated, not configurable.** The panel tells the user what to look at; the user does not assemble their own view. Dimension weights live in a configuration file, never in the UI.
  - **Executive information hierarchy.** What matters fits on one screen.
  - **Business language, not technical.** "Adherence to business rules," not "guardrail violation."
  - **Semantic color.** Green/yellow/red used with an explicit, stated criterion — never decoratively.
  - **Density gradient.** High density on the internal (FDE) screens; low density on the Client screen.
  - **Explainability is mandatory.** Every score carries a textual justification referencing a turn. No score is shown as a bare number.
  - **The Client screen is curated.** No raw bad news without an accompanying mitigation.
- **Accessibility (MVP bar — basic):**
  - All screens keyboard-navigable.
  - Status is **never communicated by color alone** — green/yellow/red always pairs with an icon or text label, so color-blind users get the same signal.
  - Sensible contrast on text and key UI elements.
  - Full WCAG 2.1 AA conformance (screen-reader support, focus management, full contrast audit) is **out of scope** for the 3-day MVP — see Out of Scope.

---

## Business Constraints

- **Stakeholders requiring alignment:** This is an interview deliverable — the candidate owns it end-to-end; the interview panel at Khal.ai is the audience. No internal approval gate before "ship" beyond the candidate's own readiness check.
- **Non-negotiable business rules:**
  - **LGPD / PII:** Conversations may contain PII. The MVP assumes PII is masked upstream and does not perform masking itself; this assumption must be documented. Each score is treated as a traceable, auditable record of an automated decision.
  - **Positioning boundary:** The product is positioned as a *production observability layer*, explicitly not an agent-building tool — it must not duplicate or appear to duplicate Khal's Agent Builder.
- **Critical timeline:** 3-day build. Day 1 — synthetic data + scoring engine + calibration. Day 2 — dashboard + drill-down + root cause + recommendation + Client screen. Day 3 — executive summary generator + visual polish + demo script + backup video + one-pager. Hard "done" gate: the five screens function on plausible data, the three illustrative cases are visible in real navigation, the full cycle is navigable in under 4 minutes, a backup video is recorded, the 3-act demo script is written, and the one-page thesis document is finalized.

> Technical decisions (the deterministic-vs-LLM scoring split, LLM-as-judge prompting, infra, batch processing, data schema) live in the Tech Spec.

---

## Out of Scope

- **Multi-account / multi-tenant** — MVP is single-tenant, single-user; portfolio scale is a later wave.
- **Real authentication, SSO, RBAC** — not needed for a single-user demo.
- **Production integrations with CRM, ERP, telephony** — replaced by synthetic data and mocks; integrations are a later wave.
- **Real-time per-call live monitoring for a human supervisor** — that is a different product.
- **Pre-production / simulation Agent Score** — Agent Score Live complements it, does not replace it.
- **Manual conversation QA with a human review queue** — no review queue in the MVP.
- **Configurable BI dashboard** — the product is deliberately opinionated and prescriptive, not a generic dashboard builder.
- **Billing, pricing, contracts** — not addressed.
- **Real PII masking / anonymization** — assumed handled upstream; documented as an assumption.
- **CRO portfolio meta-view as a live feature** — present only as a static mock in the MVP; the real multi-account meta-view is a later wave.
- **Alerts via Slack / email / WhatsApp** — later wave.
- **Human iteration-approval workflow with review** — later wave; the MVP only lets the FDE accept a recommendation as a tracked task.
- **Automated A/B comparison of agent versions** — later wave.
- **Anonymous cross-client industry benchmarking** — later wave.
- **Advanced anomaly detection** — later wave; the MVP uses the stated threshold rules.
- **Automatic suggestion of net-new use cases not yet covered** — later wave.
- **Full WCAG 2.1 AA accessibility conformance** — MVP targets a basic bar only (keyboard nav, non-color status signal, sensible contrast); full conformance is a later wave.

---

## Ready to Plan?

- [x] Problem has a concrete, observable user pain (not a feature wishlist)
- [x] At least one specific persona identified
- [x] Success metric is measurable and anchored
- [x] User stories cover happy path + at least one failure case
- [x] Acceptance criteria are observable (no internal implementation references)
- [x] Out-of-scope is explicit
- [x] No stack, schema, or technical decisions included
