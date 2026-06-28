#!/usr/bin/env python3
"""
backup.py — 文件夹备份工具

把源文件夹的所有文件复制到目标文件夹（保持目录结构），并在 backup.log 中记录操作详情。

用法:
    python backup.py <源文件夹> <目标文件夹>

示例:
    python backup.py C:/Users/JiuLi/Documents D:/Backup/Documents
"""

import argparse
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
LOG_FILE = Path(__file__).resolve().parent / "backup.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

log = logging.getLogger("backup")


# ---------------------------------------------------------------------------
# 核心逻辑
# ---------------------------------------------------------------------------
def backup_folder(src: Path, dst: Path) -> dict:
    """
    将 src 下的所有文件递归复制到 dst，保持目录结构。

    返回:
        {"total": int, "copied": int, "failed": int, "skipped": int}
    """
    if not src.exists():
        raise FileNotFoundError(f"源文件夹不存在: {src}")
    if not src.is_dir():
        raise NotADirectoryError(f"源路径不是文件夹: {src}")

    stats = {"total": 0, "copied": 0, "failed": 0, "skipped": 0}

    log.info("=" * 60)
    log.info("开始备份")
    log.info("  源:      %s", src)
    log.info("  目标:    %s", dst)
    log.info("  日志文件: %s", LOG_FILE)
    log.info("=" * 60)

    for item in src.rglob("*"):
        if not item.is_file():
            continue

        stats["total"] += 1
        relative = item.relative_to(src)
        target = dst / relative

        try:
            # 确保目标父目录存在
            target.parent.mkdir(parents=True, exist_ok=True)

            # 如果目标文件已存在且内容相同则跳过
            if target.exists() and _files_identical(item, target):
                log.info("跳过 (未变化): %s", relative)
                stats["skipped"] += 1
                continue

            shutil.copy2(item, target)
            log.info("已复制: %s", relative)
            stats["copied"] += 1

        except Exception:
            log.exception("失败: %s", relative)
            stats["failed"] += 1

    # 汇总
    log.info("=" * 60)
    log.info(
        "备份完成 — 总计 %d | 已复制 %d | 跳过 %d | 失败 %d",
        stats["total"],
        stats["copied"],
        stats["skipped"],
        stats["failed"],
    )
    log.info("=" * 60)

    return stats


def _files_identical(a: Path, b: Path) -> bool:
    """快速判断两个文件内容是否相同（先比大小再比内容）。"""
    try:
        if a.stat().st_size != b.stat().st_size:
            return False
        # 大小相同时逐块比较（避免对大文件全量读入内存）
        with open(a, "rb") as fa, open(b, "rb") as fb:
            while True:
                chunk_a = fa.read(65536)
                chunk_b = fb.read(65536)
                if chunk_a != chunk_b:
                    return False
                if not chunk_a:
                    return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="将源文件夹的所有文件备份到目标文件夹，保持目录结构。",
        epilog="示例: python backup.py ./data ./backup/data",
    )
    parser.add_argument(
        "source",
        help="源文件夹路径",
    )
    parser.add_argument(
        "target",
        help="目标文件夹路径",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖所有文件（默认跳过内容相同的文件）",
    )

    args = parser.parse_args()
    src = Path(args.source).resolve()
    dst = Path(args.target).resolve()

    try:
        stats = backup_folder(src, dst)
    except (FileNotFoundError, NotADirectoryError) as e:
        log.error(str(e))
        sys.exit(1)

    if stats["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
