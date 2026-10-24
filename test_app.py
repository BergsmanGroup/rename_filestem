import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app import matching_files, planned_renames


class RenameFilestemTests(unittest.TestCase):
    def test_matching_is_literal_and_searches_only_stems(self):
        paths = [
            Path("sample_one.dat"),
            Path("sample+two.txt"),
            Path("sample_one.se"),
        ]

        self.assertEqual(
            matching_files(paths, "sample_"),
            [Path("sample_one.dat"), Path("sample_one.se")],
        )
        self.assertEqual(matching_files(paths, "sample."), [])

    def test_plan_replaces_all_stem_occurrences_and_preserves_extension(self):
        source = Path("data-run-run.dat")

        self.assertEqual(
            planned_renames([source], "run", "set"),
            [(source, Path("data-set-set.dat"))],
        )

    def test_directory_filter_is_based_on_match_paths(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            direct = root / "item.dat"
            nested = root / "nested" / "item.txt"
            other = root / "nested" / "unrelated.txt"
            for path in (direct, nested, other):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()

            matches = matching_files([direct, nested, other], "item")

            self.assertEqual(matches, [direct, nested])
            self.assertEqual(
                {path.parent.relative_to(root) for path in matches},
                {Path("."), Path("nested")},
            )


if __name__ == "__main__":
    unittest.main()
