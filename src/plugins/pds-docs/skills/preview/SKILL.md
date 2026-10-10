---
name: preview
description: Build the Doxygen HTML documentation of a PDS assignment locally with the course Doxyfile, to see the pages before GitHub Pages publishes them - where the design is, how the briefs and details are shown, Doxygen warnings. Use when the student wants to see their documentation, asks how it will look, or asks how to run Doxygen.
---

# Documentation preview

## Steps

1. **`docs_preview`** with the task folder (`assignments/<N>`), or without a path for all of `assignments/` as GitHub Pages builds it. It uses `assignments/Doxyfile` unchanged and writes the pages to `<repository>-docs` next to the repository, so nothing new appears in `git status`.
2. **Doxygen missing** (`ok: false`): explain the installation from the course guide (`course_doc design-documentation`, "Lokalni pregled dokumentacije"): https://www.doxygen.nl/download.html, on Windows the setup program or `winget install DimitriVanHeesch.Doxygen`, then a new terminal and the AI tool started again. The student installs it.
3. **Show the result:**
   - the index page and the pages of the design units (`pages`), to open in a web browser; the designs are in the menu **Design Unit List**;
   - on a page: the brief in the summary tables (ports, signals, processes), the details below; a missing brief leaves an empty cell, a missing comment an undocumented row;
   - Doxygen `warnings`, explained (e.g. "unknown command '@details'" is a blank line inside a comment);
   - `version_note`, if the local Doxygen differs from the one of GitHub Pages.
4. **The command of the course guide**, so the student can do it without the assistant: in `assignments/` run `doxygen Doxyfile` and open `assignments/html/index.html` (`html/` is in `.gitignore`, not committed).
5. If something looks wrong on the page, use the `review` skill (`docs_check`) to find the cause in the comments.

{{include docs-rule}}

{{include teach-rule}}

{{include course-context}}
