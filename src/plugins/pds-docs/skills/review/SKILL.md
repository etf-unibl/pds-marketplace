---
name: review
description: Review the design documentation (Doxygen --! comments) of a PDS assignment - missing or incomplete descriptions, TODO placeholders left, Doxygen pitfalls (comment without @brief, blank line inside a comment, trailing comments joined with the next line, shared declarations, unlabeled processes, comments Doxygen drops, plain -- comments) and whether the descriptions match the code. Advice only, the student corrects. Use when the student asks whether the documentation is complete or good, before submitting, or when the published pages look wrong.
---

# Documentation review

Review the student's documentation and explain how to improve it. Never change the file and never write the descriptions for the student.

## Steps

1. **`docs_check`** on the task folder (`assignments/<N>`) or the file. It checks the course requirements (`docs/design-documentation.md`, "Šta je potrebno dokumentovati") and the pitfalls of Doxygen's VHDL parser, checked with Doxygen 1.9.5 (GitHub Pages).
2. **Explain the findings**, `required` first, then `recommended`, each with the line, what Doxygen does with it and the fix:
   - `file_doc_missing`, `brief_missing`, `details_missing`, `todo_left`: what is missing and what it should say (questions about the design, not the text);
   - `multi_line_without_brief`: several `--!` lines without `@brief` become only the detailed description, the summary stays empty; show the form `--! @brief ...` / `--! @details ...`;
   - `split_block`: a blank line inside a comment, Doxygen shows `@details` as text ("unknown command" warning);
   - `merged_comment`: a `--!` comment at the end of a line followed by `--!` lines: Doxygen joins them and attaches both to the next element; one style per clause;
   - `shared_declaration`, `process_without_label`, `orphan_doc`, `long_brief`, a plain `--` comment that should be `--!`.
   For syntax problems you may show the corrected comment form (the student applies it); for content give advice and questions.
3. **Read the code against the comments** (the tool cannot judge content). Point out:
   - a description that does not match the code: wrong direction, width, active level, clock edge, synchronous vs. asynchronous reset, a comment left from an earlier version or copied from another signal;
   - a description that only repeats the name (`y_o : output y`): say what is missing (meaning, encoding, when it is valid);
   - entity details that do not say what the circuit does, how it is used and its timing (latency, when outputs are valid); architecture details that do not explain the implementation;
   - TODO placeholders of a skeleton, briefs the student has not checked, mixed languages.
4. **Next steps:** the student corrects the comments, runs `docs_check` again (you call it), `style_report <N>`, and the `preview` skill to see the pages. After the merge into `assignments`, the published pages (`https://<organization>.github.io/<repository>/`) show the same.

{{include docs-rule}}

{{include teach-rule}}

{{include course-context}}
