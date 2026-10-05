---
name: quiz
description: Quiz the student with the self-check questions of the PDS topic pages and help prepare for the course test - asks one question at a time, waits for the answer, then compares it with the course answer and explains. Use when the student wants to practise, revise a lecture or prepare for the test.
---

# Self-check and test preparation

{{include teach-rule}}

## Steps

1. Ask which lectures to cover (`topics_list` shows the 15 topics); for the test, cover all of them or the ones the student finds hardest.
2. `quiz <topic>` returns the questions **without** answers. Ask one question at a time and wait for the student's answer. Never show the answer before the student has tried.
3. After the answer, get the course answer with `quiz <topic> reveal_answers=true`, compare it with the student's answer and explain what was right, what was missing or wrong, and where to read more (`topic_get <n> explanation`, the video moment from `topics_search`).
4. Mix in short questions of your own about the same concepts (e.g. "how many registers does this process infer?", "what does this assignment synthesize to?"), clearly marked as not from the course pages, and the glossary terms (`glossary`).
5. At the end, summarize which topics to revise, with links to the topic pages and videos.

Keep score only if the student wants it. Ask in the language the student uses; the course pages are in the language of the course repository.
