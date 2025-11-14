import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

URL = "https://thuvienphapluat.vn/van-ban/Bat-dong-san/Luat-Dat-dai-2024-31-2024-QH15-523642.aspx"
HEADERS = {"User-Agent": "legal-bot/3.0"}

def fetch_html(path_or_url):
    if path_or_url.startswith("http"):
        res = requests.get(path_or_url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        return res.text
    with open(path_or_url, "r", encoding="utf-8") as f:
        return f.read()


def get_content_block(soup):
    """Lấy khối nội dung chính – chịu được thay đổi layout."""
    candidates = [
        ("div", {"class": "content1"}),
        ("div", {"id": "content"}),
        ("div", {"class": "fck"}),
    ]
    for tag, attrs in candidates:
        block = soup.find(tag, attrs)
        if block:
            return block
    raise ValueError("Không tìm thấy khối nội dung chính trong HTML.")


def parse_law(html):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else "Văn bản pháp luật"

    content = get_content_block(soup)
    paragraphs = content.find_all("p")

    articles = []
    current = None
    current_chuong = None
    current_ten_chuong = None
    current_muc = None
    current_ten_muc = None

    for p in paragraphs:
        text = p.get_text(" ", strip=True)
        if not text:
            continue

        # --- Detect CHƯƠNG ---
        m_chuong = re.match(r"^Chương\s+([IVXLC]+)", text, re.IGNORECASE)
        if m_chuong:
            current_chuong = f"Chương {m_chuong.group(1)}"
            current_ten_chuong = None  # reset tên
            current_muc = None
            current_ten_muc = None
            continue

        # --- Detect tên chương ---
        if current_chuong and not re.match(r"^Mục\s+", text) and not re.match(r"^Điều\s+", text):
            # Tên chương là dòng sau Chương
            if current_ten_chuong is None:
                current_ten_chuong = text
                continue

        # --- Detect MỤC ---
        m_muc = re.match(r"^Mục\s+(\d+)", text)
        if m_muc:
            current_muc = f"Mục {m_muc.group(1)}"
            current_ten_muc = None
            continue

        # --- Detect tên mục ---
        if current_muc and not re.match(r"^Điều\s+", text):
            if current_ten_muc is None:
                current_ten_muc = text
                continue

        # --- Detect ĐIỀU ---
        match = re.match(r"^Điều\s+(\d+)", text)
        if match:
            if current:
                articles.append(current)

            so = int(match.group(1))
            full_title = re.sub(r"^Điều\s+\d+\.?\s*", "", text).strip()

            current = {
                "chuong": current_chuong,
                "ten_chuong": current_ten_chuong,
                "muc": current_muc,
                "ten_muc": current_ten_muc,
                "dieu_so": so,
                "tieu_de": full_title,
                "noi_dung": []
            }
            continue

        # --- Nội dung Điều ---
        if current:
            clean = re.sub(r"\s+", " ", text).strip()
            current["noi_dung"].append(clean)

    if current:
        articles.append(current)

    return {
        "tieu_de_luat": title,
        "nguon": URL,
        "tong_so_dieu": len(articles),
        "thoi_gian_scrape": datetime.now().isoformat(),
        "noi_dung": articles
    }

def export_files(data, out_dir="data"):
    os.makedirs(out_dir, exist_ok=True)

    base = re.sub(r"\W+", "_", data["tieu_de_luat"]).lower()
    txt_path = os.path.join(out_dir, base + ".txt")
    json_path = os.path.join(out_dir, base + ".json")

    # TXT
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"# {data['tieu_de_luat']}\n# Source: {data['nguon']}\n\n")
        for item in data["noi_dung"]:
            f.write(f"Điều {item['dieu_so']}. {item['tieu_de']}\n")
            for line in item["noi_dung"]:
                f.write(f"- {line}\n")
            f.write("\n")

    # JSON đẹp
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[✓] Saved TXT → {txt_path}")
    print(f"[✓] Saved JSON → {json_path}")


def main():
    html = fetch_html("file.html")
    data = parse_law(html)
    export_files(data)


if __name__ == "__main__":
    main()
