"""Explanations of the commands used in the course workflow (git, gh, course tools, Quartus).

Student plugins never run commands that change state; they show the command and explain it with
this table: what it does, why it is needed in the course workflow, how to check the result and
how to undo it. Texts exist in Serbian (sr) and English (en).
"""

import re
import shlex

COMMANDS = {
    "git clone": {
        "changes": True,
        "en": {"does": "Copies a repository from GitHub into a new folder, with its whole history.",
               "why": "Every student works in a local copy of the course repository.",
               "check": "cd into the new folder and run git status.",
               "undo": "Delete the folder (nothing on GitHub changes)."},
        "sr": {"does": "Kopira repozitorijum sa GitHub-a u novi folder, sa kompletnom istorijom.",
               "why": "Svaki student radi u lokalnoj kopiji repozitorijuma kursa.",
               "check": "Uđite u novi folder i pokrenite git status.",
               "undo": "Obrišite folder (na GitHub-u se ništa ne mijenja)."}},
    "git config core.hooksPath": {
        "changes": True,
        "en": {"does": "Tells git to use the hooks in the .githooks folder of the repository.",
               "why": "The course hooks check the commit message format and that only assignments/<N>/ is changed, before the commit is made.",
               "check": "git config --get core.hooksPath should print .githooks.",
               "undo": "git config --unset core.hooksPath"},
        "sr": {"does": "Podešava git da koristi hook-ove iz foldera .githooks repozitorijuma.",
               "why": "Hook-ovi kursa prije komita provjeravaju format poruke i da je izmijenjen samo folder assignments/<N>/.",
               "check": "git config --get core.hooksPath treba da ispiše .githooks.",
               "undo": "git config --unset core.hooksPath"}},
    "git fetch": {
        "changes": False,
        "en": {"does": "Downloads new commits and branches from GitHub without changing your files or your branch.",
               "why": "Needed before creating a branch from the latest assignments branch or before reading origin/main.",
               "check": "git log --oneline -3 origin/assignments", "undo": "Nothing to undo."},
        "sr": {"does": "Preuzima nove komite i grane sa GitHub-a, bez izmjene vaših fajlova i grane.",
               "why": "Potrebno prije pravljenja grane od najnovije grane assignments ili prije čitanja origin/main.",
               "check": "git log --oneline -3 origin/assignments", "undo": "Nema šta da se poništi."}},
    "git switch -c": {
        "changes": True,
        "en": {"does": "Creates a new branch at the given start point and switches to it.",
               "why": "Each issue is solved on its own branch whose name starts with the issue number (e.g. 12-nand2), made from origin/assignments.",
               "check": "git branch --show-current", "undo": "git switch assignments, then git branch -d <name> (only if nothing was committed)."},
        "sr": {"does": "Pravi novu granu od zadate tačke i prelazi na nju.",
               "why": "Svaki zadatak se rješava na svojoj grani čiji naziv počinje brojem zadatka (npr. 12-nand2), napravljenoj od origin/assignments.",
               "check": "git branch --show-current", "undo": "git switch assignments, zatim git branch -d <naziv> (samo ako nije bilo komita)."}},
    "git checkout -b": {"alias": "git switch -c"},
    "git add": {
        "changes": True,
        "en": {"does": "Stages changes: the next commit will contain them.",
               "why": "Only files in assignments/<N>/ belong in the commit; add them by path, not with git add . at the repository root.",
               "check": "git status (files under 'Changes to be committed').", "undo": "git restore --staged <file>"},
        "sr": {"does": "Priprema izmjene za komit (staging): sljedeći komit će ih sadržati.",
               "why": "U komit idu samo fajlovi iz assignments/<N>/; dodajte ih navođenjem putanje, a ne sa git add . iz korijena repozitorijuma.",
               "check": "git status (fajlovi pod 'Changes to be committed').", "undo": "git restore --staged <fajl>"}},
    "git restore --staged": {
        "changes": True,
        "en": {"does": "Removes a file from the staging area; the file itself is not changed.",
               "why": "Used when a file outside assignments/<N>/ was added by mistake (the pre-commit hook rejects such a commit).",
               "check": "git status", "undo": "git add <file>"},
        "sr": {"does": "Uklanja fajl iz pripreme za komit; sam fajl se ne mijenja.",
               "why": "Koristi se kada je greškom dodat fajl van assignments/<N>/ (pre-commit hook odbija takav komit).",
               "check": "git status", "undo": "git add <fajl>"}},
    "git commit -s": {
        "changes": True,
        "en": {"does": "Records the staged changes as a commit; -s adds 'Signed-off-by: <name> <e-mail>' from your git configuration.",
               "why": "Every commit must be signed off and use the format 'Issue #<N> : <issue title>', an empty line and '- ' items; the hooks and CI check it.",
               "check": "git log -1 (message, author, sign-off).", "undo": "git reset --soft HEAD~1 (keeps the changes staged; only before push)."},
        "sr": {"does": "Snima pripremljene izmjene kao komit; -s dodaje 'Signed-off-by: <ime> <e-mail>' iz git podešavanja.",
               "why": "Svaki komit mora biti potpisan i imati format 'Issue #<N> : <naziv zadatka>', praznu liniju i stavke '- '; provjeravaju ga hook-ovi i CI.",
               "check": "git log -1 (poruka, autor, potpis).", "undo": "git reset --soft HEAD~1 (izmjene ostaju pripremljene; samo prije push)."}},
    "git commit --amend": {
        "changes": True,
        "en": {"does": "Replaces the last commit with a new one (changed message and/or added staged changes).",
               "why": "Fixes the message or sign-off of the last commit (git commit --amend -s).",
               "check": "git log -1", "undo": "git reset --soft HEAD@{1}. After a push the branch must be pushed with --force-with-lease."},
        "sr": {"does": "Zamjenjuje posljednji komit novim (izmijenjena poruka i/ili dodate pripremljene izmjene).",
               "why": "Ispravlja poruku ili potpis posljednjeg komita (git commit --amend -s).",
               "check": "git log -1", "undo": "git reset --soft HEAD@{1}. Nakon push-a grana se mora poslati sa --force-with-lease."}},
    "git push -u": {
        "changes": True,
        "en": {"does": "Sends the commits of the branch to GitHub; -u links the local branch with origin/<branch> for later git push and git pull.",
               "why": "The pull request is opened from the branch on GitHub; the checks run on the pushed commits.",
               "check": "git status ('Your branch is up to date with origin/...').", "undo": "Pushed commits stay on GitHub; fix them with new commits."},
        "sr": {"does": "Šalje komite grane na GitHub; -u povezuje lokalnu granu sa origin/<grana> za kasnije git push i git pull.",
               "why": "Pull request se otvara iz grane na GitHub-u; provjere se pokreću nad poslatim komitima.",
               "check": "git status ('Your branch is up to date with origin/...').", "undo": "Poslati komiti ostaju na GitHub-u; ispravljaju se novim komitima."}},
    "git push --force-with-lease": {
        "changes": True,
        "en": {"does": "Overwrites the branch on GitHub with your local branch, but only if nobody else pushed to it since your last fetch.",
               "why": "Needed after rewriting already pushed commits (amend, rebase); safer than --force.",
               "check": "git status and the commits of the pull request on GitHub.", "undo": "Difficult; the old commits remain only in the reflog (git reflog)."},
        "sr": {"does": "Prepisuje granu na GitHub-u lokalnom granom, ali samo ako niko drugi nije slao izmjene od vašeg posljednjeg fetch-a.",
               "why": "Potrebno nakon prepravke već poslatih komita (amend, rebase); sigurnije od --force.",
               "check": "git status i komiti pull request-a na GitHub-u.", "undo": "Teško; stari komiti ostaju samo u reflog-u (git reflog)."}},
    "git pull": {
        "changes": True,
        "en": {"does": "fetch + merge: brings commits from GitHub into your current branch.",
               "why": "Used when the branch was changed on GitHub (e.g. by a team member or the web editor).",
               "check": "git log --oneline -5", "undo": "git reset --hard ORIG_HEAD (discards the merge; uncommitted work is lost)."},
        "sr": {"does": "fetch + merge: unosi komite sa GitHub-a u vašu trenutnu granu.",
               "why": "Koristi se kada je grana izmijenjena na GitHub-u (npr. član tima ili web editor).",
               "check": "git log --oneline -5", "undo": "git reset --hard ORIG_HEAD (poništava merge; nekomitovan rad se gubi)."}},
    "git merge": {
        "changes": True,
        "en": {"does": "Joins another branch into the current one, with a merge commit if needed.",
               "why": "Brings the latest assignments branch (e.g. a new test) into your issue branch: git merge origin/assignments.",
               "check": "git log --oneline --graph -10", "undo": "During a conflict: git merge --abort. After: git reset --hard ORIG_HEAD (before push)."},
        "sr": {"does": "Spaja drugu granu sa trenutnom, uz merge komit ako je potrebno.",
               "why": "Unosi najnoviju granu assignments (npr. novi test) u granu zadatka: git merge origin/assignments.",
               "check": "git log --oneline --graph -10", "undo": "Tokom konflikta: git merge --abort. Nakon toga: git reset --hard ORIG_HEAD (prije push)."}},
    "git rebase": {
        "changes": True,
        "en": {"does": "Moves your commits on top of another branch, rewriting them.",
               "why": "Not needed in the course workflow; prefer merge. After a rebase of pushed commits a force push is needed.",
               "check": "git log --oneline --graph -10", "undo": "git rebase --abort during the rebase; afterwards git reset --hard ORIG_HEAD."},
        "sr": {"does": "Premješta vaše komite na vrh druge grane i pri tome ih prepravlja.",
               "why": "Nije potreban u radu na kursu; koristite merge. Nakon rebase-a poslatih komita potreban je force push.",
               "check": "git log --oneline --graph -10", "undo": "git rebase --abort tokom rebase-a; nakon toga git reset --hard ORIG_HEAD."}},
    "git reset --soft": {
        "changes": True,
        "en": {"does": "Moves the branch back to an earlier commit and keeps the changes staged.",
               "why": "Undoes the last commit(s) to redo the message or combine them, before they are pushed.",
               "check": "git status and git log --oneline -3", "undo": "git reset --soft ORIG_HEAD"},
        "sr": {"does": "Vraća granu na raniji komit, a izmjene ostavlja pripremljene za komit.",
               "why": "Poništava posljednji komit (ili više njih) da bi se poruka napisala ponovo ili komiti spojili, prije slanja.",
               "check": "git status i git log --oneline -3", "undo": "git reset --soft ORIG_HEAD"}},
    "git reset --hard": {
        "changes": True,
        "en": {"does": "Moves the branch and DISCARDS all uncommitted changes in tracked files.",
               "why": "Rarely needed; check git status first, because discarded changes cannot be recovered.",
               "check": "git status", "undo": "Committed work: git reflog and git reset --hard <sha>. Uncommitted work is lost."},
        "sr": {"does": "Pomjera granu i BRIŠE sve nekomitovane izmjene praćenih fajlova.",
               "why": "Rijetko potrebno; prvo provjerite git status, jer se obrisane izmjene ne mogu vratiti.",
               "check": "git status", "undo": "Komitovan rad: git reflog i git reset --hard <sha>. Nekomitovan rad je izgubljen."}},
    "git status": {"changes": False,
                   "en": {"does": "Shows the branch, its relation to GitHub and which files are changed, staged or untracked.", "why": "Run it before and after every step.", "check": "-", "undo": "-"},
                   "sr": {"does": "Prikazuje granu, njen odnos prema GitHub-u i koji fajlovi su izmijenjeni, pripremljeni ili nepraćeni.", "why": "Pokrenite ga prije i poslije svakog koraka.", "check": "-", "undo": "-"}},
    "git log": {"changes": False,
                "en": {"does": "Shows the commit history (e.g. git log --oneline -5, git log -1 for the full last message).", "why": "Checks commit messages and sign-offs before pushing.", "check": "-", "undo": "-"},
                "sr": {"does": "Prikazuje istoriju komita (npr. git log --oneline -5, git log -1 za kompletnu posljednju poruku).", "why": "Provjera poruka i potpisa komita prije slanja.", "check": "-", "undo": "-"}},
    "git diff": {"changes": False,
                 "en": {"does": "Shows changes: not staged (git diff) or staged (git diff --staged).", "why": "Review what goes into the commit.", "check": "-", "undo": "-"},
                 "sr": {"does": "Prikazuje izmjene: nepripremljene (git diff) ili pripremljene (git diff --staged).", "why": "Pregled onoga što ide u komit.", "check": "-", "undo": "-"}},
    "vhdl-style --fix": {
        "changes": True,
        "en": {"does": "Rewrites the VHDL files to fix the style violations that can be fixed automatically, then checks again.",
               "why": "Saves manual formatting; the remaining violations must be fixed by hand.",
               "check": "git diff (review every change) and vhdl-style <N>.", "undo": "git restore <file> (before commit)."},
        "sr": {"does": "Prepravlja VHDL fajlove da ispravi greške stila koje se mogu automatski ispraviti, pa ponovo provjerava.",
               "why": "Štedi ručno formatiranje; preostale greške se ispravljaju ručno.",
               "check": "git diff (pregledajte svaku izmjenu) i vhdl-style <N>.", "undo": "git restore <fajl> (prije komita)."}},
    "gh pr create": {
        "changes": True,
        "en": {"does": "Opens a pull request from the current branch on GitHub.",
               "why": "Submission of the solution; the title must be 'Issue #<N> : <issue title>' and the description must follow the template.",
               "check": "gh pr view and the checks on the pull request page.", "undo": "gh pr close (the branch stays)."},
        "sr": {"does": "Otvara pull request iz trenutne grane na GitHub-u.",
               "why": "Predaja rješenja; naslov mora biti 'Issue #<N> : <naziv zadatka>', a opis mora pratiti šablon.",
               "check": "gh pr view i provjere na stranici pull request-a.", "undo": "gh pr close (grana ostaje)."}},
}

