# Phase 4 — Evals

## Goal
Replace "seems fine" with numbers. Build a repeatable eval harness that scores the agent on a golden dataset and blocks regressions.

## Concepts
- **Eval:** a test for AI behavior. Dataset of inputs + expected properties → run the system → score the outputs.
- **Golden set:** curated, trusted examples. Quality over quantity: 40–60 good cases beat 500 sloppy ones.
- **Grader types**
  - *Code graders:* exact match, contains/regex, "cited doc id is in expected set". Cheap and deterministic. Use them first.
  - *LLM-as-judge:* another model call scores against a rubric. Needed for open-ended quality (faithfulness, helpfulness). It's noisy, so validate it against your own labels.
  - *Human review:* the ground truth for calibrating the others.
- **Retrieval evals vs. generation evals:** score the retriever separately (did the right chunk come back? recall@k, MRR) from the answer (faithful? correct? cited?). Otherwise you can't tell what broke.
- **Faithfulness / groundedness:** every claim is supported by the retrieved context.
- **Regression gate:** CI fails if scores drop below a threshold.
- **Overfitting to your eval:** if you tune until the set passes, hold out a test split you don't tune on.

## Requirements
- `evals/datasets/qa.jsonl` with ≥40 cases. Each has: `id`, `question`, `audience`, `category` (answerable / unanswerable / conflicting / adversarial), `expected_doc_ids`, `reference_answer` or `must_include` facts, `should_abstain` (bool).
- A **train/dev split** (tune on dev) and a **held-out test** split.
- Code graders: retrieval recall@k, citation validity, abstention correctness, must-include facts.
- LLM judge for faithfulness and answer correctness with a written rubric and structured (JSON) output.
- `evals/run_evals.py`: runs the dataset concurrently with a rate limit, prints a summary table, writes results JSON, and pushes scores to Langfuse.
- Cost of each eval run is printed.

## Steps
1. Convert your Phase 3 notes (the 20 trial questions) into dataset rows, then grow to ≥40. Include every failure you saw. Write the expected answers yourself from the corpus.
2. Build the runner. Start with sequential and simple. Then add `asyncio` / a thread pool with a concurrency limit.
3. Implement code graders first and get a baseline score table.
4. Retrieval metrics: compute recall@k and MRR from `expected_doc_ids`. Compare with the vector-only baseline.
5. Write the judge prompt: rubric with explicit 1–5 or pass/fail criteria, the context, the answer, and the reference. Ask for reasoning *then* a score in JSON. Use structured outputs (`output_config` with a JSON schema, or `client.messages.parse` with a pydantic model. Check the SDK docs).
6. **Calibrate the judge:** hand-label 15 cases yourself, compare to the judge, and compute agreement. Adjust the rubric until you trust it. Keep the judge model fixed and note it in the results.
7. Add Langfuse **datasets** and **experiments**/scores so runs appear side by side in the UI. Tag each run with `prompt_version` and git commit.
8. Use it: re-run the Phase 3 experiments (chunk size, k, hybrid, rerank, prompt tweaks), one at a time, and record the deltas in a table in `NOTES.md`.
9. Add a `pytest` test or script that fails if the score falls below thresholds (e.g. citation validity ≥ 0.95, abstention ≥ 0.9). Wire it into a `Makefile`/`just` target. CI comes in Phase 15.
10. Measure run-to-run variance by running the eval 3 times without changes. If the score swings by 5 points, small improvements are noise.

## Checkpoint
- [ ] One command produces a score table by category.
- [ ] You have a baseline number and at least 3 experiments with measured deltas.
- [ ] Judge agrees with your labels on ≥80% of the calibration cases.
- [ ] You know the variance of your eval.
- [ ] A deliberately broken prompt makes the gate fail.

## Stretch
- Pairwise comparison judge ("A vs B") with position-swapping to remove order bias.
- Add synthetic test generation, then review everything by hand before adding it to the set.
- Online evals: sample production traces and score them automatically in Langfuse.

## Pitfalls
- The judge sees the reference and rubber-stamps similar wording. Judge meaning, not phrasing.
- Leaking eval answers into the prompt or the corpus.
- Using the same model as generator and judge without checking for self-preference bias.
- Dataset skewed toward easy questions.
- Treating a 1-point gain as real without knowing the variance.

## Reading
Anthropic's "Define success and build evaluations" docs; Hamel Husain's writing on evals; Langfuse docs on datasets and experiments.
