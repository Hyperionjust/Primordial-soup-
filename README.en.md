# primordial-soup · 原始汤

[中文](README.md) | English

**The first collision-based memory system: it doesn't retrieve old ideas — it smashes old cards into new ones.**

> A cross-conversation association mechanism: conversations crystallize "amino-acid cards"; each new session, a "lightning strike" — a Miller-Urey-style random collision — smashes randomly drawn old cards into today's topic.

> **Positioning: as of Aug 2026 research, no public project combines these four layers.** The mainstream memory routes are **retrieval** (semantic search) and **compression** (summarization). This mechanism's core action is **collision**: randomly flip up old cards and crash them into the current topic, letting unexpected connections produce new ideas. Public neighbors — the [A-MEM](https://github.com/amemhq/amem) line (graph linking + semantic retrieval + LLM-driven evolution) and the memory-compiler line (summarization + embedding retrieval) — cover none of the four-layer stack: **true-random sampling (with a wildcard slot) × weight evolution (Hebbian / Zeigarnik / decay) × protein synthesis × full ledger audit**. Plenty of projects retrieve memories. Almost none **collide** them.

| Route | Representatives | How memory is accessed | What's different here |
|---|---|---|---|
| Semantic retrieval & evolution | A-MEM line | Ranked recall by relevance | Cards are drawn by **weighted randomness**, not relevance — surprise is a feature, not a bug; deliberate picking kills serendipity |
| Summarization / embedding compression | memory-compiler line | Squeezed into the context window | Memory **never enters the context**; it appears only when a collision passes the presentation gate — otherwise total silence |
| Cross-conversation association (this project) | primordial-soup | Random collision + verdict-driven evolution | Four layers: true randomness (wildcard slot guarantees surprise) × weight evolution × protein synthesis × full audit (even silence is logged) |

原始汤 (primordial soup, from the origin-of-life metaphor) is an association system that keeps memory in the filesystem: each conversation's conclusions crystallize into an "amino acid" card; at the start of a new session, a "lightning strike" randomly draws a few old cards and smashes them into today's topic — the sparks may correct old conclusions, answer old open questions, or synthesize new "protein" review cards. All memory lives in files, with no dependency on any global memory.

- Amino acid ＝ one conversation's conclusion card (one strong claim per line, plus open questions and connection points)
- Protein ＝ a synthesis of several cards (joins the pool, but never co-drawn with its members)
- Lightning ＝ weighted random draw (2 weighted + 1 wildcard), smashing old cards into today's topic
- Tide ＝ a weekly reconciliation task: collect pending verdicts, detect clusters, propose closures (proposes only, never implements)

## Features

- **True-random collision**: card selection is computed deterministically by the sampler (system entropy, or `--seed` for reproducibility). The model is forbidden to hand-pick cards — deliberate picking kills the very serendipity lightning exists for.
- **Incremental presentation gate**: a collision is presented only if it passes at least one of four incremental tests (changes a conclusion / provides a counterexample or tension / answers an old open question / opens a genuinely new direction). Otherwise total silence — no mention, no "no collision this time" ceremony.
- **Silence is auditable**: even silent draws are logged. The silence rate feeds the M5 effectiveness settlement, so gate tightness is measurable and tunable.
- **Verdict power belongs to the user**: the AI only proposes; the user clicks the verdict (strong-accept / accept / indifferent / reject, one card per question). Strong-accept triggers the Hebbian ×2 weight, and must point at a concrete location (structural criterion — intensity adjectives are banned).
- **Weights are script-computed, never model-computed**: Hebbian learning, Zeigarnik keeping-warm, and forgetting decay are all deterministic script math.
- **Append-only**: card numbers never change once issued; bidirectional write-backs only append annotations — old text that cited a number can never point at the wrong card.
- **Host-agnostic**: the mechanism spec and scripts are plain files + command line; host-specific adaptations (e.g. for DSH) live in their own layer under `adapters/`.

## Five-minute quickstart

See [`examples/GETTING-STARTED.md`](examples/GETTING-STARTED.md) (Chinese): copy the synthetic mini-soup → lightning → settle a card → status page. Fully synthetic data, whole loop runs in minutes.

