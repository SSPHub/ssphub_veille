curl -X 'POST' \
  --max-redirs 0 \
  "https://grist.numerique.gouv.fr/api/docs/${GRIST_VEILLE_DOC_ID}/tables/Test/records" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer ${GRIST_SERVICE_ACCOUNT_VEILLE_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{
    "records": [
        {
            "fields": {
                "Titre_article": "SHELL - 2 Les Rencontres du Numérique Ouvert le 13/11",
                "Lien_article": "https://docs.numerique.gouv.fr/dorerer/",
                "Quel_chanel": "https://tchap.gouv.fr/#/room/!DTuNyduZcTlsapzfyV:agent.finances.tchap.gouv.fr/$175974485023378hbhrc:agent.finances.tchap.gouv.fr",
                "Resume": " ",
                "Date": "2025-10-06 12:00"
            }
        },
        {
            "fields": {
                "Titre_article": "SHELL - vcvxcwcvwxxxw",
                "Lien_article": "https://www.linkedin.com/posts/",
                "Quel_chanel": "https://tchap.gouv.fr/#/room/!DTuNyduZcTlsapzfyV:agent.finances.tchap.gouv.fr/$175978782747889EWpei:agent.finances.tchap.gouv.fr",
                "Resume": "ht au cm d [qui a fdsfsfsdf](https://www.linkedin.com/posts/) 🚀",
                "Date": "2025-10-06 23:57"
            }
        },
        {
            "fields": {
                "Titre_article": "SHELL - Webinaire eurostat: utilisation de l ia pour la stat publique",
                "Lien_article": "https://link.europa.eu/BXDdKD",
                "Quel_chanel": "https://tchap.gouv.fr/#/room/!DTuNyduZcTlsapzfyV:agent.finances.tchap.gouv.fr/$1759935114134590jLsxw:agent.finances.tchap.gouv.fr",
                "Resume": " ",
                "Date": "2025-10-08 16:51"
            }
        }
    ]
}' | tee response.json
