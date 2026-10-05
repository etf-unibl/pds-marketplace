---
name: glossary
description: Look up PDS course terms in the glossary built from the "Key terms" sections of the topic pages (Serbian and English, with the topic where each is explained), and translate technical terms between Serbian and English. Use when the student asks what a term means or how it is called in the other language.
---

# Glossary

{{include teach-rule}}

## Steps

1. `glossary "<term>"` searches the key terms of all topic pages (term, alternative names in brackets, short explanation, topic). Without a term it returns the whole glossary (about 110 terms).
2. Answer with the course definition, the topic page where it is explained (`docs/topics/...`) and, when useful, the video moment (`topics_search "<term>"`).
3. For translations: the Serbian pages keep many English terms (testbench, pipeline, slack) and give English names in brackets (e.g. *leč* (*latch*)); explain which form the course uses. If the term is not in the glossary, say so and explain it, marking that the explanation is not from the course pages.
4. On request, build a short revision list of terms for a topic (`glossary` filtered by the topic number in the results).
