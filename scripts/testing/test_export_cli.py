#!/usr/bin/env python3
"""
Quick test for the export CLI functionality
"""
import os
import subprocess
import sys
import tempfile


def test_export_cli():
    """Test the export CLI with index-only mode"""
    print("🧪 Testing export CLI...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test index-only mode (safe, doesn't require network)
        cmd = [
            sys.executable,
            "scripts/export_cli.py",
            "--index-only",
            "--output-dir", tmpdir,
            "--db-path", os.path.join(tmpdir, "test.sqlite")
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
            )
            if result.returncode == 0:
                print("✅ Export CLI test passed")
                return True
            else:
                print(f"❌ Export CLI test failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("⚠️  Export CLI test timed out")
            return False
        except (OSError, subprocess.SubprocessError) as e:
            print(f"❌ Export CLI test error: {e}")
            return False


if __name__ == "__main__":
    success = test_export_cli()
    sys.exit(0 if success else 1)
