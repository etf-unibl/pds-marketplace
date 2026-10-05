"""Explanations of the commands used in the course workflow (git, gh, course tools).

Student plugins never run commands that change state; they show the command and explain it with
this table: what it does, why it is needed in the course workflow, how to check the result and
how to undo it. Texts exist in Serbian (sr) and English (en).
"""

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


def _resolve(key):
    entry = COMMANDS[key]
    return COMMANDS[entry["alias"]] if "alias" in entry else entry


def explain_command(command, lang="en"):
    """Explains a command line: the best matching course command, whether it changes anything, and how to check and undo it."""
    lang = "sr" if lang == "sr" else "en"
    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    best = None
    for key in COMMANDS:
        kw = key.split()
        if words[:len(kw[:2])] == kw[:2] and all(k in words for k in kw[2:]):
            if best is None or (len(kw), len(key)) > (len(best.split()), len(best)):
                best = key
    if not best:
        return {"ok": False, "command": command, "message": "Not a command of the course workflow; explain it from the git documentation (git help <command>).",
                "known": sorted(COMMANDS)}
    entry = _resolve(best)
    return {"ok": True, "command": command, "matched": best, "changes_repository": entry["changes"], **entry[lang],
            "rule": ("The assistant does not run this command; run it yourself and then check the result."
                     if entry["changes"] else "Read-only command.")}


def is_state_changing(command):
    """True if the command changes the repository or GitHub (used by the student plugin guard hook)."""
    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    if not words:
        return False
    if words[0] == "git":
        sub = next((w for w in words[1:] if not w.startswith("-")), "")
        if sub in ("status", "log", "diff", "show", "fetch", "ls-files", "ls-tree", "rev-parse", "blame", "describe", "shortlog", "reflog", "grep", "help", "version"):
            return False
        if sub == "branch" and all(w.startswith("-") and w in ("--show-current", "-a", "-r", "-v", "-vv", "--list", "--all") for w in words[2:]):
            return False
        if sub == "remote" and (len(words) == 2 or words[2] in ("-v", "show", "get-url")):
            return False
        if sub == "config" and any(w in ("--get", "--list", "-l", "--get-all") for w in words):
            return False
        if sub == "stash" and len(words) > 2 and words[2] in ("list", "show"):
            return False
        return True
    if words[0] == "gh":
        if len(words) > 1 and words[1] == "api":
            # gh api is read-only only as a plain GET without fields or input
            method = next((words[i + 1] for i, w in enumerate(words[:-1]) if w in ("-X", "--method")), "GET")
            writes = any(w in ("-f", "-F", "--field", "--raw-field", "--input") or w.startswith(("-f=", "-F=", "--field=", "--raw-field=", "--input=", "--method=")) for w in words)
            return method.upper() != "GET" or writes
        sub = " ".join(words[1:3])
        return not any(sub.startswith(s) for s in ("pr view", "pr list", "pr checks", "pr diff", "pr status", "issue view", "issue list", "run view", "run list", "repo view", "auth status"))
    if words[0] == "vhdl-style":
        return "--fix" in words
    return False
