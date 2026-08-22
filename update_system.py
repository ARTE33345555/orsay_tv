import hashlib
import os
import requests
import shutil
import tempfile
import time


def compute_md5_for_file(path, chunk_size=8192):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_and_patch(component, local_path, server_url, expected_hash, timeout=30):
    """Download a patch from server_url, verify its MD5 against expected_hash,
    and atomically replace local_path while keeping a timestamped backup.

    Returns True on success, False otherwise.
    """
    print(f"[UPDATE] Verifying component: {component}")

    # 1. Download to a temporary file
    try:
        with requests.get(server_url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False) as tmpf:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        tmpf.write(chunk)
                tmp_name = tmpf.name
    except requests.RequestException as e:
        print(f"[ERROR] Failed to download {component} from {server_url}: {e}")
        return False

    # 2. Compute MD5 of downloaded file
    try:
        downloaded_md5 = compute_md5_for_file(tmp_name)
    except Exception as e:
        print(f"[ERROR] Failed to compute MD5 for downloaded file: {e}")
        os.remove(tmp_name)
        return False

    if downloaded_md5 != expected_hash:
        print(f"[ERROR] Hash mismatch for {component} (got {downloaded_md5}, expected {expected_hash}).")
        os.remove(tmp_name)
        return False

    # 3. Create a backup of the existing file (if any)
    backup_path = None
    try:
        if os.path.exists(local_path):
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            backup_path = f"{local_path}.bak.{timestamp}"
            shutil.copy2(local_path, backup_path)
            print(f"[UPDATE] Created backup: {backup_path}")

        # 4. Atomically move the downloaded file into place
        os.replace(tmp_name, local_path)
        print(f"[OK] {component} updated at {local_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to apply update for {component}: {e}")
        # Attempt to restore from backup if we created one
        try:
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, local_path)
                print(f"[RECOVERY] Restored from backup: {backup_path}")
        except Exception as _:
            print("[RECOVERY] Failed to restore backup. Manual intervention required.")
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        return False


if __name__ == "__main__":
    # Simple self-test (won't actually fetch unless you provide real values)
    print("update_system.py loaded. Use verify_and_patch(component, local_path, server_url, expected_hash)")
