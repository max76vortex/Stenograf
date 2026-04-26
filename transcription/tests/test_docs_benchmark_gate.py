from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPTION_DIR = REPO_ROOT / "transcription"


class DocumentationContractTests(unittest.TestCase):
    def test_readme_sets_local_default_and_marks_cloud_as_experimental(self) -> None:
        readme = (TRANSCRIPTION_DIR / "README.md").read_text(encoding="utf-8").lower()

        self.assertIn("production/default provider", readme)
        self.assertIn("faster-whisper-local", readme)
        self.assertIn("cloud/api движки", readme)
        self.assertIn("r&d/экспериментальные", readme)
        self.assertIn("yandex-speechkit", readme)
        self.assertIn("deepgram-nova-2", readme)
        self.assertIn("nexara", readme)

    def test_readme_documents_continue_on_error_and_exit_codes(self) -> None:
        readme = (TRANSCRIPTION_DIR / "README.md").read_text(encoding="utf-8").lower()

        self.assertIn("continue-on-error", readme)
        self.assertIn("коды возврата", readme)
        self.assertIn("`0`", readme)
        self.assertIn("`1`", readme)

    def test_setup_mentions_large_v3_first_run_download(self) -> None:
        setup = (TRANSCRIPTION_DIR / "SETUP.md").read_text(encoding="utf-8").lower()

        self.assertIn("faster-whisper-local", setup)
        self.assertIn("модель `large-v3`", setup)
        self.assertIn("при первом запуске", setup)

    def test_benchmark_readme_defines_gate_contract(self) -> None:
        benchmark_readme_path = TRANSCRIPTION_DIR / "asr-benchmark" / "README.md"
        self.assertTrue(benchmark_readme_path.exists())

        benchmark_readme = benchmark_readme_path.read_text(encoding="utf-8").lower()
        self.assertIn("worktree 2 (asr r&d)", benchmark_readme)
        self.assertIn("worktree 1 (core delivery)", benchmark_readme)
        self.assertIn("decision.md", benchmark_readme)
        self.assertIn("results.csv", benchmark_readme)
        for field in (
            "file_id",
            "duration_min",
            "noise",
            "engine",
            "a_loops",
            "a_empty",
            "a_coherence",
            "a_pass",
        ):
            self.assertIn(field, benchmark_readme)

    def test_core_gate_and_handoff_docs_define_delta04_contract(self) -> None:
        core_gate = (
            TRANSCRIPTION_DIR / "asr-benchmark" / "CORE_GATE.md"
        ).read_text(encoding="utf-8").lower()
        handoff = (
            REPO_ROOT / "multi-agent-system" / "current-run" / "worktree_handoff.md"
        ).read_text(encoding="utf-8").lower()
        readme = (TRANSCRIPTION_DIR / "README.md").read_text(encoding="utf-8").lower()

        self.assertIn("faster-whisper-local", core_gate)
        self.assertIn("decision.md", core_gate)
        self.assertIn("results.csv", core_gate)
        self.assertIn("exact provider/profile", core_gate)
        for state in (
            "missing",
            "stale",
            "simulated-only",
            "provisional",
            "validation in progress",
            "blocked",
            "rejected",
        ):
            self.assertIn(state, core_gate)

        self.assertIn("worktree 2", handoff)
        self.assertIn("worktree 1", handoff)
        self.assertIn("faster-whisper-local", handoff)
        self.assertIn("decision.md", handoff)
        self.assertIn("results.csv", handoff)
        self.assertIn("rollback/default", handoff)

        self.assertIn("transcription/asr-benchmark/core_gate.md", readme)
        self.assertIn("multi-agent-system/current-run/worktree_handoff.md", readme)


if __name__ == "__main__":
    unittest.main()