def _quartus(en, sr):
    return {"changes": False, "kind": "quartus", "en": en, "sr": sr}


# Quartus command-line tools: they work in the Quartus project folder outside the repository (course
# rule) and never change the repository; the pds-quartus tools run them and show these command lines
COMMANDS.update({
    "quartus_sh -t": _quartus(
        {"does": "Runs a Tcl script in the Quartus shell; create_project.tcl, for example, creates the project: device, top-level entity, VHDL files, pins and the SDC file.",
         "why": "A project made from a script can be re-created exactly, and it is kept outside the repository (course rule), so nothing Quartus generates ends up in a commit.",
         "check": "The .qpf and .qsf files appear in the project folder and quartus_sh prints 'Evaluation of Tcl script ... was successful'.",
         "undo": "Delete the project folder: it is outside the repository and only references the VHDL files."},
        {"does": "Pokreće Tcl skriptu u Quartus shell-u; create_project.tcl, na primjer, pravi projekat: čip, top-level entitet, VHDL fajlove, pinove i SDC fajl.",
         "why": "Projekat napravljen skriptom može se tačno ponoviti, a drži se van repozitorijuma (pravilo kursa), pa ništa što Quartus generiše ne završi u komitu.",
         "check": "U folderu projekta se pojave fajlovi .qpf i .qsf, a quartus_sh ispiše 'Evaluation of Tcl script ... was successful'.",
         "undo": "Obrišite folder projekta: van repozitorijuma je i VHDL fajlove samo referencira."}),
    "quartus_sh --flow compile": _quartus(
        {"does": "Full compilation: Analysis & Synthesis, Fitter, Assembler and Timing Analyzer; produces output_files/<top>.sof.",
         "why": "Needed before timing analysis and before programming the board; to check only that the design synthesizes, quartus_map is enough.",
         "check": "'Quartus Prime Full Compilation was successful', the reports in output_files/ (flow, map, fit, sta) and the .sof file.",
         "undo": "The repository does not change; delete output_files/, db/ and incremental_db/ in the project folder to start clean."},
        {"does": "Kompletna kompilacija: Analysis & Synthesis, Fitter, Assembler i Timing Analyzer; pravi output_files/<top>.sof.",
         "why": "Potrebna prije analize vremenskih parametara i prije programiranja ploče; za provjeru da li se dizajn sintetiše dovoljan je quartus_map.",
         "check": "'Quartus Prime Full Compilation was successful', izvještaji u output_files/ (flow, map, fit, sta) i fajl .sof.",
         "undo": "Repozitorijum se ne mijenja; za čist početak obrišite output_files/, db/ i incremental_db/ u folderu projekta."}),
    "quartus_map": _quartus(
        {"does": "Analysis & Synthesis: checks the VHDL, infers the hardware (registers, latches, multiplexers, adders) and maps it to the logic of the device.",
         "why": "The fastest check that a design synthesizes; its warnings point to design errors such as inferred latches and incomplete sensitivity lists.",
         "check": "output_files/<top>.map.rpt: the Analysis & Synthesis Summary and the warnings.",
         "undo": "The repository does not change; the reports are rewritten by the next run."},
        {"does": "Analysis & Synthesis: provjerava VHDL, prepoznaje hardver (registre, lečeve, multipleksere, sabirače) i preslikava ga na logiku čipa.",
         "why": "Najbrža provjera da li se dizajn sintetiše; njena upozorenja ukazuju na greške u dizajnu, kao što su lečevi i nepotpune liste osjetljivosti.",
         "check": "output_files/<top>.map.rpt: Analysis & Synthesis Summary i upozorenja.",
         "undo": "Repozitorijum se ne mijenja; sljedeće pokretanje ponovo piše izvještaje."}),
    "quartus_fit": _quartus(
        {"does": "Fitter: places the synthesized logic in the chip, routes the connections and applies the pin assignments.",
         "why": "Runs after synthesis; only after fitting are the real delays and the pin usage known.",
         "check": "output_files/<top>.fit.rpt: resource usage, pins and the I/O assignment warnings.",
         "undo": "The repository does not change."},
        {"does": "Fitter: raspoređuje sintetisanu logiku u čipu, povezuje veze i primjenjuje dodjelu pinova.",
         "why": "Pokreće se nakon sinteze; tek nakon raspoređivanja poznata su stvarna kašnjenja i korišćenje pinova.",
         "check": "output_files/<top>.fit.rpt: zauzeće resursa, pinovi i upozorenja o dodjeli ulaza i izlaza.",
         "undo": "Repozitorijum se ne mijenja."}),
    "quartus_asm": _quartus(
        {"does": "Assembler: writes the programming file output_files/<top>.sof from the fitted design.",
         "why": "The .sof is what quartus_pgm loads into the FPGA.",
         "check": "output_files/<top>.sof exists and output_files/<top>.asm.rpt reports success.",
         "undo": "The repository does not change."},
        {"does": "Assembler: od raspoređenog dizajna piše fajl za programiranje output_files/<top>.sof.",
         "why": "Fajl .sof je ono što quartus_pgm upisuje u FPGA.",
         "check": "Postoji output_files/<top>.sof, a output_files/<top>.asm.rpt prijavljuje uspjeh.",
         "undo": "Repozitorijum se ne mijenja."}),
    "quartus_sta -t": _quartus(
        {"does": "Runs a Tcl script in the Timing Analyzer; pds_timing.tcl, for example, reads the SDC constraints and reports slack and Fmax per clock, the worst paths and the input-to-output delays.",
         "why": "Timing analysis of the course: the script stays in the project folder, so it can be read, changed and run again.",
         "check": "The pds_*.txt reports in the project folder (setup and hold summary, Fmax, paths, unconstrained paths).",
         "undo": "The repository does not change; the script only writes reports."},
        {"does": "Pokreće Tcl skriptu u Timing Analyzer-u; pds_timing.tcl, na primjer, čita SDC ograničenja i prijavljuje slack i Fmax po taktu, najgore putanje i kašnjenja od ulaza do izlaza.",
         "why": "Analiza vremenskih parametara na kursu: skripta ostaje u folderu projekta, pa se može pročitati, izmijeniti i ponovo pokrenuti.",
         "check": "Izvještaji pds_*.txt u folderu projekta (setup i hold sažetak, Fmax, putanje, neograničene putanje).",
         "undo": "Repozitorijum se ne mijenja; skripta samo piše izvještaje."}),
    "quartus_sta": _quartus(
        {"does": "Timing analysis of a compiled project with the default reports (the summary per clock).",
         "why": "Part of the full compilation; for the worst paths and the input-to-output delays use a script (quartus_sta -t pds_timing.tcl).",
         "check": "output_files/<top>.sta.rpt and .sta.summary.",
         "undo": "The repository does not change."},
        {"does": "Analiza vremenskih parametara kompajliranog projekta sa podrazumijevanim izvještajima (sažetak po taktu).",
         "why": "Dio kompletne kompilacije; za najgore putanje i kašnjenja od ulaza do izlaza koristite skriptu (quartus_sta -t pds_timing.tcl).",
         "check": "output_files/<top>.sta.rpt i .sta.summary.",
         "undo": "Repozitorijum se ne mijenja."}),
    "quartus_pgm -l": _quartus(
        {"does": "Lists the programming cables (USB-Blaster) that Quartus sees.",
         "why": "Check before programming that the board is connected, switched on and its driver installed.",
         "check": "A numbered line such as '1) DE-SoC [USB-1]'.",
         "undo": "Nothing to undo."},
        {"does": "Ispisuje kablove za programiranje (USB-Blaster) koje Quartus vidi.",
         "why": "Provjera prije programiranja da je ploča povezana, uključena i da je drajver instaliran.",
         "check": "Numerisana linija, na primjer '1) DE-SoC [USB-1]'.",
         "undo": "Nema šta da se poništi."}),
    "quartus_pgm -c": _quartus(
        {"does": "Programs the FPGA over JTAG with a .sof file, e.g. -m JTAG -o \"p;output_files/<top>.sof@2\" (@2: on the DE1-SoC the FPGA is the second device of the chain, after the HPS).",
         "why": "Puts the design on the board to test it with switches, keys, LEDs and displays.",
         "check": "'Configuration succeeded' and the board behaves as designed.",
         "undo": "Switch the board off (the configuration is volatile) or program another .sof."},
        {"does": "Programira FPGA preko JTAG-a fajlom .sof, npr. -m JTAG -o \"p;output_files/<top>.sof@2\" (@2: na DE1-SoC ploči FPGA je drugi uređaj u lancu, poslije HPS-a).",
         "why": "Postavlja dizajn na ploču radi testiranja prekidačima, tasterima, LED diodama i displejima.",
         "check": "'Configuration succeeded' i ploča se ponaša kako je dizajnirano.",
         "undo": "Isključite ploču (konfiguracija se gubi) ili programirajte drugi .sof."}),
})


