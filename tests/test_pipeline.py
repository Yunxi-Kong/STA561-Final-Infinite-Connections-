from __future__ import annotations

import unittest
import shutil
from pathlib import Path

from infinite_connections.batch import run_batch, write_batch_outputs
from infinite_connections.generator import LocalTemplateGenerator
from infinite_connections.seed_bank import CATEGORY_BANK
from infinite_connections.solver import solve_puzzle
from infinite_connections.validator import score_puzzle, validate_puzzle


class PipelineTests(unittest.TestCase):
    def test_local_generator_produces_valid_shape(self) -> None:
        puzzles = LocalTemplateGenerator().generate(count=5, seed=561)
        self.assertEqual(len(puzzles), 5)
        self.assertEqual([puzzle.title for puzzle in puzzles], [f"Puzzle {index:03d}" for index in range(1, 6)])
        for puzzle in puzzles:
            self.assertEqual(len(puzzle.words), 16)
            self.assertEqual(len(set(puzzle.normalized_words())), 16)
            self.assertEqual(len(puzzle.groups), 4)
            self.assertEqual(sum(len(group.words) for group in puzzle.groups), 16)

    def test_offline_seed_bank_is_large_enough_for_curated_diversity(self) -> None:
        exact_groups = {tuple(sorted(template.words)) for template in CATEGORY_BANK}
        unique_words = {word for template in CATEGORY_BANK for word in template.words}
        self.assertGreaterEqual(len(exact_groups), 12000)
        self.assertGreaterEqual(len(unique_words), 1200)

    def test_validator_accepts_generated_puzzle_shape(self) -> None:
        puzzle = LocalTemplateGenerator().generate(count=1, seed=1)[0]
        issues = validate_puzzle(puzzle)
        self.assertFalse([issue for issue in issues if issue.severity == "error"])
        report = score_puzzle(puzzle)
        self.assertGreaterEqual(report.quality_score, 60)

    def test_blind_solver_finds_generated_answer_key(self) -> None:
        puzzle = LocalTemplateGenerator().generate(count=1, seed=561)[0]
        result = solve_puzzle(puzzle)
        self.assertTrue(result.intended_solution_found)
        self.assertGreaterEqual(result.solution_count, 1)

    def test_batch_writes_cache_files(self) -> None:
        root = Path.cwd() / "tmp_test_outputs" / "unit"
        root.mkdir(parents=True, exist_ok=True)
        reference = root / "missing_reference.json"
        result = run_batch(count=8, seed=561, provider="local", reference_path=reference)
        paths = write_batch_outputs(result, root / "data")
        for path in paths.values():
            self.assertTrue(path.exists())
        self.assertEqual(len(result.candidates), 8)
        shutil.rmtree(root.parent, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
