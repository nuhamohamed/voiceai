<!-- GSD:project-start source:PROJECT.md -->

## Project

**Standup Proxy (Clone Agent)**

A *standup proxy*: when a teammate can't attend standup, **their clone agent joins in their cloned voice**, gives their update, and **answers follow-up questions about their work in real time** — grounded in that person's week of context (Slack / calendar / Linear) retrieved live via **Moss** — then posts action items to a Slack summary channel. Built for the Moss-hosted Conversational AI Hackathon (YC SF, Co-Pilot track). Buyer = teams and managers losing hours to status meetings. The hackathon demo uses 2 hardcoded personas (the team members themselves).

**Core Value:** **The clone answers a live follow-up question with the *right, real specifics* retrieved from that person's context in Moss** — visibly (retrieval shown on screen) and audibly (in their cloned voice). If everything else fails, this one moment must work — it is the moat and the demo's killer moment.

### Constraints

- **Tech stack**: Python + LiveKit (Python SDK) — most mature for agents; team leans it. Ground all Moss/LiveKit/Qwen/Minimax SDK calls in current docs (source-driven); do not hallucinate SDK APIs.
- **Timeline**: ~24h build; submissions due 11 AM Sunday. Every phase must stay demo-able.
- **Team**: 3 people working in parallel — roadmap must expose 3 clear ownable workstreams against a shared contract.
- **Demo surface**: LiveKit playground + a Slack summary channel. No custom UI.
- **Security**: No secrets in repo. No API keys committed.
- **Demo integrity**: Demo only what is real; pitch enterprise/full-org-brain as vision.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->

## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

| Skill | Description | Path |
|-------|-------------|------|
| caveman | > Ultra-compressed communication mode. Cuts token usage ~75% by dropping filler, articles, and pleasantries while keeping full technical accuracy. Use when user says "caveman mode", "talk like caveman", "use caveman", "less tokens", "be brief", or invokes /caveman. | `.agents/skills/caveman/SKILL.md` |
| design-an-interface | Generate multiple radically different interface designs for a module using parallel sub-agents. Use when user wants to design an API, explore interface options, compare module shapes, or mentions "design it twice". | `.agents/skills/design-an-interface/SKILL.md` |
| diagnose | Disciplined diagnosis loop for hard bugs and performance regressions. Reproduce → minimise → hypothesise → instrument → fix → regression-test. Use when user says "diagnose this" / "debug this", reports a bug, says something is broken/throwing/failing, or describes a performance regression. | `.agents/skills/diagnose/SKILL.md` |
| edit-article | Edit and improve articles by restructuring sections, improving clarity, and tightening prose. Use when user wants to edit, revise, or improve an article draft. | `.agents/skills/edit-article/SKILL.md` |
| git-guardrails-claude-code | Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute. Use when user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code. | `.agents/skills/git-guardrails-claude-code/SKILL.md` |
| grill-me | Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me". | `.agents/skills/grill-me/SKILL.md` |
| grill-with-docs | Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates documentation (CONTEXT.md, ADRs) inline as decisions crystallise. Use when user wants to stress-test a plan against their project's language and documented decisions. | `.agents/skills/grill-with-docs/SKILL.md` |
| handoff | Compact the current conversation into a handoff document for another agent to pick up. | `.agents/skills/handoff/SKILL.md` |
| improve-codebase-architecture | Find deepening opportunities in a codebase, informed by the domain language in CONTEXT.md and the decisions in docs/adr/. Use when the user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more testable and AI-navigable. | `.agents/skills/improve-codebase-architecture/SKILL.md` |
| migrate-to-shoehorn | Migrate test files from `as` type assertions to @total-typescript/shoehorn. Use when user mentions shoehorn, wants to replace `as` in tests, or needs partial test data. | `.agents/skills/migrate-to-shoehorn/SKILL.md` |
| obsidian-vault | Search, create, and manage notes in the Obsidian vault with wikilinks and index notes. Use when user wants to find, create, or organize notes in Obsidian. | `.agents/skills/obsidian-vault/SKILL.md` |
| prototype | Build a throwaway prototype to flesh out a design before committing to it. Routes between two branches — a runnable terminal app for state/business-logic questions, or several radically different UI variations toggleable from one route. Use when the user wants to prototype, sanity-check a data model or state machine, mock up a UI, explore design options, or says "prototype this", "let me play with it", "try a few designs". | `.agents/skills/prototype/SKILL.md` |
| qa | Interactive QA session where user reports bugs or issues conversationally, and the agent files GitHub issues. Explores the codebase in the background for context and domain language. Use when user wants to report bugs, do QA, file issues conversationally, or mentions "QA session". | `.agents/skills/qa/SKILL.md` |
| request-refactor-plan | Create a detailed refactor plan with tiny commits via user interview, then file it as a GitHub issue. Use when user wants to plan a refactor, create a refactoring RFC, or break a refactor into safe incremental steps. | `.agents/skills/request-refactor-plan/SKILL.md` |
| review | Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes — Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/PRD asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to "review since X". | `.agents/skills/review/SKILL.md` |
| scaffold-exercises | Create exercise directory structures with sections, problems, solutions, and explainers that pass linting. Use when user wants to scaffold exercises, create exercise stubs, or set up a new course section. | `.agents/skills/scaffold-exercises/SKILL.md` |
| setup-matt-pocock-skills | Sets up an `## Agent skills` block in AGENTS.md/CLAUDE.md and `docs/agents/` so the engineering skills know this repo's issue tracker (GitHub or local markdown), triage label vocabulary, and domain doc layout. Run before first use of `to-issues`, `to-prd`, `triage`, `diagnose`, `tdd`, `improve-codebase-architecture`, or `zoom-out` — or if those skills appear to be missing context about the issue tracker, triage labels, or domain docs. | `.agents/skills/setup-matt-pocock-skills/SKILL.md` |
| setup-pre-commit | Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests in the current repo. Use when user wants to add pre-commit hooks, set up Husky, configure lint-staged, or add commit-time formatting/typechecking/testing. | `.agents/skills/setup-pre-commit/SKILL.md` |
| tdd | Test-driven development with red-green-refactor loop. Use when user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development. | `.agents/skills/tdd/SKILL.md` |
| teach | Teach the user a new skill or concept, within this workspace. | `.agents/skills/teach/SKILL.md` |
| to-issues | Break a plan, spec, or PRD into independently-grabbable issues on the project issue tracker using tracer-bullet vertical slices. Use when user wants to convert a plan into issues, create implementation tickets, or break down work into issues. | `.agents/skills/to-issues/SKILL.md` |
| to-prd | Turn the current conversation context into a PRD and publish it to the project issue tracker. Use when user wants to create a PRD from the current context. | `.agents/skills/to-prd/SKILL.md` |
| triage | Triage issues through a state machine driven by triage roles. Use when user wants to create an issue, triage issues, review incoming bugs or feature requests, prepare issues for an AFK agent, or manage issue workflow. | `.agents/skills/triage/SKILL.md` |
| ubiquitous-language | Extract a DDD-style ubiquitous language glossary from the current conversation, flagging ambiguities and proposing canonical terms. Saves to UBIQUITOUS_LANGUAGE.md. Use when user wants to define domain terms, build a glossary, harden terminology, create a ubiquitous language, or mentions "domain model" or "DDD". | `.agents/skills/ubiquitous-language/SKILL.md` |
| write-a-skill | Create new agent skills with proper structure, progressive disclosure, and bundled resources. Use when user wants to create, write, or build a new skill. | `.agents/skills/write-a-skill/SKILL.md` |
| writing-beats | Shape an article as a journey of beats, choose-your-own-adventure style. The user picks a starting beat from the raw material, you write only that beat, then offer options for where to pivot next, beat by beat, until the article reaches a natural end. Use when the user has raw material and wants to assemble it as a narrative rather than an argument. | `.agents/skills/writing-beats/SKILL.md` |
| writing-fragments | Grilling session that mines the user for fragments — heterogeneous nuggets of writing (claims, vignettes, sharp sentences, half-thoughts) — and appends them to a single document as raw material for a future article. Use when the user wants to develop ideas before imposing structure, or mentions "fragments", "ideate", or "raw material" for writing. | `.agents/skills/writing-fragments/SKILL.md` |
| writing-shape | Take a markdown file of raw material and shape it into an article through a conversational session — drafting candidate openings, growing the piece paragraph by paragraph, arguing about format (lists, tables, callouts, quotes) at each step. Use when the user has a pile of notes, fragments, or a rough draft and wants help turning it into something publishable. | `.agents/skills/writing-shape/SKILL.md` |
| zoom-out | Tell the agent to zoom out and give broader context or a higher-level perspective. Use when you're unfamiliar with a section of code or need to understand how it fits into the bigger picture. | `.agents/skills/zoom-out/SKILL.md` |
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

