# ssphub_veille

## Set up :

Initialize a vault file with following features :

- **GRIST_VEILLE_DOC_ID** : id of grist document _VEILLE_ → go to Grist, Veille tab, settings and API part
- **GRIST_API_KEY** : API key to access to Grist → go to Grist, Account settings, generate API key

## Instructions :

### Export Tchap conversation

- go to Tchap
- extract the discussion using the "Export conversation" button within the group, with the following options :
  - formater: _json_ file
  - messages :
    - specify a # of msg
    - 1000 enough (10000 messages is 3 years of chat and represents 3Mo)
  - max size : set to 3Mo
- upload it to _working directory_ as **ssphub_veille/export.json**
  run

### Update to Grist table

```{bash}
cd ssphub_veille
uv sync
source .venv/bin/activate
uv run script.py
```

- uv sync
- go to script, run main.py
- Grist table has been updated
