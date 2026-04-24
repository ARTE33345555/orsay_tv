import hashlib, os, requests

def verify_and_patch(component, local_path, server_url, expected_hash):
    # 1. Завантаження патча
    response = requests.get(server_url)
    data = response.content
    
    # 2. Перевірка цілісності (захист від "цегли")
    if hashlib.md5(data).hexdigest() == expected_hash:
        # 3. Створення бекапу перед заміною
        os.rename(local_path, local_path + ".bak")
        # 4. Застосування патчу
        with open(local_path, "wb") as f:
            f.write(data)
        print(f"[OK] {component} updated!")
    else:
        print("[ERROR] Corrupted file! Rollback triggered.")
        os.rename(local_path + ".bak", local_path)
