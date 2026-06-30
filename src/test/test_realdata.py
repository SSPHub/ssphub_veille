"""
Run the completion logic over the REAL rows of the Grist `Test` table.

Integration test against the live `Test` table of the Veille document. Most
tests are read-only and run the completion logic with the page fetch and the LLM
call mocked, so they are deterministic and spend no LLM credits. One test
(`test_update_records_roundtrip`) exercises the real write path: it PATCHes a
sentinel into a single row's `Traitement`, checks it landed, then restores the
original value — so the table is left exactly as it was found.

It needs Grist credentials (`GRIST_VEILLE_DOC_ID` plus
`GRIST_SERVICE_ACCOUNT_VEILLE_KEY` or `GRIST_API_KEY`) and network access. When
those are absent — e.g. in CI without secrets — the whole module is SKIPPED, so
it is safe to keep in the suite.

    uv run pytest src/test/test_realdata.py
    VEILLE_TEST_TABLE="Test" uv run pytest src/test/test_realdata.py  # override table

Read-only assertions check invariants (rows load, every result is a valid PATCH
payload, the fallback categorises un-scrapeable rows without overwriting titles),
not specific ids or counts, so they keep passing as the table evolves.
"""

import os
import sys

# Allow running this file directly (`uv run src/test/test_realdata.py`), not
# only via pytest: put the repo root on sys.path so `import src...` resolves.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest import mock

import pytest

import src.data.complete_veille as cv
import src.utils.config as config

TEST_TABLE = os.environ.get("VEILLE_TEST_TABLE", "Test")

_HAS_GRIST_CREDS = "GRIST_VEILLE_DOC_ID" in os.environ and (
    "GRIST_SERVICE_ACCOUNT_VEILLE_KEY" in os.environ or "GRIST_API_KEY" in os.environ
)

pytestmark = pytest.mark.skipif(
    not _HAS_GRIST_CREDS,
    reason="Grist credentials not set (GRIST_VEILLE_DOC_ID + a key); "
    "live Test-table test skipped.",
)


@pytest.fixture(scope="module")
def rows():
    """Fetch the live `Test` table; skip the module if it can't be reached."""
    try:
        df = cv.GristApi().fetch_table_pl(TEST_TABLE)
    except Exception as exc:  # network/auth issue -> skip rather than fail
        pytest.skip(f"could not fetch the '{TEST_TABLE}' table from Grist: {exc}")
    return df.to_dicts()


@pytest.fixture(scope="module")
def ref_maps():
    """Fetch the Rubriques table and build the id<->name category lookups."""
    try:
        rubriques = cv.GristApi().fetch_table_pl(config.TABLE_RUBRIQUES).to_dicts()
    except Exception as exc:
        pytest.skip(f"could not fetch the '{config.TABLE_RUBRIQUES}' table from Grist: {exc}")
    return cv.build_category_ref_maps(rubriques)  # (id_to_name, name_to_id)


@pytest.fixture(scope="module")
def vocab(ref_maps):
    id_to_name, _ = ref_maps
    return cv.category_vocabulary(id_to_name)


@pytest.fixture(scope="module")
def examples(rows, ref_maps):
    id_to_name, _ = ref_maps
    return cv.build_category_examples(rows, id_to_name, n=15)


def test_rows_have_ids(rows):
    assert all("id" in r for r in rows)


def test_vocabulary_and_examples(vocab, examples):
    assert isinstance(vocab, list)
    assert len(examples) <= 15
    assert all("contenu" in e and "categorie" in e for e in examples)


def test_process_all_rows_without_crashing(rows, ref_maps, vocab, examples):
    """Every real row yields a valid PATCH payload and nothing raises."""
    id_to_name, name_to_id = ref_maps
    fake_llm = {"titre": "T", "resume": "R", "categories": [vocab[0]] if vocab else []}
    with mock.patch.object(cv, "fetch_if_working", return_value="<title>T</title><body>x</body>"), \
         mock.patch.object(cv, "ask_json", return_value=fake_llm):
        for r in rows:
            fields = cv.process_row(r, vocab, examples, mock.Mock(), id_to_name, name_to_id)
            assert cv.COL_PROCESS in fields
            assert "id" not in fields  # the row id is carried separately, not in fields


def test_fallback_categorises_unscrapeable_rows(rows, ref_maps, vocab, examples):
    """Rows on bot-blocking hosts that lack a category but carry text should be
    categorised via the fallback (as Rubriques ids), without overwriting titles."""
    id_to_name, name_to_id = ref_maps
    if not vocab:
        pytest.skip("the Rubriques table is empty")
    a_category = vocab[0]
    expected_ref = ["L", name_to_id[a_category]]

    blocked_hosts = ("x.com", "twitter", "reddit", "linkedin", "youtu", "youtube")

    def is_blocked(url):
        return any(h in (url or "") for h in blocked_hosts)

    targets = [
        r for r in rows
        if is_blocked(r.get(config.COL_LINK))
        and not cv.normalise_categories(r.get("Categorie"), id_to_name)
        and cv.fallback_text(r)
    ]
    if not targets:
        pytest.skip("no un-scrapeable + uncategorised + has-text rows in the Test table")

    def fake_fetch(url, logger):
        return None if is_blocked(url) else "<title>T</title><body>x</body>"

    with mock.patch.object(cv, "fetch_if_working", side_effect=fake_fetch), \
         mock.patch.object(cv, "ask_json",
                           return_value={"titre": "", "resume": "", "categories": [a_category]}):
        for r in targets:
            fields = cv.process_row(r, vocab, examples, mock.Mock(), id_to_name, name_to_id)
            assert "NO WORKING LINK" not in fields[cv.COL_PROCESS]
            assert fields[cv.COL_CATEGORY] == expected_ref  # written as Rubriques ids
            if cv.clean_text(r.get("Titre_article")):
                assert cv.COL_TITLE not in fields  # existing title preserved


def test_update_records_roundtrip(rows):
    """Real write path against Grist: PATCH a sentinel into one row's
    `Traitement`, confirm it landed, then restore the original value."""
    if not rows:
        pytest.skip("the Test table is empty")

    target = rows[0]
    row_id = target["id"]
    original = target.get(cv.COL_PROCESS)
    sentinel = f"__pytest_roundtrip__ {os.getpid()}"
    api = cv.GristApi()

    try:
        resp = api.update_records(
            TEST_TABLE, json={"records": [{"id": row_id, "fields": {cv.COL_PROCESS: sentinel}}]}
        )
        assert resp.status_code == 200, (resp.status_code, resp.text[:200])

        after = {r["id"]: r for r in api.fetch_table_pl(TEST_TABLE).to_dicts()}
        assert after[row_id][cv.COL_PROCESS] == sentinel
    finally:
        # Always restore the original value (empty string clears the cell).
        api.update_records(
            TEST_TABLE,
            json={"records": [{"id": row_id, "fields": {cv.COL_PROCESS: original or ""}}]},
        )


if __name__ == "__main__":
    # `uv run src/test/test_realdata.py` -> run this file through pytest.
    raise SystemExit(pytest.main([__file__, "-v", "-rs"]))