"""
Unit tests for the LLM completion stage (`src/data/complete_veille.py`).

Self-contained: no network, no Grist/LLM credentials, no data file — the page
fetch and the LLM call are mocked. Run from the repository root:

    uv run pytest src/test/test_complete_veille.py
"""

import os
import sys

# Allow running this file directly (`uv run src/test/test_complete_veille.py`),
# not only via pytest: put the repo root on sys.path so `import src...` resolves.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import doctest
from unittest import mock

import pytest

import src.data.complete_veille as cv
import src.utils.llm_client as llm
import src.utils.config as config

FAKE_HTML = (
    "<html><head><title>Mon Titre</title></head>"
    "<body>Du contenu riche sur l'IA.</body></html>"
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def sample_rows():
    return [
        {"id": 1, config.COL_CATEGORY: ["L", "IA", "Stat publique"], config.COL_TITLE: "Article A"},
        {"id": 2, config.COL_CATEGORY: ["L", "IA"], config.COL_RESUME: "Resume B"},
        {"id": 3, config.COL_CATEGORY: None, config.COL_TITLE: "Pas de cat"},
        {"id": 4, config.COL_CATEGORY: "Cartographie", config.COL_TITLE: "Carte"},
    ]


@pytest.fixture
def vocab():
    # The closed category vocabulary (content is irrelevant to the mocked
    # process_row tests, which stub out the LLM).
    return ["IA", "Stat publique", "Cartographie", "fun"]


@pytest.fixture
def examples(sample_rows):
    return cv.build_category_examples(sample_rows, n=15)


# --------------------------------------------------------------------------- #
# Doctests on the pure helpers
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("module", [cv, llm], ids=["complete_veille", "llm_client"])
def test_doctests(module):
    result = doctest.testmod(module, verbose=False)
    assert result.failed == 0, f"{module.__name__} doctests failed: {result}"


# --------------------------------------------------------------------------- #
# llm_client.parse_json_answer
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "raw, expected",
    [
        ('```json\n{"a":1}\n```', {"a": 1}),       # fenced
        ('blah {"x": [1,2]} trailing', {"x": [1, 2]}),  # surrounded by prose
        ("not json at all", {}),                    # unrecoverable -> {}
    ],
)
def test_parse_json_answer(raw, expected):
    assert llm.parse_json_answer(raw) == expected


# --------------------------------------------------------------------------- #
# Categories as a Reference List into the Rubriques table
# --------------------------------------------------------------------------- #
def test_build_category_ref_maps_and_vocabulary():
    rubriques = [
        {"id": 1, "Category": "IA", "Rubrique": "Tech"},
        {"id": 2, "Category": "Stat publique", "Rubrique": "Metier"},
        {"id": 3, "Category": "fun", "Rubrique": "Divers"},
    ]
    id_to_name, name_to_id = cv.build_category_ref_maps(rubriques)
    assert id_to_name == {1: "IA", 2: "Stat publique", 3: "fun"}
    assert name_to_id == {"IA": 1, "Stat publique": 2, "fun": 3}
    assert cv.category_vocabulary(id_to_name) == ["IA", "Stat publique", "fun"]


def test_normalise_categories_translates_ref_ids():
    id_to_name = {1: "IA", 2: "fun"}
    # the API returns Rubriques row ids (the fetch often stringifies them)
    assert cv.normalise_categories(["L", "1", 2], id_to_name) == ["IA", "fun"]
    assert cv.normalise_categories(["L", 99], id_to_name) == []  # unknown id dropped
    # without a map, elements are treated as names (legacy / no Rubriques)
    assert cv.normalise_categories(["L", "IA"]) == ["IA"]


def test_to_grist_ref_list_maps_names_to_ids():
    name_to_id = {"IA": 1, "fun": 2}
    assert cv.to_grist_ref_list(["IA", "fun"], name_to_id) == ["L", 1, 2]
    assert cv.to_grist_ref_list(["inconnue"], name_to_id) is None  # unmapped -> None


def test_build_category_examples(examples):
    assert {"contenu": "Article A", "categorie": ["IA", "Stat publique"]} in examples
    assert len(examples) == 3  # rows 1, 2 and 4 have both a category and content


# --------------------------------------------------------------------------- #
# candidate_links
# --------------------------------------------------------------------------- #
def test_candidate_links_ordering():
    row = {
        config.COL_LINK: "https://primary.fr/article",
        config.COL_RESUME: "voir aussi https://backup1.fr et https://backup2.fr",
    }
    assert cv.candidate_links(row) == [
        "https://primary.fr/article",
        "https://backup1.fr",
        "https://backup2.fr",
    ]


