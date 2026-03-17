# ssphub_veille

## Set up :

Initialize a vault file with following features :

- **GRIST_VEILLE_DOC_ID** : id of grist document _VEILLE_ → go to Grist, Veille tab, settings and API part
- **GRIST_API_KEY** : API key to access to Grist → go to Grist, Account settings, generate API key

### Add a secret in Onyxia

Using Onyxia, you can add a secret by going to "Mes secrets/Nouveau secret/".
![](onyxia_secrets.png)

![](onyxia_newsecret.png)

Name it SSPHub for example.
Then, you click on "add a new variable", enter the secret's name and its value.
The final result should be something like :
![](onyxia_addvar.png)

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

- run the following commands on Terminal. `main.py` will accept two arguments :
  - a path to the json file to clean and import to Grist. The argument is named `-f` or `--file`
  - the name of the target Grist table to import the data to. It can be either "Test" or "Veille". The argument is named `-t` or `--table`
  - by default, the main script will run using a file named "export.json" in the ssphub_veille directory and import it into the table named "Test".

```{bash}
cd ssphub_veille
# uv run main.py # default file is export.json and target table is Test
uv run main.py -t "Veille"
# uv run main.py -f "export.json" -t "Veille"
```

- Grist table has been updated

# Bugs

- If everything works correctly but no update, the Grist API may not work and redirect to GET request.
  Run `uv run test.py` to test that one.
  You can also run it directly with `bash src/test/test_grist.sh`

# Documentation

![overview of the structure of the functions (except testing functions)](docs/call_graph_all_but_test.png)

The graph can be generated with `graphs.sh`