## Layout

```
primordial-soup\
  README.md / README.en.md   this file, bilingual
  LICENSE                    Apache-2.0
  spec\
    SOUP-MECHANISM.md        the mechanism spec (host-agnostic: range guard / folder contract / numbering / tag dimensions / lightning / settlement / sentinels / fast-track closure / maintenance)
    lightning-trigger.md     trigger design T1-T6 (when lightning fires, dedup criteria, settlement hooks, boundary table)
  scripts\
    闪电抽样器.py            M3 weighted sampling + wildcard slot (read-only, zero side effects)
    状态页生成器.py          generates _氨基酸库\状态页.html (pre-generated static page)
    M5结算脚本.py            effectiveness settlement (closed questions / strong-accepts / silence rate)
    潮汐周报生成器.py        weekly report md → HTML (with content reconciliation; exit 3 = missing sections)
  examples\
    mini-soup\               synthetic sample soup (all cards are fictional test data — copy and remix freely)
    GETTING-STARTED.md       quickstart walkthrough
  adapters\
    ds-harness\              adapter for a specific host (SKILL.md, INSTALL.md, porting notes)
```

## Script parameters (quick reference)

| Script | Parameter | Notes |
|---|---|---|
| 闪电抽样器.py | `root` (required) | absolute soup root; read-only, zero side effects |
| | `--exclude NAME` | remove before drawing, repeatable (exact → prefix-insensitive → unique-substring matching) |
| | `--seed N` | RNG seed; omit for system entropy (the reproduce command is printed) |
| | `--n N` | draw count, default 3 (2 weighted + 1 wildcard) |
| | `--hebb / --zeig-closed / --decay / --floor / --min-rows` | weight parameters (defaults 2.0 / 0.5 / 0.7 / 0.1 / 10) |
| | `--strict` | verify INDEX row count == card folders on disk |
| 状态页生成器.py | `root` (required) | default output `<root>\_氨基酸库\状态页.html` |
| | `--stamp` | fixed timestamp (`"YYYY-MM-DD HH:MM"` or `fixed`); omit = now |
| M5结算脚本.py | `root` (required) | reuses the sampler's parse section for settlement (explicit errors on spawn failure / 9009 / empty output) |
| | `--sampler PATH` | explicit sampler path (default `<root>\_氨基酸库\闪电抽样器.py`) |
| 潮汐周报生成器.py | `<report.md> [output.html]` | field lines must be `- 【label】text`; exit 3 = reconciliation gap |

The weight formula structure, the four incremental gate criteria, silence-auditability, and append-only write-backs are mechanism invariants — deliberately not parameterized.

## Design principles

1. **True randomness**: only the sampler may be random (entropy or `--seed`); the model must not pick cards.
2. **Presentation gate**: fail the incremental test and stay completely silent — no mention, no explanation, no ritual trace.
3. **Auditable silence**: silent draws are logged anyway; the silence rate feeds M5 settlement, so gate tightness can be calibrated with data.
4. **User holds the verdict**: AI recommendations are proposals; the click is the verdict. Strong-accept must cite a concrete location (structural criterion, no intensity adjectives).
5. **Script math, model no-discretion**: Hebbian ×2 / Zeigarnik keeping-warm / forgetting decay are all computed deterministically by scripts.

## Adapters

The spec and scripts are host-agnostic; adaptations to a specific host (agent runtime / workspace conventions / interaction tools / scheduling) live under `adapters/`:

- `adapters/ds-harness/` — for the DSH host: `SKILL.md` (full skill), `INSTALL.md` (install locations / hot reload / two script-distribution modes), `PORTING-NOTES.md` (porting checklist + design notes: dependency mapping, script-level findings, contract baselines, R1-R7 work orders).

## Provenance

The mechanism and scripts were battle-tested in a private deployment before being open-sourced. This public repository contains no private data — the sample soup (`examples/mini-soup/`) is entirely synthetic and fictional.

## License

[Apache-2.0](LICENSE), Copyright 2026 primordial-soup contributors.
