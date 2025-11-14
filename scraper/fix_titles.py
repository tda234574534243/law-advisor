"""
Script để sửa lỗi tiêu đề các Điều bị cắt ngắn
"""
import json

# Mapping tiêu đề bị cắt -> tiêu đề đầy đủ
TITLE_FIXES = {
    "Phạm": "Phạm vi điều chỉnh",
    "Đối": "Đối tượng áp dụng",
    "Giải": "Giải thích từ ngữ",
    "Người": "Người sử dụng đất",
    "Nguyên tắc sử dụng đất": "Nguyên tắc sử dụng đất",  # OK
    "Người chịu trách nhiệm trước Nhà nước đối với việc sử dụng đất": "Người chịu trách nhiệm trước Nhà nước đối với việc sử dụng đất",  # OK
    "Người chịu trách nhiệm trước Nhà nước đối với đất được giao quản": "Người chịu trách nhiệm trước Nhà nước đối với đất được giao quản lý",
    "Khuyến khích đầu tư vào sử dụng đất đai": "Khuyến khích đầu tư vào sử dụng đất đai",  # OK
    "Phân loại đất": "Phân loại đất",  # OK
    "Xác định loại đất": "Xác định loại đất",  # OK
    "Hành vi bị nghiêm cấm trong lĩnh vực đất đai": "Hành vi bị nghiêm cấm trong lĩnh vực đất đai",  # OK
    "Sở": "Sở hữu toàn dân",
    "Bảo": "Bảo hộ quyền sử dụng đất",
    "Vai": "Vai trò, trách nhiệm của Mặt trận Tổ quốc Việt Nam",
    "Nội": "Nội dung quy hoạch sử dụng đất",
}

def fix_titles(json_file):
    """Sửa lỗi tiêu đề trong file JSON"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for article in data['noi_dung']:
        title = article['tieu_de']
        
        # Kiểm tra các tiêu đề bị cắt
        if title in TITLE_FIXES:
            article['tieu_de'] = TITLE_FIXES[title]
            print(f"Fixed Điều {article['dieu_so']}: '{title}' -> '{article['tieu_de']}'")
    
    # Lưu file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Fixed and saved to {json_file}")

def fix_titles_txt(txt_file):
    """Sửa lỗi tiêu đề trong file TXT"""
    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Thay thế tiêu đề bị cắt
    replacements = {
        "Điều 1. Phạm\n": "Điều 1. Phạm vi điều chỉnh\n",
        "Điều 2. Đối\n": "Điều 2. Đối tượng áp dụng\n",
        "Điều 3. Giải\n": "Điều 3. Giải thích từ ngữ\n",
        "Điều 4. Người\n": "Điều 4. Người sử dụng đất\n",
        "Điều 12. Sở\n": "Điều 12. Sở hữu toàn dân\n",
        "Điều 17. Bảo\n": "Điều 17. Bảo hộ quyền sử dụng đất\n",
        "Điều 19. Vai\n": "Điều 19. Vai trò, trách nhiệm của Mặt trận Tổ quốc Việt Nam\n",
        "Điều 20. Nội\n": "Điều 20. Nội dung quy hoạch sử dụng đất\n",
        "Điều 7. Người chịu trách nhiệm trước Nhà nước đối với đất được giao quản\n": 
            "Điều 7. Người chịu trách nhiệm trước Nhà nước đối với đất được giao quản lý\n",
    }
    
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            print(f"Fixed: {old.strip()} -> {new.strip()}")
    
    # Lưu file
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✓ Fixed and saved to {txt_file}")

if __name__ == "__main__":
    import os
    
    # Đường dẫn tệp
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    json_file = os.path.join(data_dir, 'luật_đất_đai_2024_số_31_2024_qh15_áp_dụng_năm_2025_mới_nhất.json')
    txt_file = os.path.join(data_dir, 'luật_đất_đai_2024_số_31_2024_qh15_áp_dụng_năm_2025_mới_nhất.txt')
    
    print("=" * 60)
    print("FIX TITLES SCRIPT")
    print("=" * 60)
    
    # Sửa JSON
    if os.path.exists(json_file):
        print(f"\n[1/2] Processing JSON file...")
        fix_titles(json_file)
    else:
        print(f"❌ JSON file not found: {json_file}")
    
    # Sửa TXT
    if os.path.exists(txt_file):
        print(f"\n[2/2] Processing TXT file...")
        fix_titles_txt(txt_file)
    else:
        print(f"❌ TXT file not found: {txt_file}")
    
    print("\n" + "=" * 60)
    print("✓ All titles have been fixed!")
    print("=" * 60)
