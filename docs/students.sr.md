# Dodaci za AI asistente za studente PDS-a

Dodaci (*plugin*-ovi) PDS-a uvode kurs u AI asistenta kojeg pokrećete u terminalu: poznaju tok rada na kursu, pravila koja provjeravaju automatske provjere, stranice tema video predavanja i kod primjera. Oni **uče, a ne rade umjesto vas**:

- komande koje mijenjaju vaš repozitorijum ili *GitHub* (komit, slanje izmjena, *pull request*, `vhdl-style --fix`) asistent prikazuje i objašnjava, a pokrećete ih **vi**;
- fajlove u folderu `assignments/` (rad koji se ocjenjuje) asistent ne mijenja;
- za zadatke koji se ocjenjuju dobijate savjete, objašnjenja i pregled sopstvenog koda, a ne rješenja.

Dodaci rade u alatima **Claude Code**, **GitHub Copilot CLI** i **Antigravity CLI**. Koristite onaj kojem imate pristup.

**Pravilo kursa:** kod koji je generisao AI alat, uključujući kod preuzet iz odgovora asistenta, mora biti naveden u poruci komita u kojem se nalazi, uz objašnjenje kako je alat korišćen: linija iznad potpisa, po jedna za svaki alat, na primjer

```
AI-assisted-by: GitHub Copilot CLI - generated the testbench loop over all input combinations; I wrote the checks and verified the results
```

Ako je asistent samo objašnjavao, a kod ste pisali sami, linija nije potrebna. Detalji: „Korišćenje AI alata“ u `docs/assignment-submission.md` repozitorijuma kursa. Vještina za komit dodatka `pds-git` pita za to i pomaže da napišete liniju.

## Šta je potrebno

