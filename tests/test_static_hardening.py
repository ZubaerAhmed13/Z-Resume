from pathlib import Path
import re, shutil, subprocess

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'index.html').read_text(encoding='utf-8')
JS_FILES = sorted((ROOT / 'assets' / 'js').glob('*.js'))
CSS_FILES = sorted((ROOT / 'assets' / 'css').glob('*.css'))
SOURCE = HTML + '\n' + '\n'.join(p.read_text(encoding='utf-8') for p in JS_FILES) + '\n' + '\n'.join(p.read_text(encoding='utf-8') for p in CSS_FILES)

def require(cond, message):
    if not cond:
        raise AssertionError(message)

def absent(pattern, message, flags=re.I):
    require(re.search(pattern, SOURCE, flags) is None, message)

def present(pattern, message, flags=re.I):
    require(re.search(pattern, SOURCE, flags) is not None, message)

require(JS_FILES, 'external JavaScript assets are required')
require(CSS_FILES, 'external CSS asset is required')
require('<style>' not in HTML, 'editable CSS must live in assets/css')
require(re.search(r'<script(?![^>]*src=)', HTML, re.I) is None, 'editable JavaScript must live in assets/js')

absent(r'Zubaer Ahmed', 'real person name must not be embedded in production defaults')
absent(r'zubaerknight@gmail\.com', 'real email must not be embedded in production defaults')
absent(r'Liebenauer Str\. 81', 'real street address must not be embedded in production defaults')
present(r"fullName:'Alex Morgan'", 'synthetic demo fixture should remain available')
present(r"alex\.morgan@example\.com", 'demo email must use example.com')

absent(r'api\.anthropic\.com', 'browser-side Anthropic endpoint must not exist')
present(r"connect-src 'none'", 'CSP must block browser API connections in the static build')
present(r'External AI is intentionally disabled', 'static AI limitation must be explicit')
absent(r'__CF\$cv|challenge-platform|cdn-cgi', 'Cloudflare challenge artifact must not ship')

present(r'const STORAGE_VERSION = 3;', 'workspace schema must be v3')
present(r'normalizeWorkspaceV3', 'v3 migration must exist')
present(r'ws\.masterProfile\.personal\.summary', 'master summary must migrate to canonical personal.summary')
absent(r'data-mp="summary"', 'master summary editor must not write legacy master.summary')
present(r'data-mp="personal\.summary"', 'master summary editor must write canonical path')

present(r'function safeImageSrc', 'central photo URL validation must exist')
absent(r'data-gap-add="\' \+ g\.text', 'JD gap text must not be inserted raw into an attribute')
absent(r"\+ v\.text \+ '</div>'", 'variant text must not be inserted raw into HTML')
present(r'hasUnsafeObjectKeys', 'backup import must reject prototype-pollution keys')

present(r'Print / Save as PDF', 'supported PDF label must describe browser print')
present(r'setTimeout\(\(\) => window\.print\(\), 60\)', 'PDF action must route to browser print')
present(r'ATS compatibility preflight', 'ATS feature must be labelled as a preflight')
present(r'cannot guarantee how any employer ATS', 'ATS limitation must be explicit')

present(r'compatibilitySectionHTML', 'template section fallback must exist')
absent(r'\.page-break\{ height:970px', 'fixed fake page-break spacer must not return')
present(r"cv\.addEventListener\('pointerdown'", 'photo crop must use Pointer Events')
absent(r"cv\.addEventListener\('mousedown'", 'mouse-only crop handler must not return')

present(r'Delete local workspace', 'complete local deletion action must be explicit')
present(r'Saved in this browser', 'save status must describe actual persistence scope')

node = shutil.which('node')
if node:
    for p in JS_FILES:
        proc = subprocess.run([node, '--check', str(p)], text=True, capture_output=True)
        require(proc.returncode == 0, f'{p.name} syntax failed:\n{proc.stderr}')

print(f'PASS: static hardening regression suite ({len(JS_FILES)} JS assets, {len(CSS_FILES)} CSS assets)')
