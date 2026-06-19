# ssphub_veille

# What do I need to be able to use this repo ?

For convenience, the readme is done using Onyxia and [SSPCloud's data platform](https://datalab.sspcloud.fr/).

- You should therefore already have an account there.
- You should also have a Grist account on [https://grist.numerique.gouv.fr/](https://grist.numerique.gouv.fr/).
- You need to have edit rights on Grist's Veille document.

## Have access to Grist SSPHub

Ask an admin of the SSPHub organization in Grist to give you edit rights on the Veille document.
If you have the rights, you should have the following icon in Grist :

![Access to SSPHub's Grist ](grist_ssphub.png)

You need to store the id of the Veille document.
It's accessible through the url of the Veille document : https://grist.numerique.gouv.fr/o/ssphub/doc/ID_OF_THE_DOCUMENT_TO_NOTE

## Get Grist API key

In Grist, on the top right, go to account's settings.

![Access your Grist account's settings](grist_account.png)

You can then create and have access to your Grist API Key. Note it down for later.
![Here is your Grist API key](grist_api.png)

You can also use a service account on Grist that gives you access to an API key.
Service account are linked to a single document and reduce the risk ok leaking the key.
Indeed, your personnal key gives access to all of your Grist files when a service account key
has access only to the documents you granted it access to.

## Set up :

Initialize a vault file with following features :

- **GRIST_VEILLE_DOC_ID** : id of Grist SSPHub's _VEILLE_ document (cf. steps above)
- **GRIST_SERVICE_ACCOUNT_VEILLE_KEY** : key of the service account linked to the document
- **GRIST_API_KEY** : API key to access Grist (cf. steps above)

By default, it searches for a service account key stored in an environment variable called
"GRIST_SERVICE_ACCOUNT_VEILLE_KEY".
If not present, it seaches for the environment variable called "GRIST_API_KEY".

### Add a secret in Onyxia

Using Onyxia, you can add a secret by going to "Mes secrets/Nouveau secret/".
![Select my secrets](onyxia_secrets.png)

![Then "new secret"](onyxia_newsecret.png)

Name it SSPHub for example.
Then, you click on "add a new variable", enter the secret's name and its value.
The final result should be something like :
![Final result with the two environment variables](onyxia_addvar.png)

## Instructions :

- Launch a VSCode-Pyhton service in Onyxia with above secrets and clone this git repo.

### Export Tchap conversation

- go to Tchap;
- extract the discussion using:
  - click on the discussion name (top of the window)
  - on the right handside panel, go to "Export conversation" , with the following options :
    - format: _json_ file
    - messages :
      - specify a # of msg
      - 500 enough (10000 messages is 3 years of chat and represents 3Mo)
    - max size : set to 3Mo
- upload the file into **ssphub_veille directory** as **export.json**

### Update to Grist table

- run the `main.py` script with `uv` on Terminal. `main.py` will accept two arguments from the CLI:
  - a path to the json file to clean and import to Grist.
    The argument is named `-f` or `--file` and by default is "export.json".
  - the name of the target Grist table to import the data to.
    It can be either "Test" or "Veille". The argument is named `-t` or `--table`.
    By default, it is the "Test" table
  - by default, the main script will run using a file named "export.json" in the
    ssphub_veille directory and import it into the table named "Test".

```{bash}
cd ssphub_veille
# uv run main.py # default file is export.json and target table is Test
uv run main.py -t "Veille"
# uv run main.py -f "export.json" -t "Veille"
```

- You should see logs of the script with the following steps:
  - Extraction from the Tchap conversation and number of links extracted,
  - Grist target table downloaded and number of rows before update,
  - Filtering duplicate links and number of final links to be added,
  - Export to the target table and ids of the appended rows

# Completing the Veille table with an LLM

This is the second stage of the pipeline. Once links have been extracted from
Tchap and added to the Grist table (see *Update to Grist table* above), this
step goes over the rows **whose `Traitement` column is empty** and fills in, for
each one, the **title**, a short **summary** and one or more **categories**,
using the SSP Cloud LLM lab. It then stamps the `Traitement` column, so a row is
processed once and skipped on the next run.

## What it does, row by row

1. **Duplicates** (`Doublon_lien > 1`) are skipped and recorded in `Traitement`.
2. It looks for a **working link**: it tries `Lien_article` first, then any link
   found in `Resume`.
   - If a link responds, the page is fetched and analysed.
   - If no link responds **but** the row already has a title/summary, it falls
     back to that existing text so a category can still be assigned. In this
     fallback it only fills empty cells (it never overwrites your curated
     title/summary, since there is no new information — just a re-reading).
   - If there is neither a working link nor any text, the row is left with
     `NO WORKING LINK FOUND`.
3. The LLM is asked, in a single call, to return JSON with:
   - `titre` — the article/blog/paper title (or a short invented one, ≤10 words);
   - `resume` — a concise, telegraphic summary in French (2–3 sentences max);
   - `categories` — chosen **from the existing categories**, guided by example
     assignments taken from already-categorised rows. It must not duplicate a
     similar existing category, and replies `["??"]` when it is unsure rather
     than guessing.
4. The results are written back to `Titre_article`, `Resume`, `Categorie`
   (encoded as Grist's `["L", …]` choice list), and `Traitement` is timestamped.

## Prerequisites

In addition to the Grist setup documented above, you need an LLM lab key.

Secrets (Onyxia → *Mes secrets*, same as for Grist):

- `GRIST_VEILLE_DOC_ID`, `GRIST_SERVICE_ACCOUNT_VEILLE_KEY` (or `GRIST_API_KEY`) —
  the Grist access already used by the extraction step.
- `LLM_LAB_API_KEY` — your key for <https://llm.lab.sspcloud.fr/api>.

Optional overrides: `LLM_LAB_ENDPOINT` (default `https://llm.lab.sspcloud.fr/api`)
and `LLM_MODEL_NAME` (default `gemma4-26b-moe`).

> **One-time Grist check:** the `Traitement` column must be a **data** column
> (type Text), not a formula column. If it is a formula column, the API cannot
> write to it; the script detects this and stops with a clear message before
> spending any LLM calls. `Doublon_lien` is expected to stay a formula column —
> it is only read.

## Usage

Everything is exposed through a single command, `veille.py`, with two
subcommands (the original `main.py` still works for extraction too):

```bash
# 1) extraction (unchanged): Tchap export -> new Grist rows
uv run veille.py extract -f export.json -t Veille

# 2) completion: process the rows whose Traitement is empty
#    Always dry-run first — it prints the exact update for each row, writes nothing.
uv run veille.py complete -t Veille --limit 5 --dry-run

# write the first 5 for real, then the rest
uv run veille.py complete -t Veille --limit 5
uv run veille.py complete -t Veille
```

Rows are selected solely on `Traitement` being empty. A successful run stamps
`Traitement`, so the same row is not processed twice; to redo a row, clear its
`Traitement` cell in Grist.

### `complete` options

| Option | Effect |
| --- | --- |
| `-t, --table` | Grist table id (e.g. `Veille`). |
| `--limit N` | Process at most N rows (useful for a first run / testing). |
| `--dry-run` | Compute updates and log them, but do not write to Grist. |
| `--n-examples N` | Number of example category assignments sent to the LLM (default 15). |

When a page is fetched successfully, the LLM results **overwrite**
`Titre_article`, `Resume` and `Categorie`. When the page can't be fetched, the
fallback only *fills* empty cells from the existing text (it never overwrites a
hand-written title/summary). Column names (`Lien_article`, `Resume`,
`Titre_article`, `Categorie`, `Doublon_lien`, `Traitement`) are defined as
constants at the top of `src/data/complete_veille.py`.

## Notes & limitations

- Links on sites that block scrapers or serve JavaScript-only pages (x.com,
  reddit, LinkedIn, youtube, some news sites) will fail the link check; those
  rows fall back to their existing text (for categorisation) or end up as
  `NO WORKING LINK FOUND` if they have no text.
- The category vocabulary is read from the table itself, so it grows/cleans up
  as you curate the table. `??` is the designated "unknown / unsure" category.

## Tests

`test_complete_veille.py` covers the pure logic (duplicate detection, link
resolution, category encoding, JSON parsing, gap-filling and the fallback path)
with the network and LLM mocked. `test_realdata.py` runs the same logic over a
real Grist snapshot. Run them with:

```bash
uv run python test_complete_veille.py
uv run python test_realdata.py   # expects a Veille_-_test.grist file alongside
```

# Bugs

- If everything works correctly but no update, the Grist API may not work and redirect to GET request.
  Run `uv run test.py` to test that one.
  You can also run it directly with `bash src/test/test_grist.sh`

  If the result of the command is :

  ```bash
  Test with allow_redirects=True
  <Response [200]>
  https://grist.numerique.gouv.fr/api/docs/qntJ8WFEMytztkVZCwyCSN/tables/Test/records
  GET
  Test with allow_redirects=False
  <Response [302]>
  https://grist.numerique.gouv.fr/api/docs/qntJ8WFEMytztkVZCwyCSN/tables/Test/records
  POST
  ```

  It means that there is a problem.

  If there is no problem, the result should be <Response [200]> and <Response [200]>.

# Documentation

![overview of the structure of the functions (except testing functions)](docs/call_graph_all_but_test.png)

The graph can be generated by running the `docs/graphs.sh` with bash.
