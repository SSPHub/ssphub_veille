from src.utils.access_grist_api import GristApi
from src.extract import extract_and_add_to_veille
from src.utils.config import _INTERNAL_PREFIXES, COL_LINK, COL_TITLE, COL_RESUME

def test_():
    return extract_and_add_to_veille("export.json", target_table="Test")


def test_fetch():
    return GristApi().fetch_table_pl("Veille")


def test_add_records(**kwargs):
    data_list = [
        {
            "fields": {
                COL_TITLE: "TEST FROM ONYXIA - 2 Les Rencontres du Numérique Ouvert le 13/11",
                COL_LINK: "https://docs.numerique.gouv.fr/dorerer/",
                "Quel_chanel": _INTERNAL_PREFIXES[0] + "#/room/!DTuNyduZcTlsapzfyV:agent.finances.tchap.gouv.fr/$175974485023378hbhrc:agent.finances.tchap.gouv.fr",
                COL_RESUME: "",
                "Date": "2025-10-06 12:00",
            },
        },
        {
            "fields": {
                COL_TITLE: "TEST FROM ONYXIA - vcvxcwcvwxxxw",
                COL_LINK: "https://www.linkedin.com/posts/",
                "Quel_chanel": _INTERNAL_PREFIXES[0] + "#/room/!DTuNyduZcTlsapzfyV:agent.finances.tchap.gouv.fr/$175978782747889EWpei:agent.finances.tchap.gouv.fr",
                COL_RESUME: "ht au cm d'e [qui a réussi](https://www.linkedin.com/) 🚀",
                "Date": "2025-10-06 23:57",
            },
        },
        {
            "fields": {
                COL_TITLE: "TEST FROM ONYXIA - Webinaire eurostat: utilisation de l'ia pour la stat publique",
                COL_LINK: "https://link.europa.eu",
                "Quel_chanel": _INTERNAL_PREFIXES[0] + "#/room/!DTuNyduZcTlsapzfyV:agent.finances.tchap.gouv.fr/$1759935114134590jLsxw:agent.finances.tchap.gouv.fr",
                COL_RESUME: None,
                "Date": "2025-10-08 16:51",
            },
        },
    ]

    data_json = {"records": data_list}

    return GristApi().add_records("Test", json=data_json, **kwargs)


def test_redirect_post():
    r = test_add_records(allow_redirects=True)
    print("Test with allow_redirects=True")
    print(r)
    print(r.url)
    print(r.request.method)
    r = test_add_records(allow_redirects=False)
    print("Test with allow_redirects=False")
    print(r)
    print(r.url)
    print(r.request.method)
