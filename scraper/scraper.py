import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

URL = "https://thuvienphapluat.vn/van-ban/Bat-dong-san/Luat-Dat-dai-2024-31-2024-QH15-523642.aspx"
HEADERS = {"User-Agent": "legal-bot/2.0"}

def fetch_html(url):
    """Lấy HTML từ URL hoặc file cục bộ"""
    if url.startswith("http"):
        print(f"[+] Fetching {url}")
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        return res.text
    else:
        print(f"[+] Reading local file {url}")
        with open(url, "r", encoding="utf-8") as f:
            return f.read()

def parse_law(html):
    """Phân tích HTML và trích xuất nội dung luật"""
    soup = BeautifulSoup(html, "html.parser")
    
    # Lấy tiêu đề từ thẻ title
    title_tag = soup.find("title")
    law_title = title_tag.get_text(strip=True) if title_tag else "Luật Đất đai 2024"
    
    # Tìm khối nội dung chính
    content = soup.find("div", class_="content1")
    if not content:
        raise ValueError("Không tìm thấy khối nội dung chính (div.content1)")
    
    laws = []
    current_article = None
    title_buffer = []  # Buffer để ghép các dòng tiêu đề bị ngắt

    # Chỉ lấy các thẻ <p> trong khối content1
    paragraphs = content.find_all("p", recursive=True)
    
    for p in paragraphs:
        # Lấy text nhưng giữ lại khoảng trắng
        text = p.get_text(strip=True)
        if not text or len(text) < 2:
            continue

        # Kiểm tra xem đây có phải là một Điều mới không
        dieu_match = re.match(r"^Điều\s+(\d+)\.\s*(.*)", text)
        
        if dieu_match:
            # Nếu có dữ liệu trong title_buffer, ghép lại tiêu đề
            if title_buffer:
                title_buffer_text = " ".join(title_buffer).strip()
                title_buffer = []
                if current_article:
                    current_article["tieu_de"] += " " + title_buffer_text
            
            # Lưu điều trước đó nếu tồn tại
            if current_article and current_article["noi_dung"].strip():
                current_article["noi_dung"] = re.sub(r'\s+', ' ', current_article["noi_dung"].strip())
                laws.append(current_article)
            
            # Bắt đầu điều mới
            dieu_so = dieu_match.group(1)
            tieu_de_part = dieu_match.group(2).strip()
            
            current_article = {
                "dieu_so": dieu_so,
                "tieu_de": tieu_de_part,
                "noi_dung": ""
            }
        else:
            # Thêm nội dung vào điều hiện tại
            if current_article is not None:
                # Loại bỏ những phần không cần thiết
                cleaned_text = text.strip()
                
                # Bỏ qua các dòng chỉ chứa thông tin định dạng hoặc trống
                if cleaned_text and not cleaned_text.startswith("http"):
                    # Kiểm tra nếu đây là phần tiếp tục của tiêu đề
                    # Điều kiện: nội dung còn trống, text ngắn, và không phải số (bullet point)
                    if (len(current_article["noi_dung"]) == 0 and 
                        len(cleaned_text) < 100 and 
                        not re.match(r'^[\d\w\.\)\-]+', cleaned_text) and
                        not cleaned_text[0].isdigit()):
                        # Thêm vào buffer tiêu đề
                        title_buffer.append(cleaned_text)
                    else:
                        # Đây là nội dung - clear title_buffer và bắt đầu với nội dung
                        title_buffer = []
                        if current_article["noi_dung"]:
                            current_article["noi_dung"] += " " + cleaned_text
                        else:
                            current_article["noi_dung"] = cleaned_text

    # Thêm điều cuối cùng
    if title_buffer:
        title_buffer_text = " ".join(title_buffer).strip()
        if current_article:
            current_article["tieu_de"] += " " + title_buffer_text
    
    if current_article and current_article["noi_dung"].strip():
        current_article["noi_dung"] = re.sub(r'\s+', ' ', current_article["noi_dung"].strip())
        laws.append(current_article)

    return {
        "tieu_de_luat": law_title,
        "nguon": URL,
        "tong_so_dieu": len(laws),
        "thoi_gian_scrape": datetime.now().isoformat(),
        "noi_dung": laws
    }

def export_files(data, out_dir="data"):
    os.makedirs(out_dir, exist_ok=True)
    
    base_name = re.sub(r"\W+", "_", data["tieu_de_luat"]).lower()
    txt_path = os.path.join(out_dir, base_name + ".txt")
    json_path = os.path.join(out_dir, base_name + ".json")

    # TXT output
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"# {data['tieu_de_luat']}\n# Source: {data['nguon']}\n\n")
        for d in data["noi_dung"]:
            f.write(f"Điều {d['dieu_so']}. {d['tieu_de']}\n")
            f.write(d["noi_dung"].strip() + "\n\n")

    # JSON output
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[✓] TXT saved to {txt_path}")
    print(f"[✓] JSON saved to {json_path}")

def main():
    # Sử dụng file cục bộ thay vì URL
    local_file = "file.html"
    html = fetch_html(local_file)
    data = parse_law(html)
    export_files(data)

if __name__ == "__main__":
    main()
