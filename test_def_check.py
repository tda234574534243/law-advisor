from backend.bot import check_definition_exists_in_db

exists, defn = check_definition_exists_in_db('quyền sử dụng đất')
print(f'Exists: {exists}')
print(f'Definition: {defn[:150] if defn else "Not found"}')
