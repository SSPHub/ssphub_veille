# ssphub_veille


## Set up :

Initialize a vault file with following features :

- **GRIST_VEILLE_DOC_ID** : id of grist document *VEILLE* → go to Grist, Veille tab, settings and API part
- **GRIST_API_KEY** : API key to access to Grist → go to Grist, Account settings, generate API key


## Instructions : 

### Export Tchap conversation

- go to Tchap
- extract the discussion using the "Export conversation" button within the group, with the following options :
    - formater: *json* file 
    - messages : 
        - specify a # of msg 
        - 1000 enough (10000 messages is 3 years of chat and represents 3Mo)
    - max size : set to 3Mo
- upload it to *working directory* as **ssphub_veille/export.json**
run 

### Update to Grist table

```{bash}
cd ssphub_veille
uv sync
source .venv/bin/activate
uv run script.py
```
- uv sync
- go to script, run function with adequate input and min date to upload to Grist table. 
- Grist table has been updated 