def test_candidate_links_skips_internal_link():
    # An internal Tchap link in Lien_article is ignored; we fall back to Resume.
    row = {
        config.COL_LINK: config._INTERNAL_PREFIXES[0] + "#/room/abc",
        config.COL_RESUME: "le vrai lien https://real.fr",
    }
    assert cv.candidate_links(row) == ["https://real.fr"]


# --------------------------------------------------------------------------- #
# process_row branches
# --------------------------------------------------------------------------- #
def test_process_row_duplicate(vocab, examples):
    fields = cv.process_row(
        {"id": 9, config.COL_DUPLICATE: 2, config.COL_LINK: "https://x.fr"},
        vocab, examples, mock.Mock(),
    )
    assert "doublon" in fields["Traitement"].lower()
    assert set(fields) == {"Traitement"}  # nothing else touched


def test_process_row_no_working_link(vocab, examples):
    with mock.patch.object(cv, "fetch_if_working", return_value=None):
        fields = cv.process_row(
            {"id": 10, config.COL_DUPLICATE: 1, config.COL_LINK: "https://dead.fr", config.COL_RESUME: ""},
            vocab, examples, mock.Mock(),
        )
    assert fields["Traitement"].startswith("NO WORKING LINK FOUND")


def test_process_row_happy_path(vocab, examples):
    fake_llm = {
        "titre": "Un titre extrait",
        "resume": "Resume telegraphique. Deux phrases.",
        "categories": ["IA"],
    }
    with mock.patch.object(cv, "fetch_if_working", return_value=FAKE_HTML), \
         mock.patch.object(cv, "ask_json", return_value=fake_llm):
        fields = cv.process_row(
            {"id": 11, config.COL_DUPLICATE: 1, config.COL_LINK: "https://live.fr/a", config.COL_RESUME: "x"},
            vocab, examples, mock.Mock(),
        )
    assert fields[config.COL_TITLE] == "Un titre extrait"
    assert fields[config.COL_RESUME] == "Resume telegraphique. Deux phrases."
    assert fields[config.COL_CATEGORY] == ["L", "IA"]  # no ref map passed -> names kept
    assert fields[config.COL_PROCESS].startswith("Traite le")
    assert config.COL_LINK not in fields  # original link worked -> not rewritten


def test_process_row_writes_category_as_rubriques_refs(vocab, examples):
    # With a name->id map, the category is written as Rubriques row ids, not names.
    fake_llm = {"titre": "T", "resume": "R", "categories": ["IA", "fun"]}
    id_to_name = {1: "IA", 2: "fun"}
    name_to_id = {"IA": 1, "fun": 2}
    with mock.patch.object(cv, "fetch_if_working", return_value=FAKE_HTML), \
         mock.patch.object(cv, "ask_json", return_value=fake_llm):
        fields = cv.process_row(
            {"id": 31, config.COL_DUPLICATE: 1, config.COL_LINK: "https://live.fr", config.COL_RESUME: ""},
            vocab, examples, mock.Mock(), id_to_name=id_to_name, name_to_id=name_to_id,
        )
    assert fields[config.COL_CATEGORY] == ["L", 1, 2]  # Rubriques ids, not names


def test_process_row_drops_category_absent_from_rubriques(vocab, examples):
    # A category the LLM returns that isn't in Rubriques can't be referenced.
    fake_llm = {"titre": "T", "resume": "R", "categories": ["inconnue"]}
    with mock.patch.object(cv, "fetch_if_working", return_value=FAKE_HTML), \
         mock.patch.object(cv, "ask_json", return_value=fake_llm):
        fields = cv.process_row(
            {"id": 32, config.COL_DUPLICATE: 1, config.COL_LINK: "https://live.fr", config.COL_RESUME: ""},
            vocab, examples, mock.Mock(), id_to_name={1: "IA"}, name_to_id={"IA": 1},
        )
    assert config.COL_CATEGORY not in fields  # nothing writable -> column left untouched


def test_process_row_keeps_lien_article_when_original_works(vocab, examples):
    fake_llm = {"titre": "T", "resume": "R", "categories": ["IA"]}
    with mock.patch.object(cv, "fetch_if_working", return_value=FAKE_HTML), \
         mock.patch.object(cv, "ask_json", return_value=fake_llm):
        fields = cv.process_row(
            {"id": 20, config.COL_DUPLICATE: 1, config.COL_LINK: "https://live.fr", config.COL_RESUME: ""},
            vocab, examples, mock.Mock(),
        )
    assert config.COL_LINK not in fields  # no spurious rewrite


def test_process_row_writes_back_backup_link_from_resume(vocab, examples):
    fake_llm = {"titre": "T", "resume": "R", "categories": ["IA"]}

    def fake_fetch(url, logger):  # only the Resume backup responds
        return FAKE_HTML if url == "https://backup.fr" else None

    with mock.patch.object(cv, "fetch_if_working", side_effect=fake_fetch), \
         mock.patch.object(cv, "ask_json", return_value=fake_llm):
        fields = cv.process_row(
            {"id": 21, config.COL_DUPLICATE: 1, config.COL_LINK: "https://dead.fr",
             config.COL_RESUME: "essaie plutot https://backup.fr"},
            vocab, examples, mock.Mock(),
        )
    assert fields[config.COL_LINK] == "https://backup.fr"  # Lien_article updated


