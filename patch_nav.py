#!/usr/bin/env python3
"""
patch_nav.py — Pluribus nav updater
Run this from the root of your pluribus repo:
    python3 patch_nav.py

What it does:
  - Finds every .html file in the current directory
  - Replaces the old nav link block with the new 4-link structure
  - Marks the correct active link based on filename
  - Writes the file in-place

Old nav:  Dashboard | Resources | Clip Drop | Mast Mentions | Administration
New nav:  Mast HQ   | Political Universe | Clip Drop | Mast Mentions

Also renames references:
  - dashboard_v2.html  →  mast-hq.html
  - resources.html     →  political-universe.html
"""

import os
import re
import shutil
from pathlib import Path

# ── FILE → PAGE IDENTITY MAP ────────────────────────────────────────────────
# Maps filename → which nav link should be "active"
# 'none' = no link is active (external/utility pages)
ACTIVE_MAP = {
    'mast-hq.html':            'masthq',
    'dashboard_v2.html':       'masthq',   # old filename, still patch it
    'index.html':              'masthq',
    'affiliations.html':       'masthq',
    'district.html':           'masthq',
    'messaging.html':          'masthq',
    'social-approvals.html':   'masthq',
    'strategy.html':           'masthq',
    'rapid-response.html':     'masthq',
    'list-matcher.html':       'masthq',
    'observance-calendar.html':'masthq',
    'political-universe.html': 'poluniv',
    'resources.html':          'poluniv',  # old filename
    'whitehouse.html':         'poluniv',
    'clipdrop.html':           'clipdrop',
    'mast-mentions.html':      'mentions',
    'calendar.html':           'masthq',
}

def build_nav(active_page):
    """Return the full new nav-inner block."""
    def lnk(label, href, key):
        cls = 'nav-link active' if active_page == key else 'nav-link'
        return f'    <a href="{href}" class="{cls}">{label}</a>'

    lines = [
        '  <div class="nav-inner">',
        '    <a href="mast-hq.html" class="nav-logo">P</a>',
        lnk('Mast HQ',            'mast-hq.html',            'masthq'),
        lnk('Political Universe',  'political-universe.html', 'poluniv'),
        lnk('Clip Drop',           'clipdrop.html',           'clipdrop'),
        lnk('Mast Mentions',       'mast-mentions.html',      'mentions'),
        '    <div class="nav-date" id="navDate"></div>',
        '  </div>',
    ]
    return '\n'.join(lines)

# ── PATTERNS TO REPLACE ──────────────────────────────────────────────────────
# Matches the entire nav-inner div including all its children
NAV_PATTERN = re.compile(
    r'<div class="nav-inner">.*?</div>\s*(?=</div>)',
    re.DOTALL
)

# Old href references to update throughout the file body (tiles, links etc.)
HREF_RENAMES = [
    # old href                       new href
    ('href="dashboard_v2.html"',    'href="mast-hq.html"'),
    ('href="resources.html"',       'href="political-universe.html"'),
    # nav-logo link
    ('href="dashboard_v2.html" class="nav-logo"', 'href="mast-hq.html" class="nav-logo"'),
]

def patch_file(filepath):
    fname = filepath.name
    active = ACTIVE_MAP.get(fname, 'none')
    
    text = filepath.read_text(encoding='utf-8', errors='replace')
    original = text
    
    # 1. Replace nav-inner block
    new_nav_inner = build_nav(active)
    text = NAV_PATTERN.sub(new_nav_inner + '\n  ', text, count=1)
    
    # 2. Rename stale hrefs anywhere in the file
    for old, new in HREF_RENAMES:
        text = text.replace(old, new)
    
    # 3. Remove any remaining "Administration" nav links
    text = re.sub(
        r'\s*<a href="whitehouse\.html" class="nav-link[^"]*">Administration</a>',
        '',
        text
    )
    
    if text != original:
        # Backup original
        backup = filepath.with_suffix('.html.bak')
        shutil.copy2(filepath, backup)
        filepath.write_text(text, encoding='utf-8')
        print(f"  ✓ patched  {fname}  (backup: {backup.name})")
    else:
        print(f"  — skipped  {fname}  (no nav block found or no changes)")

# ── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    repo_root = Path('.')
    html_files = sorted(repo_root.glob('*.html'))
    
    if not html_files:
        print("No .html files found in current directory.")
        print("Make sure you're running this from your pluribus repo root.")
        raise SystemExit(1)
    
    print(f"Found {len(html_files)} HTML files. Patching navs...\n")
    for f in html_files:
        if f.suffix == '.html' and not f.name.endswith('.bak'):
            patch_file(f)
    
    print("\nDone. Review the .bak files if you need to undo anything.")
    print("\nNext steps:")
    print("  1. Copy mast-hq.html, political-universe.html, rapid-response.html,")
    print("     list-matcher.html, observance-calendar.html into the repo")
    print("  2. Optionally delete or redirect dashboard_v2.html and resources.html")
    print("  3. git add -A && git commit -m 'Nav: Mast HQ / Political Universe restructure'")
    print("  4. git push  →  Netlify auto-deploys")
