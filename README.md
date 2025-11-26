# Ransomware Chat Formatter

Converts JSON chat logs (like those from ransomware negotiations) into polished, human-readable HTML pages.

Originally developed to process the [Casualtek/Ransomchats](https://github.com/Casualtek/Ransomchats) repository containing real-world ransomware negotiations normalized as JSON files.

## Features

- 🎨 **Clean, professional design** - White background, easy-to-read layout
- ⏰ **Smart date handling** - Parses dates from filenames (handles `20221011`, `20250425b`, `20210518_3` formats)
- 👥 **Color-coded messages** - Victim (blue) vs Attacker (red) for easy identification
- 💬 **Formatted content** - Bold party labels, indented messages, cleaned spacing
- 📊 **Statistics** - Message counts in header for quick overview
- 🔗 **GitHub integration** - Works directly with GitHub URLs, handles spaces in paths
- 📱 **Responsive design** - Clean rendering in any modern browser
- 📂 **Bulk processing** - Process entire repositories with hierarchical output structure
- ⚡ **Quality verified** - Tested with 595 messages across 10 random chats

## Scripts

### 1. `format_chat.py` - Single Chat Formatter

Process a single JSON chat file and convert it to HTML.

**Usage:**
```bash
python format_chat.py <url_to_json>
```

**Examples:**
```bash
python format_chat.py https://raw.githubusercontent.com/Casualtek/Ransomchats/main/BlackBasta/20221011.json
```

**Output:** Generates `chat_<chat_id>.html` in the current directory (e.g., `chat_20221011.html`)

---

### 2. `group_format_chat.py` - Bulk Repository Formatter

Process an entire GitHub repository of ransomware chats at once.

**Usage:**
```bash
python group_format_chat.py <github_repo_url>
```

**Example:**
```bash
python group_format_chat.py https://github.com/Casualtek/Ransomchats/tree/main
```

**Output:** Creates `ransomware_chats/` directory with:
- Organized subdirectories by ransomware group (e.g., `BlackBasta/`, `Conti/`)
- HTML files for each chat maintaining original naming
- `index.html` at root level with statistics and links to all groups
- `index.html` in each group folder listing all chats


**Configuration:**
Edit these variables at the top of `group_format_chat.py`:
- `REQUEST_DELAY = 1.5` - Delay between requests (seconds) to avoid rate limiting
- `MAX_RETRIES = 3` - Maximum retry attempts for failed network requests

**Features:**
- ✅ **GitHub API integration** - Uses GitHub's API for reliable directory/file listing (unauthenticated)
- ✅ **URL encoding** - Properly handles spaces and special characters in paths
- ✅ **Smart filtering** - Automatically skips non-data folders (`.github`, `parsers`, `LICENSE`, `README`, etc.)
- ✅ **Error handling** - Retries failed network requests up to 3 times with detailed error messages
- ✅ **Empty directory handling** - Creates placeholder READMEs for empty source directories
- ✅ **Date extraction** - Intelligently parses dates from various filename formats
- ✅ **Index generation** - Creates navigable index pages at root and group levels
- ✅ **Overwrite mode** - Re-running will overwrite existing files with updated versions

---

## Output Structure

### Example: Processing Casualtek/Ransomchats

When you run `group_format_chat.py` on the full repository, you get:

```
json_chat_formatter/
├── format_chat.py              # Single file processor
├── group_format_chat.py        # Bulk processor
├── README.md                   # This file
├── chat_20221011.html          # Example single file output
└── ransomware_chats/           # Bulk processor output
    ├── index.html              # Main index (24 groups, 234 chats)
    │
    ├── Akira/
    │   ├── index.html          # Group index (60 chats)
    │   ├── 20230529.html
    │   ├── 20230606.html
    │   ├── ...
    │   └── 20250425b.html      # Handles date suffixes
    │
    ├── BlackBasta/
    │   ├── index.html          # Group index (5 chats)
    │   ├── 20221011.html
    │   └── ...
    │
    ├── Conti/
    │   ├── index.html          # Group index (32 chats)
    │   └── ...
    │
    ├── Hunters International/  # Handles spaces in names
    │   ├── index.html
    │   └── 20240510.html
    │
    ├── lockbit3.0/
    │   ├── index.html          # Group index (42 chats)
    │   ├── continental_com.html
    │   └── ...
    │
    └── ... (20 more groups)
```

**Statistics (as of last run):**
- 24 ransomware groups
- 234 total chats converted
- Groups include: Akira (60), Conti (32), lockbit3.0 (42), REvil (20), and more

---

## JSON Format

Expected JSON structure:
```json
{
  "chat_id": "20221011",
  "messages": [
    {
      "party": "Victim",
      "content": "Message text here",
      "timestamp": "14:30"
    },
    {
      "party": "Black Basta",
      "content": "Response text here",
      "timestamp": "14:35"
    }
  ]
}
```

**Notes:**
- `chat_id`: Usually a date (YYYYMMDD) or unique identifier
- `party`: Name of the sender (e.g., "Victim", "Black Basta", etc.)
- `content`: Message text (can include newlines)
- `timestamp`: Time in 24-hour format (e.g., "14:30")

---

## Requirements

- Python 3.6+
- No external dependencies (uses standard library only)

---

## Quality Verification

Both scripts have been thoroughly tested:

- ✅ **10 random chats verified** against original JSON sources
- ✅ **595 messages** checked across diverse groups
- ✅ **100% content preservation** - All message content present
- ✅ **Format improvements** - Extra blank lines cleaned while preserving all text

**What gets cleaned:**
- Multiple consecutive blank lines (`\n\n\n` → `\n`)
- Leading/trailing whitespace
- **All actual message content is preserved exactly**

---

## Troubleshooting

### Common Issues

**1. "URL can't contain control characters"**
- Fixed in current version
- Issue was with spaces in directory/file names
- Now properly URL-encodes all paths

**2. "Invalid JSON" error**
- Check that the source file is valid JSON
- Script will exit with detailed error message
- Verify the URL is correct

**3. Rate limiting from GitHub**
- Increase `REQUEST_DELAY` in `group_format_chat.py`
- Default 1.5s works well for most cases
- GitHub API has generous rate limits for public repos

**4. Empty or missing output**
- Check that source directory contains JSON files
- Script creates placeholder README for empty directories
- Use `--limit 2` to test with small sample first

### Running on macOS/Linux

```bash
# Make scripts executable
chmod +x format_chat.py group_format_chat.py

# Run with python3
python3 format_chat.py <url>
python3 group_format_chat.py <url>
```

---

## License

Free to use and modify as long as you mention source.

Created for processing ransomware negotiation data from public sources.

## Notes

- Works with any JSON that follows the above detailed format.
- HTML output is self-contained (no external CSS/JS files needed).
- All processing happens locally - no data sent to external services.