def test_process_row_writes_back_link_extracted_from_markdown(vocab, examples):
    fake_llm = {"titre": "T", "resume": "R", "categories": ["IA"]}
    with mock.patch.object(cv, "fetch_if_working", return_value=FAKE_HTML), \
         mock.patch.object(cv, "ask_json", return_value=fake_llm):
        fields = cv.process_row(
            {"id": 22, config.COL_DUPLICATE: 1,
             config.COL_LINK: "[ici](https://clean.fr/a) et [x](https://clean.fr/b)",
             config.COL_RESUME: ""},
            vocab, examples, mock.Mock(),
        )
    assert fields[config.COL_LINK] == "https://clean.fr/a"  # clean URL written back


# --------------------------------------------------------------------------- #
# select_rows
# --------------------------------------------------------------------------- #
def test_select_rows_keeps_empty_traitement_only():
    rows = [
        {"id": 1, "Traitement": ""},
        {"id": 2, "Traitement": "deja fait"},
        {"id": 3, "Traitement": None},
        {"id": 4, "Traitement": "None"},  # literal string "None" counts as empty
    ]
    assert [r["id"] for r in cv.select_rows(rows)] == [1, 3, 4]


# --------------------------------------------------------------------------- #
# Fallback: unreachable link -> categorise from existing text, no overwrite
# --------------------------------------------------------------------------- #
def test_process_row_fallback_categorises_without_overwriting(vocab, examples):
    fake_llm = {"titre": "", "resume": "", "categories": ["IA"]}
    with mock.patch.object(cv, "fetch_if_working", return_value=None), \
         mock.patch.object(cv, "ask_json", return_value=fake_llm) as ask:
        fields = cv.process_row(
            {
                "id": 12, config.COL_DUPLICATE: 1, config.COL_LINK: "https://dead.fr",
                config.COL_TITLE: "Un titre humain", config.COL_RESUME: "Un resume humain.",
                config.COL_CATEGORY: None,
            },
            vocab, examples, mock.Mock(),
        )
        ask.assert_called_once()  # the LLM was called via the fallback
    assert fields[config.COL_PROCESS].startswith("Traite via texte existant")
    assert fields[config.COL_CATEGORY] == ["L", "IA"]  # category filled from existing text
    assert config.COL_TITLE not in fields              # curated title NOT overwritten
    assert config.COL_RESUME not in fields             # curated resume NOT overwritten


def test_process_row_fallback_no_text(vocab, examples):
    with mock.patch.object(cv, "fetch_if_working", return_value=None), \
         mock.patch.object(cv, "ask_json") as ask:
        fields = cv.process_row(
            {
                "id": 13, config.COL_DUPLICATE: 1, config.COL_LINK: "https://dead.fr",
                config.COL_RESUME: "", config.COL_TITLE: "",
            },
            vocab, examples, mock.Mock(),
        )
        ask.assert_not_called()  # no text to work from -> no LLM call
    assert fields[config.COL_PROCESS].startswith("NO WORKING LINK FOUND")


# --------------------------------------------------------------------------- #
# Pre-flight: detect formula (non-writable) target columns
# --------------------------------------------------------------------------- #
def test_formula_target_columns_flags_formula_cols():
    api = mock.Mock()
    api.fetch_columns.return_value = mock.Mock(
        json=lambda: {
            "columns": [
                {"id": config.COL_TITLE, "fields": {"isFormula": False}},
                {"id": config.COL_RESUME, "fields": {"isFormula": False}},
                {"id": config.COL_CATEGORY, "fields": {"isFormula": False}},
                {"id": config.COL_PROCESS, "fields": {"isFormula": True}},
            ]
        }
    )
    blocked = cv.formula_target_columns(
        api, "Veille",
        [config.COL_PROCESS, config.COL_TITLE, config.COL_RESUME, config.COL_CATEGORY],
        mock.Mock(),
    )
    assert blocked == ["Traitement"]


def test_formula_target_columns_tolerates_fetch_error():
    api = mock.Mock()
    api.fetch_columns.side_effect = RuntimeError("network down")
    # On a metadata-fetch error it warns and returns [] (does not block the run).
    assert cv.formula_target_columns(api, "Veille", [config.COL_PROCESS], mock.Mock()) == []


if __name__ == "__main__":
    # `uv run src/test/test_complete_veille.py` -> run this file through pytest.
    raise SystemExit(pytest.main([__file__, "-v", "-rs"]))
