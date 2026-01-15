# ssphub_veille

Directory to 

Instructions : 
- go to Tchap
- Extract discussion as json file, specify a # of msg (1000 enough : 10000 messages is 3 years of chat and represents 3Mo), set max size to 3Mo
- upload it to wd as ssphub_veille/export.json
run 
```{bash}
cd ssphub_veille
uv sync
source .venv/bin/activate
uv run script.py
```
- uv sync
- go to script, run function with adequate input and min date to upload to Grist table. 
- Grist table has been updated 

