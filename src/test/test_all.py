import src.veille_function as veille
from src.utils.access_grist_api import GristApi


def test_():
    return veille.extract_and_add_to_veille("export.json", target_table="Test")


def test_fetch():
    return GristApi().fetch_table_pl("Veille")


def test_add_records():
    data_list = [
        {
            "fields": {
                "Titre_article": "2 Les Rencontres du Numérique Ouvert le 13/11",
                "Lien_article": "https://docs.numerique.gouv.fr/dorerer/",
                "Qui_a_propose": "Coucou",
                "Quel_chanel": "https://tchap.gouv.fr/#/room/!DTuNyduZcTlsapzfyV:agent.finances.tchap.gouv.fr/$175974485023378hbhrc:agent.finances.tchap.gouv.fr",
                "Resume": "",
                "Date": "2025-10-06 12:00",
            },
        },
        {
            "fields": {
                "Titre_article": "vcvxcwcvwxxxw",
                "Lien_article": "https://www.linkedin.com/posts/",
                "Qui_a_propose": "rezrez",
                "Quel_chanel": "https://tchap.gouv.fr/#/room/!DTuNyduZcTlsapzfyV:agent.finances.tchap.gouv.fr/$175978782747889EWpei:agent.finances.tchap.gouv.fr",
                "Resume": "ht au cm d'e [qui a réussi](https://www.linkedin.com/) 🚀",
                "Date": "2025-10-06 23:57",
            },
        },
        {
            "fields": {
                "Titre_article": "Webinaire eurostat: utilisation de l'ia pour la stat publique",
                "Lien_article": "https://link.europa.eu",
                "Qui_a_propose": "vxcvxcv",
                "Quel_chanel": "https://tchap.gouv.fr/#/room/!DTuNyduZcTlsapzfyV:agent.finances.tchap.gouv.fr/$1759935114134590jLsxw:agent.finances.tchap.gouv.fr",
                "Resume": None,
                "Date": "2025-10-08 16:51",
            },
        },
    ]

    data_json = {"records": data_list}

    return GristApi().add_records("Test", json=data_json)
