# ssphub_veille

## Set up :

Initialize a vault file with following features :

- **GRIST_VEILLE_DOC_ID** : id of grist document _VEILLE_ → go to Grist, Veille tab, settings and API part
- **GRIST_API_KEY** : API key to access to Grist → go to Grist, Account settings, generate API key

## Instructions :

### Export Tchap conversation

- go to Tchap
- extract the discussion using the "Export conversation" button within the group, with the following options :
  - format: _json_ file
  - messages :
    - specify a # of msg
    - 1000 enough (10000 messages is 3 years of chat and represents 3Mo)
  - max size : set to 3Mo
- upload it to _working directory_ as **ssphub_veille/export.json**

### Update to Grist table

- run the following commands on Terminal :

```{bash}
cd ssphub_veille
uv sync
# uv run main.py # default file is export.json and target table is Test
uv run main.py -t "Veille"
# uv run main.py -f "export.json" -t "Veille"
```

- Grist table has been updated

# Bugs

- If everything works correctly but no update, the Grist API may not work and redirect to GET request.
  See test_redirect_post() in test_all.py to check for that.

# Documentation

![overview of the structure of the functions (except testing functions)](docs/call_graph_all_but_test.png)

The graph can be generated with `graphs.sh`
