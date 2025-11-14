# 🕷️ Scraper Module

Web scraper for Vietnamese law documents.

## Overview

Collects Vietnamese law text from web sources and exports to JSON format for use in the law query system.

## Files

```
scraper/
├── scraper.py          # Main scraper logic
├── fix_titles.py       # Data cleaning utility
├── data/               # Collected data
│   └── *.json          # Law documents (JSON format)
└── README.md
```

## Usage

### Run Scraper

```bash
python scraper/scraper.py
```

Output: `scraper/data/luật_*.json`

### Data Format

Input (HTML):
```html
<h2>Điều 69 - Bồi thường, hỗ trợ</h2>
<p>Nhà nước bồi thường, hỗ trợ cho các chủ thể...</p>
```

Output (JSON):
```json
{
  "tieu_de_luat": "Luật Đất Đai 2024",
  "noi_dung": [
    {
      "dieu_so": 69,
      "tieu_de": "Bồi thường, hỗ trợ",
      "noi_dung": "Nhà nước bồi thường..."
    }
  ],
  "source_url": "http://...",
  "scraped_date": "2024-01-14"
}
```

## Data Cleaning

### Using fix_titles.py

```bash
python scraper/fix_titles.py
```

Fixes:
- Inconsistent article numbering
- Missing article titles
- Formatting issues
- Encoding problems

## Integration with Pipeline

### 1. Scrape Data

```bash
python scraper/scraper.py
# Creates: scraper/data/luật_*.json
```

### 2. Ingest to Database

```bash
python backend/ingest.py
# Reads: scraper/data/*.json
# Writes to: TinyDB or MongoDB
```

### 3. Build Indexes

```bash
python backend/indexer.py
# Creates: TF-IDF + optional embeddings
```

### 4. Query System

```bash
python app.py
# Now ready for queries
```

## Source Data Format

### Expected JSON Structure

```json
{
  "tieu_de_luat": "Luật Đất Đai 2024 - Số 31/2024/QH15",
  "noi_dung": [
    {
      "dieu_so": 1,
      "tieu_de": "Phạm vi điều chỉnh",
      "noi_dung": "Luật này quy định...",
      "dieu_khoan": []
    },
    {
      "dieu_so": 2,
      "tieu_de": "Quyền và nghĩa vụ...",
      "noi_dung": "...",
      "dieu_khoan": [
        {
          "khoan_so": 1,
          "noi_dung": "..."
        }
      ]
    }
  ],
  "so_dieu": 210,
  "effective_date": "2025-01-01",
  "source_url": "http://..."
}
```

## Supported Sources

### Vietnamese Government Sources
- [Thư Viện Pháp Luật](http://www.thuvienphapluat.vn)
- [Lao Động](http://laodong.vn)
- [VietnamNet](http://vietnamnet.vn)
- [Báo Xã Hội](http://baoxahoi.vn)

### Configuration

```python
# scraper.py
SOURCES = [
    "http://example.com/laws",
    "http://thuvienphapluat.vn/...",
]

OUTPUT_DIR = "scraper/data/"
```

## Troubleshooting

### SSL Certificate Error

```python
# In scraper.py
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

### Encoding Issues

```python
# Ensure UTF-8 encoding
with open(file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
```

### Missing Data

1. Check source website accessibility
2. Verify CSS selectors in scraper.py
3. Check output file in scraper/data/

### Incomplete Articles

```bash
# Use fix_titles.py to fill gaps
python scraper/fix_titles.py

# Or manually add missing articles
```

## Data Validation

### Pre-Ingest Validation

```python
# scraper/validate_data.py
def validate_json(file):
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check required fields
    assert "tieu_de_luat" in data
    assert "noi_dung" in data
    assert isinstance(data["noi_dung"], list)
    
    # Check articles
    for article in data["noi_dung"]:
        assert "dieu_so" in article
        assert "noi_dung" in article
```

## Performance

| Operation | Time |
|-----------|------|
| Scrape 1 law | ~2-5s |
| Process 200 articles | ~1-2s |
| Save to JSON | <1s |

## File Management

### View Scraped Data

```bash
ls -la scraper/data/
```

### Count Articles

```bash
python -c "
import json
with open('scraper/data/luật_đất_đai.json') as f:
    data = json.load(f)
print(f'Articles: {len(data[\"noi_dung\"])}')"
```

### Backup Data

```bash
cp -r scraper/data/ scraper/data.backup/
```

### Clean Old Data

```bash
rm scraper/data/*.old.json
```

## Advanced Features

### Custom Scraper

```python
# Create custom scraper for specific source
class MyLawScraper:
    def __init__(self, url):
        self.url = url
    
    def fetch_articles(self):
        # Custom fetch logic
        pass
    
    def parse_article(self, html):
        # Custom parse logic
        pass
    
    def export(self, output_file):
        # Export to JSON
        pass
```

### Multi-Source Collection

```bash
# Scrape multiple sources
python scraper/scraper.py --source thuvienphapluat
python scraper/scraper.py --source laodong

# Merge results
python scraper/merge_sources.py
```

### Incremental Updates

```bash
# Only scrape new articles
python scraper/scraper.py --update-only

# Check for changes
python scraper/check_updates.py
```

## Best Practices

1. **Rate Limiting**
   - Add delays between requests
   - Respect robots.txt
   - Use appropriate User-Agent

2. **Error Handling**
   - Retry failed requests
   - Log errors
   - Continue on failures

3. **Data Validation**
   - Validate JSON format
   - Check article completeness
   - Verify links

4. **Storage**
   - Backup original data
   - Version control updates
   - Archive old versions

## License Compliance

Ensure data collection complies with:
- Website terms of service
- Local copyright laws
- License requirements
- Fair use guidelines

---

**Version 2.0 | Scraper Module**