---

## Agent Coordination Protocol

This project has three agents working in parallel: **Agent A**, **Agent B**, and **Agent C**. Follow this protocol every session — it prevents file conflicts and keeps all agents aligned.

### Who are you?
- Collaborator 1 → **Agent A** → owns `agent-status/agent-a.json`
- Collaborator 2 → **Agent B** → owns `agent-status/agent-b.json`
- Collaborator 3 (Nuha) → **Agent C** → owns `agent-status/agent-c.json`

### Step 1 — Read other agents' status BEFORE writing any code

Fetch the two status files that are NOT yours:
- https://raw.githubusercontent.com/nuhamohamed/voiceai/main/agent-status/agent-a.json
- https://raw.githubusercontent.com/nuhamohamed/voiceai/main/agent-status/agent-b.json
- https://raw.githubusercontent.com/nuhamohamed/voiceai/main/agent-status/agent-c.json

Check:
- **`files`** — do not touch any file listed in another agent's `files` array without coordinating first
- **`blockers`** — if another agent is waiting on you, address it before starting new work

### Step 2 — Claim your work before writing any code

Update your own `agent-status/agent-X.json`:

```json
{
  "agent": "X",
  "status": "working",
  "currentTask": "short description",
  "files": ["every/file/you/plan/to/touch.py"],
  "blockers": [],
  "waitingOn": null,
  "lastUpdated": "ISO timestamp",
  "notes": ""
}
```

Then commit and push immediately:
```bash
git add agent-status/agent-X.json
git commit -m "[status] Agent X: <what you're doing>"
git push
```

### Step 3 — Check in every 30 minutes

```bash
git pull origin main
```
Re-read the other agents' JSON files. Update and push your own if anything changed.

### Step 4 — Clear your status when done

Set `status` to `"idle"`, clear `files` and `currentTask`, commit and push with `[status]` prefix.

### Rules
- Only write to your own status file. Never edit another agent's JSON.
- Never touch a file in another agent's `files` list without coordinating first.
- Always `git pull` before starting new work.

### Dashboard
Live view: https://nuhamohamed.github.io/voiceai/