def _resolve(key):
    entry = COMMANDS[key]
    return COMMANDS[entry["alias"]] if "alias" in entry else entry


def explain_command(command, lang="en"):
    """Explains a command line: the best matching course command, whether it changes anything, and how to check and undo it.
    Commands chained with && or || are explained one by one (parts)."""
    lang = "sr" if lang == "sr" else "en"
    chain = [c.strip() for c in re.split(r"&&|\|\||\n", command) if c.strip()]
    if len(chain) > 1:
        parts = [explain_command(c, lang) for c in chain]
        return {"ok": all(p["ok"] for p in parts), "command": command, "parts": parts}
    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    first = re.match(r'\s*(?:"([^"]+)"|(\S+))', command)
    if words and first:  # "C:\...\bin64\quartus_sh.exe" -> quartus_sh (shlex drops the backslashes)
        exe = (first.group(1) or first.group(2)).replace("\\", "/").rsplit("/", 1)[-1]
        words = [exe[:-4] if exe.lower().endswith(".exe") else exe] + words[1:]
    best = None
    for key in COMMANDS:
        kw = key.split()
        if words[:len(kw[:2])] == kw[:2] and all(k in words for k in kw[2:]):
            if best is None or (len(kw), len(key)) > (len(best.split()), len(best)):
                best = key
    if not best:
        return {"ok": False, "command": command, "message": "Not a command of the course workflow; explain it from its documentation (git help <command>, quartus_sh --help=<tool>).",
                "known": sorted(COMMANDS)}
    entry = _resolve(best)
    if entry.get("kind") == "quartus":
        rule = ("Changes only the Quartus project folder outside the repository (quartus_pgm: the board). The pds-quartus "
                "tools run it and show the command line; run it yourself in the project folder to repeat a step by hand.")
    elif entry["changes"]:
        rule = "The assistant does not run this command; run it yourself and then check the result."
    else:
        rule = "Read-only command."
    return {"ok": True, "command": command, "matched": best, "changes_repository": entry["changes"], **entry[lang], "rule": rule}


