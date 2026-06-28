"""backup.py 的单元测试"""

import tempfile
import unittest
from pathlib import Path

# 把 backup.py 所在目录加入导入路径
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backup import backup_folder, _files_identical


class TestFilesIdentical(unittest.TestCase):
    """测试 _files_identical 辅助函数"""

    def test_same_content_returns_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.txt"
            b = Path(tmp) / "b.txt"
            a.write_text("hello world", encoding="utf-8")
            b.write_text("hello world", encoding="utf-8")
            self.assertTrue(_files_identical(a, b))

    def test_different_content_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.txt"
            b = Path(tmp) / "b.txt"
            a.write_text("hello world", encoding="utf-8")
            b.write_text("goodbye", encoding="utf-8")
            self.assertFalse(_files_identical(a, b))

    def test_different_size_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.txt"
            b = Path(tmp) / "b.txt"
            a.write_text("short", encoding="utf-8")
            b.write_text("much longer content here", encoding="utf-8")
            self.assertFalse(_files_identical(a, b))


class TestBackupFolder(unittest.TestCase):
    """测试 backup_folder 核心函数"""

    def test_copies_files_and_preserves_structure(self):
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dst_dir:
            src = Path(src_dir)
            dst = Path(dst_dir)

            # 构造测试目录结构
            (src / "sub").mkdir()
            (src / "a.txt").write_text("AAA", encoding="utf-8")
            (src / "sub" / "b.txt").write_text("BBB", encoding="utf-8")

            stats = backup_folder(src, dst)

            self.assertEqual(stats["total"], 2)
            self.assertEqual(stats["copied"], 2)
            self.assertEqual(stats["failed"], 0)

            # 验证目标文件存在且内容正确
            self.assertTrue((dst / "a.txt").exists())
            self.assertTrue((dst / "sub" / "b.txt").exists())
            self.assertEqual((dst / "a.txt").read_text(encoding="utf-8"), "AAA")
            self.assertEqual((dst / "sub" / "b.txt").read_text(encoding="utf-8"), "BBB")

    def test_skips_unchanged_files_on_second_run(self):
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dst_dir:
            src = Path(src_dir)
            dst = Path(dst_dir)

            (src / "file.txt").write_text("unchanged", encoding="utf-8")

            # 第一次备份
            stats1 = backup_folder(src, dst)
            self.assertEqual(stats1["copied"], 1)

            # 第二次备份（内容未变）
            stats2 = backup_folder(src, dst)
            self.assertEqual(stats2["total"], 1)
            self.assertEqual(stats2["skipped"], 1)
            self.assertEqual(stats2["copied"], 0)

    def test_raises_on_missing_source(self):
        with tempfile.TemporaryDirectory() as dst_dir:
            with self.assertRaises(FileNotFoundError):
                backup_folder(Path("/no/such/path"), Path(dst_dir))


if __name__ == "__main__":
    unittest.main(verbosity=2)
