#!/usr/bin/env python3
"""
GitHub Actions Artifacts 시뮬레이션

이 스크립트는 로컬 환경에서 GitHub Actions의 Artifacts 기능을 시뮬레이션합니다.
중복 기사 방지 기능을 로컬에서 테스트할 수 있습니다.

Usage:
    python scripts/simulate_github_actions.py
"""

import os
import sys
import shutil
from pathlib import Path

# 시뮬레이션 디렉토리
ARTIFACTS_DIR = Path("temp_artifacts")
DB_PATH = Path("data/articles.db")


def simulate_download_artifact():
    """
    Artifact 다운로드 시뮬레이션.

    이전 실행의 DB를 복원합니다.
    """
    print("\n" + "=" * 60)
    print("📥 Step 1: Download Previous Artifact")
    print("=" * 60)

    artifact_db = ARTIFACTS_DIR / "articles.db"

    if artifact_db.exists():
        print(f"✅ Found previous artifact: {artifact_db}")
        file_size = artifact_db.stat().st_size
        print(f"   Size: {file_size / 1024:.2f} KB")

        # data/ 디렉토리 생성
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        # DB 복사
        shutil.copy(artifact_db, DB_PATH)
        print(f"✅ Restored to: {DB_PATH}")

        # DB 통계 확인
        show_db_stats(DB_PATH, "Previous Database")

        return True
    else:
        print("ℹ️  No previous artifact found (first run)")
        print("   This is normal for the first execution")
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        return False


def simulate_upload_artifact():
    """
    Artifact 업로드 시뮬레이션.

    현재 DB를 artifact로 저장합니다.
    """
    print("\n" + "=" * 60)
    print("📤 Step 3: Upload Updated Artifact")
    print("=" * 60)

    if not DB_PATH.exists():
        print("❌ No database to upload")
        print("   Database should have been created by main.py")
        return False

    # artifacts 디렉토리 생성
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # DB 복사
    artifact_db = ARTIFACTS_DIR / "articles.db"
    shutil.copy(DB_PATH, artifact_db)

    file_size = artifact_db.stat().st_size
    print(f"✅ Uploaded to: {artifact_db}")
    print(f"   Size: {file_size / 1024:.2f} KB")
    print(f"   Retention: 90 days (simulated)")

    # 최종 DB 통계
    show_db_stats(DB_PATH, "Final Database")

    return True


def show_db_stats(db_path: Path, title: str = "Database"):
    """
    DB 통계 표시.

    Args:
        db_path: DB 파일 경로
        title: 제목
    """
    if not db_path.exists():
        print(f"ℹ️  {title}: No database yet")
        return

    try:
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 기사 통계
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN notified = 1 THEN 1 END) as notified,
                COUNT(CASE WHEN notified = 0 THEN 1 END) as pending
            FROM articles
        """)

        stats = cursor.fetchone()

        print(f"\n📊 {title} Statistics:")
        print(f"   📚 Total articles: {stats[0]}")
        print(f"   ✉️  Notified: {stats[1]}")
        print(f"   🆕 Pending: {stats[2]}")

        conn.close()

    except Exception as e:
        print(f"⚠️  Could not read stats: {e}")


def run_main_program():
    """
    메인 프로그램 실행 안내.
    """
    print("\n" + "=" * 60)
    print("🚀 Step 2: Run Main Program")
    print("=" * 60)
    print("\nNow run the monitoring program:")
    print("   python main.py --mode test")
    print("\nPress Enter after the program completes...")

    try:
        input()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)


def show_comparison():
    """
    이전/현재 DB 비교.
    """
    print("\n" + "=" * 60)
    print("🔍 Comparison: Before vs After")
    print("=" * 60)

    artifact_db = ARTIFACTS_DIR / "articles.db"
    current_db = DB_PATH

    if not artifact_db.exists():
        print("ℹ️  No previous artifact to compare (first run)")
        return

    if not current_db.exists():
        print("❌ Current database not found")
        return

    try:
        import sqlite3

        # 이전 DB 통계
        conn1 = sqlite3.connect(artifact_db)
        cursor1 = conn1.cursor()
        cursor1.execute("SELECT COUNT(*) FROM articles")
        before_count = cursor1.fetchone()[0]
        conn1.close()

        # 현재 DB 통계
        conn2 = sqlite3.connect(current_db)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT COUNT(*) FROM articles")
        after_count = cursor2.fetchone()[0]
        conn2.close()

        new_articles = after_count - before_count

        print(f"📊 Before: {before_count} articles")
        print(f"📊 After:  {after_count} articles")

        if new_articles > 0:
            print(f"✅ New articles added: {new_articles}")
        elif new_articles == 0:
            print("ℹ️  No new articles (all duplicates)")
        else:
            print(f"⚠️  Articles decreased: {abs(new_articles)}")

    except Exception as e:
        print(f"⚠️  Could not compare: {e}")


def cleanup():
    """
    정리 옵션 제공.
    """
    print("\n" + "=" * 60)
    print("🧹 Cleanup Options")
    print("=" * 60)
    print("\nDo you want to delete the artifacts? (y/N): ", end="")

    try:
        response = input().strip().lower()
        if response == 'y':
            if ARTIFACTS_DIR.exists():
                shutil.rmtree(ARTIFACTS_DIR)
                print(f"✅ Deleted: {ARTIFACTS_DIR}")
            if DB_PATH.exists():
                DB_PATH.unlink()
                print(f"✅ Deleted: {DB_PATH}")
            print("\nNext run will be like a first run (no duplicates)")
        else:
            print("ℹ️  Artifacts kept for next run")
            print(f"   Location: {ARTIFACTS_DIR}")
    except KeyboardInterrupt:
        print("\n\nℹ️  Cleanup skipped")


def main():
    """
    메인 시뮬레이션 함수.
    """
    print("=" * 60)
    print("GitHub Actions Artifacts Simulation")
    print("Gomu News Monitor - Duplicate Prevention Test")
    print("=" * 60)

    # Step 1: Artifact 다운로드
    had_previous = simulate_download_artifact()

    # Step 2: 메인 프로그램 실행 안내
    run_main_program()

    # Step 2.5: 비교
    show_comparison()

    # Step 3: Artifact 업로드
    simulate_upload_artifact()

    # 완료 메시지
    print("\n" + "=" * 60)
    print("✅ Simulation Complete!")
    print("=" * 60)

    if had_previous:
        print("\nThis was a subsequent run:")
        print("  - Previous database was restored")
        print("  - Duplicate articles were prevented")
        print("  - Only new articles were processed")
    else:
        print("\nThis was the first run:")
        print("  - No previous database found")
        print("  - All articles were new")
        print("  - Database created for next run")

    print(f"\nArtifacts stored in: {ARTIFACTS_DIR.absolute()}")
    print("Run this script again to simulate the next execution")

    # 정리 옵션
    cleanup()

    print("\n" + "=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