# Same classification as src/shared/guard.py (the guard hook of the student plugins); keep them equal
READ_ONLY_GIT = {"status", "log", "diff", "show", "fetch", "ls-files", "ls-tree", "rev-parse", "blame", "describe",
                 "shortlog", "reflog", "grep", "help", "version", "cat-file", "rev-list", "for-each-ref", "merge-base",
                 "symbolic-ref", "whatchanged", "count-objects"}
READ_ONLY_GH = ("pr view", "pr list", "pr checks", "pr diff", "pr status", "issue view", "issue list", "run view", "run list",
                "run watch", "repo view", "auth status", "browse")
GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}

def is_state_changing(command):
    """True if a single command changes the repository or GitHub."""
    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
        words = words[1:]  # VAR=value prefixes
    if not words:
        return False
    exe = words[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    exe = exe[:-4] if exe.endswith(".exe") else exe
    if exe == "git":
        rest, i = words[1:], 0
        while i < len(rest) and rest[i].startswith("-"):
            i += 2 if rest[i] in GIT_GLOBAL_WITH_VALUE else 1
        if i >= len(rest):
            return False
        sub, args = rest[i], rest[i + 1:]
        if sub in READ_ONLY_GIT:
            return False
        if sub == "branch" and all(a in ("--show-current", "-a", "-r", "-v", "-vv", "--list", "--all") or a.startswith("--contains") or a.startswith("--merged") for a in args):
            return False
        if sub == "remote" and (not args or args[0] in ("-v", "show", "get-url")):
            return False
        if sub == "config" and any(a in ("--get", "--list", "-l", "--get-all", "--get-regexp") for a in args):
            return False
        if sub == "stash" and args and args[0] in ("list", "show"):
            return False
        return True
    if exe == "gh":
        if len(words) > 1 and words[1] == "api":
            method = next((words[i + 1] for i, w in enumerate(words[:-1]) if w in ("-X", "--method")), "GET")
            writes = any(w in ("-f", "-F", "--field", "--raw-field", "--input") or w.startswith(("-f=", "-F=", "--field=", "--raw-field=", "--input=", "--method=")) for w in words)
            return method.upper() != "GET" or writes
        sub = " ".join(words[1:3])
        return not any(sub.startswith(s) for s in READ_ONLY_GH)
    if exe == "vhdl-style":
        return "--fix" in words
    return False
