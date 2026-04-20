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

### Export Tchap conversation

- go to Tchap
- extract the discussion using :
  - click on the discussion name (top of the window)
  - on the right handside panel, go to "Export conversation" , with the following options :
    - format: _json_ file
    - messages :
      - specify a # of msg
      - 500 enough (10000 messages is 3 years of chat and represents 3Mo)
    - max size : set to 3Mo
- upload the file into **ssphub_veille directory** as **export.json**

### Update to Grist table

- Launch a VSCode-Pyhton service in Onyxia with your secret and clone the git repo.
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

  If the result of the command is :

  Test with allow_redirects=True
  <Response [200]>
  https://grist.numerique.gouv.fr/api/docs/qntJ8WFEMytztkVZCwyCSN/tables/Test/records
  GET
  Test with allow_redirects=False
  <Response [302]>
  https://grist.numerique.gouv.fr/api/docs/qntJ8WFEMytztkVZCwyCSN/tables/Test/records
  POST

  It means that there is a problem.

  If there is no problem, the result should be <Response [200]> and <Response [200]>.

# Documentation

![overview of the structure of the functions (except testing functions)](docs/call_graph_all_but_test.png)

The graph can be generated with `graphs.sh`