| Šta | Potrebno za | Provjera |
| ------ | ------ | ------ |
| Podešavanje kursa iz `docs/getting-started.md` repozitorijuma kursa: *git*, *Python* 3.10 ili noviji, GHDL, alat za provjeru stila (`pip install -r requirements.txt`) | sve | `git --version`, `python --version`, `ghdl --version`, `vhdl-style --help` |
| Jedan AI alat: [Claude Code](https://code.claude.com/docs/en/quickstart), [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli) (besplatan za studente kroz [GitHub Education](https://education.github.com)) ili Antigravity CLI | asistent | `claude --version`, `copilot --version` ili `agy --version` |
| `pds-tools`, alati kursa koje dodaci koriste (korak 1) | alati dodataka | `pds-mcp --list` |
| Za `pds-quartus`: *Quartus Prime Lite* sa podrškom za *Cyclone V*, `quartus/bin64` na putanji (`docs/tools-setup.md`) | kreiranje projekata, prevođenje, tajming, programiranje | `quartus_sh --version` |
| Opciono: *GitHub CLI* `gh`, sa prijavom (`gh auth login`) | stanje *pull request*-a i evidencija vremena privatnih repozitorijuma; više zahtjeva prema *GitHub*-u na sat | `gh auth status` |

*Node.js* nije potreban.

## 1. Instalacija alata kursa

Instalirajte `pds-tools` u isti *Python* koji koristite za kurs (u kojem je instaliran `vhdl-style`):

```
python -m pip install "pds-tools @ git+https://github.com/etf-unibl/pds-marketplace@v0.2.9#subdirectory=tools/pds-tools"
```

Na *Linux* i *macOS* platformama umjesto `python` koristite `python3`. Provjerite da se komanda `pds-mcp` pronalazi:

```
pds-mcp --list
```

Ispis navodi skupove alata dodataka (`course`, `git`, `design`, `testing`, `learning`, `quartus`).

**Virtuelno okruženje:** ako ste alate kursa instalirali u virtuelno okruženje, aktivirajte ga **prije** pokretanja AI alata (`.venv\Scripts\Activate.ps1` na *Windows*-u, `source .venv/bin/activate` na *Linux*-u i *macOS*-u). AI alat pokreće `pds-mcp` sa putanje (`PATH`) terminala u kojem je pokrenut; bez okruženja alati dodataka nedostaju.

## 2. Dodavanje dodataka u AI alat

Svi PDS dodaci dolaze iz jednog *marketplace*-a, `pds-marketplace`. Instalirajte dodatke koji vam trebaju; dobar početak su `pds-course`, `pds-git` i `pds-learning`.

| Dodatak | Pomaže kod |
| ------ | ------ |
| `pds-course` | provjere podešavanja, razumijevanja zadatka, pripreme predaje, neuspješnih provjera *pull request*-a, evidencije vremena |
| `pds-git` | početka rada na zadatku, komita u formatu kursa, slanja i usklađivanja izmjena, ispravljanja grešaka u radu sa *git*-om |
| `pds-design` | rezultata provjere stila, upozorenja sinteze u *Quartus*-u, pinova ploče DE1-SoC |
| `pds-testing` | pisanja *testbench*-eva sa samoprovjerom i njihovog pokretanja kao u CI-ju |
| `pds-learning` | učenja uz predavanja (stranice tema, trenuci u videu, kod primjera), rječnika pojmova, kviza za provjeru znanja |
| `pds-quartus` | rada sa *Quartus*-om iz komandne linije: projekat za vaš dizajn (DE1-SoC, VHDL-2008, pinovi, takt) izvan repozitorijuma, sinteza i kompletno prevođenje, vremenska analiza i zatvaranje tajminga, *Tcl* skripte, programiranje ploče |
| `pds-datasheet` | čitanja tajminga iz *datasheet*-a komponente (PDF): gdje su tabele tajminga, šta znači svaki parametar, koje vrijednosti odgovaraju vašoj ploči; rezultat koristi `pds-quartus` za vremenska ograničenja |

### Claude Code

Pokrenite *Claude Code* u repozitorijumu kursa (`claude`) i izvršite:

```
/plugin marketplace add etf-unibl/pds-marketplace
/plugin install pds-course@pds-marketplace
/plugin install pds-git@pds-marketplace
/plugin install pds-learning@pds-marketplace
```

(`pds-design` i `pds-testing` na isti način.) Zatim izvršite `/reload-plugins` ili ponovo pokrenite *Claude Code*. Kada se alat dodatka prvi put pokrene, *Claude Code* traži dozvolu; alati samo čitaju, pa ih možete trajno dozvoliti za taj dodatak.

### GitHub Copilot CLI

U terminalu:

```
copilot plugin marketplace add etf-unibl/pds-marketplace
copilot plugin install pds-course@pds-marketplace
copilot plugin install pds-git@pds-marketplace
copilot plugin install pds-learning@pds-marketplace
```

Pokrenite *Copilot* u repozitorijumu kursa sa najjačim automatskim podešavanjem, `copilot --model auto --auto-tier intelligence`, i potvrdite povjerenje u folder kada to bude zatraženo. Da bi to bilo podrazumijevano, jednom pokrenite `/config model` i izaberite *Auto* sa profilom *intelligence*. Ako vaš plan dozvoljava izbor modela komandom `/model`, izaberite model *Claude Sonnet*, *Claude Opus* ili *GPT-5*, a ne model sa oznakom *mini*, *flash* ili *haiku*: manji modeli češće odgovaraju napamet, bez alata dodataka.

### Antigravity CLI

*Antigravity* instalira dodatke iz foldera. Jednom klonirajte *marketplace* i instalirajte dodatke iz njega:

```
git clone https://github.com/etf-unibl/pds-marketplace.git
agy plugin install pds-marketplace/plugins/pds-course
agy plugin install pds-marketplace/plugins/pds-git
agy plugin install pds-marketplace/plugins/pds-learning
```

Provjerite komandom `agy plugin list`. Za ažuriranje kasnije izvršite `git pull` u klonu i ponovo instalirajte dodatke.

## 3. Provjera da sve radi

U repozitorijumu kursa pokrenite AI alat i pitajte:

> Provjeri moje podešavanje za PDS kurs.

Asistent pokreće provjeru podešavanja dodatka `pds-course` (*git* identitet sa *GitHub* *noreply* adresom, *git hook*-ovi kursa, *Python* alati, GHDL, `gh`) i kaže šta treba ispraviti. Ako odgovori bez pokretanja alata, pogledajte [Rješavanje problema](#rješavanje-problema).

## 4. Korišćenje dodataka

Pitajte svojim riječima, na srpskom ili engleskom; asistent bira odgovarajuću vještinu (*skill*). U *Claude Code*-u vještinu možete pozvati i direktno, npr. `/pds-learning:tutor`.

| Želite da | Pitajte na primjer | Vještina |
| ------ | ------ | ------ |
| razumijete zadatak | „Dobio sam zadatak #12. Šta treba da uradim?“ | `pds-course:task` |
| počnete rad | „Kako da počnem rad na zadatku #12?“ | `pds-git:start` |
| napravite komit | „Pomozi mi da komitujem izmjene u formatu kursa.“ | `pds-git:commit` |
| ispravite grešku u *git*-u | „Komitovao sam na pogrešnu granu.“ | `pds-git:fix` |
| provjerite stil | „Da li će kod u assignments/12 proći provjeru stila?“ | `pds-design:style` |
| testirate | „Pokreni moje testbench-eve kao CI.“ / „Kako da napišem testbench sa samoprovjerom?“ | `pds-testing:run`, `pds-testing:testbench` |
| predate rješenje | „Da li sam spreman da otvorim pull request?“ | `pds-course:submit` |
| razumijete neuspješne provjere | „Moj pull request ima neuspješne provjere. Šta znače?“ | `pds-course:checks` |
| evidentirate vrijeme | „Provjeri moj /spent komentar: /spent 1h 30m“ | `pds-course:time` |
| učite | „Zašto Quartus ovdje pravi leč?“ / „Ispitaj me iz predavanja 10.“ | `pds-learning:tutor`, `pds-learning:quiz` |
| povežete dizajn sa pločom | „Koje pinove koristim za prekidače i sedmosegmentne displeje?“ | `pds-design:pins` |
| koristite *Quartus* | „Napravi Quartus projekat za zadatak 12 i sintetizuj ga.“ / „Prevedi ga i reci mi Fmax.“ / „Isprogramiraj ploču.“ / „Napiši Tcl skriptu koja dodjeljuje pinove.“ / „Koja vremenska ograničenja treba mom dizajnu i kako da izračunam kašnjenje ulaza?“ | `pds-quartus:project`, `compile`, `timing`, `constraints`, `program`, `tcl` |
| čitate *datasheet* | „Ovo je datasheet AD konvertora: datasheets/ltc2308.pdf. Gdje su vrijednosti tajminga i šta znače?“ | `pds-datasheet:datasheet` |

Šta asistent radi sam: čita fajlove, pokreće GHDL i provjeru stila (bez `--fix`), čita vaše zadatke i *pull request*-ove na *GitHub*-u i pretražuje stranice tema kursa. Šta ostavlja vama: svaku komandu koja nešto mijenja. Prikazuje komandu, objašnjava svaki njen dio, kaže šta treba da vidite i kako da poništite izmjenu, a nakon što je pokrenete, provjerava rezultat.

Ako asistent pokuša sam da pokrene takvu komandu, zaštita ga zaustavlja porukom „PDS plugin rule (teach, don't execute)“ i on vam umjesto toga prikazuje komandu. To je očekivano.

**Privatnost:** AI alat šalje ono što pročita (vaš kod, zadatke, poruke) svom provajderu. Ne lijepite lozinke ni tokene u razgovor.

## Ažuriranje

Kurs najavljuje nove verzije dodataka i alata `pds-tools` (dodaci pozivaju alate iz `pds-tools`, pa nova verzija dodataka može zahtijevati i novu verziju `pds-tools`). Ažurirajte oba dijela, ovim redom:

1. **Zatvorite AI alat** (svaku otvorenu sesiju). Na *Windows*-u se `pds-mcp` koji radi ne može zamijeniti.
2. **Ažurirajte `pds-tools`** u istom *Python*-u kao u koraku 1; ako koristite virtuelno okruženje, prvo ga aktivirajte. Koristite oznaku verzije koju kurs najavi:

   ```
   python -m pip install --upgrade "pds-tools @ git+https://github.com/etf-unibl/pds-marketplace@v0.2.9#subdirectory=tools/pds-tools"
   pds-mcp --version
   ```

   `pds-mcp --version` mora ispisati verziju iz oznake u komandi.
3. **Ažurirajte dodatke:**

   | Alat | Ažuriranje dodataka |
   | ------ | ------ |
   | Claude Code | pokrenite ga, zatim `/plugin marketplace update pds-marketplace` i `/reload-plugins` |
   | Copilot CLI | u terminalu: `copilot plugin marketplace update`, zatim `copilot plugin update` (svi instalirani dodaci) |
   | Antigravity CLI | `git pull` u klonu, zatim ponovo `agy plugin install` |

4. **Ponovo pokrenite AI alat** u repozitorijumu kursa, iz terminala u kojem je okruženje aktivno, i pitajte "Provjeri moje okruženje za kurs PDS." Odgovor navodi alate i njihove verzije, uključujući `pds-tools`.

## Rješavanje problema

| Problem | Uzrok i rješenje |
| ------ | ------ |
| Asistent odgovara bez pokretanja PDS alata; `/mcp` (*Claude Code*) ne prikazuje server `pds-…` ili prijavljuje grešku | komanda `pds-mcp` se ne pronalazi: instalirajte `pds-tools` (korak 1) i pokrenite AI alat iz terminala u kojem `pds-mcp --list` radi (prethodno aktivirajte virtuelno okruženje) |
| „PDS plugin rule (teach, don't execute)“ | očekivano: prikazanu komandu pokrenite sami |
| Dokumenti kursa ili stranice tema se ne pronalaze | pokrenite AI alat u repozitorijumu kursa; ako ste klonirali samo granu `assignments`, izvršite `git fetch origin main` |
| Greške *GitHub*-a kod stanja *pull request*-a ili evidencije vremena (403, ograničenje broja zahtjeva, 404 za privatni repozitorijum) | prijavite se komandom `gh auth login`; alati tada koriste vašu *GitHub* prijavu |
| *Copilot* odgovara napamet umjesto da koristi alate | ukucajte `/mcp`: serveri `pds-…` moraju biti navedeni i pokrenuti; ako nisu, *Copilot* ne nalazi `pds-mcp` (pokrenite ga iz terminala u kojem radi `pds-mcp --list`). Ako rade, pokrenite *Copilot* komandom `copilot --model auto --auto-tier intelligence` (odjeljak 2) i pitajte ponovo, navodeći dodatak, npr. „koristi pds-learning alate“ |
| *Antigravity*: dodatak ništa ne radi | izvršite `agy plugin list`; ponovo instalirajte iz klona; zaštita zahtijeva *Python* na putanji (`python --version`) |
| *Windows*: „Python was not found; run without arguments to install from the Microsoft Store“ | bezopasna poruka *Windows* prečice `python3`; zaštita tada koristi `python` ili `py` |
