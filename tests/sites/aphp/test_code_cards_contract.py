from pathlib import Path

from genpatientprofile.sites.aphp.code_cards import CodeCardsRegistry


def _write_card_library(
    root: Path,
    *,
    exact_header: str,
    exact_row: str,
    category_header: str,
    category_row: str,
) -> tuple[Path, Path]:
    exact_dir = root / "exact"
    category_dir = root / "categories"
    exact_dir.mkdir()
    category_dir.mkdir()

    (exact_dir / "index.csv").write_text(
        f"{exact_header}\n{exact_row}\n", encoding="utf-8"
    )
    (category_dir / "index.csv").write_text(
        f"{category_header}\n{category_row}\n", encoding="utf-8"
    )
    (exact_dir / "exact.md").write_text("FICHE EXACTE", encoding="utf-8")
    (category_dir / "category.md").write_text("FICHE CATÉGORIE", encoding="utf-8")
    return exact_dir, category_dir


def test_registry_reads_canonical_fichier_column(tmp_path):
    exact_dir, category_dir = _write_card_library(
        tmp_path,
        exact_header="code,fichier",
        exact_row="A014,exact.md",
        category_header="code,fichier",
        category_row="B20,category.md",
    )

    registry = CodeCardsRegistry.from_dirs(exact_dir, category_dir)

    assert registry.exact_index == {"A01.4": exact_dir / "exact.md"}
    assert registry.category_index == {"B20": category_dir / "category.md"}
    assert registry.find("A01.4").text == "FICHE EXACTE"
    assert registry.find("B20.1").text == "FICHE CATÉGORIE"


def test_registry_keeps_legacy_filepath_fallback(tmp_path):
    exact_dir, category_dir = _write_card_library(
        tmp_path,
        exact_header="code,filepath",
        exact_row="A014,exact.md",
        category_header="code,filepath",
        category_row="B20,category.md",
    )

    registry = CodeCardsRegistry.from_dirs(exact_dir, category_dir)

    assert registry.find("A014").path == exact_dir / "exact.md"
    assert registry.find("B209").path == category_dir / "category.md"


def test_canonical_fichier_takes_precedence_over_legacy_filepath(tmp_path):
    exact_dir, category_dir = _write_card_library(
        tmp_path,
        exact_header="code,fichier,filepath",
        exact_row="A014,exact.md,missing-exact.md",
        category_header="code,fichier,filepath",
        category_row="B20,category.md,missing-category.md",
    )

    registry = CodeCardsRegistry.from_dirs(exact_dir, category_dir)

    assert registry.exact_index["A01.4"] == exact_dir / "exact.md"
    assert registry.category_index["B20"] == category_dir / "category.md"
