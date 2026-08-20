# Evaluation strategy

RAG quality has at least two separable stages:

1. **Retrieval:** did the correct chunk appear above the relevance threshold?
2. **Generation:** did the model answer only from that evidence and cite it correctly?

The included smoke evaluation verifies two supported facts and one unsupported question. It is a regression check, not a claim of broad model accuracy.

## Useful metrics

- Recall@k for expected supporting chunks
- Mean reciprocal rank for the first relevant result
- Refusal precision/recall for out-of-scope questions
- Citation correctness and citation completeness
- Answer faithfulness to retrieved text
- End-to-end latency, embedding latency, and generation latency

## Building a meaningful dataset

Create questions from documents you are allowed to process. Include direct lookup, synthesis across chunks, similar-but-wrong distractors, unanswerable questions, prompt-injection text, tables, and content near page boundaries. Keep expected source/page labels beside expected answer concepts.

Do not tune the threshold on the same questions used for the final report. Split evaluation cases into development and held-out sets.

## Interpreting `grounded`

`grounded: true` means at least one result cleared the configured retrieval threshold and was supplied to the generator. It is not a mathematical guarantee that every sentence in the generated answer is faithful. Production systems should add automated citation verification or a second-stage evaluator.
