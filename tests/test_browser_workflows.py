#!/usr/bin/env python3
from pathlib import Path
import json, re, sys, zipfile, subprocess, os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-artifacts'
OUT.mkdir(exist_ok=True)

def build_inline_html():
    html=(ROOT/'index.html').read_text()
    html=re.sub(r'<meta[^>]+http-equiv=["\']Content-Security-Policy["\'][^>]*>', '', html, flags=re.I)
    css_links = re.findall(r'<link[^>]+href=["\'](assets/css/[^"\']+\.css)["\'][^>]*>', html, flags=re.I)
    css = '\n'.join((ROOT / href).read_text() for href in css_links)
    html=re.sub(r'<link[^>]+href=["\']assets/css/[^"\']+\.css["\'][^>]*>', '', html, flags=re.I)
    html=html.replace('</head>', '<style>'+css+'</style></head>', 1)
    html=re.sub(r'<script\s+src=["\']assets/js/[^"\']+["\']\s*></script>', '', html, flags=re.I)
    return html

def storage_shim(page):
    page.evaluate("""() => {
      const m = new Map();
      const s = {getItem:k=>m.has(String(k))?m.get(String(k)):null,setItem:(k,v)=>m.set(String(k),String(v)),removeItem:k=>m.delete(String(k)),clear:()=>m.clear(),key:i=>Array.from(m.keys())[i]||null,get length(){return m.size}};
      Object.defineProperty(window,'localStorage',{value:s,configurable:true});
    }""")

AXE_JS = ROOT / 'node_modules' / 'axe-core' / 'axe.min.js'

def install_axe(page):
    if not AXE_JS.is_file():
        if os.environ.get('REQUIRE_AXE') == '1':
            raise AssertionError('axe-core is required but node_modules/axe-core/axe.min.js is missing')
        return False
    page.add_script_tag(content=AXE_JS.read_text())
    return True

def assert_axe_clean(page, label):
    results = page.evaluate("""async () => await axe.run(document, {
      runOnly: { type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa'] },
      resultTypes: ['violations']
    })""")
    violations = results.get('violations', [])
    if violations:
        summary = []
        for violation in violations:
            targets = [node.get('target', []) for node in violation.get('nodes', [])[:4]]
            summary.append(f"{violation.get('id')}[{violation.get('impact')}]: {violation.get('help')} targets={targets}")
        raise AssertionError(f"axe WCAG A/AA violations in {label}: " + ' | '.join(summary))

def load_app(page):
    errors=[]
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.set_content(build_inline_html(), wait_until='domcontentloaded')
    storage_shim(page)
    script_srcs = re.findall(r'<script\s+src=["\']([^"\']+)["\']', (ROOT/'index.html').read_text())
    assert script_srcs, 'index.html must declare external JavaScript assets'
    for src in script_srcs:
        js = ROOT / src
        assert js.is_file(), f'Missing script asset referenced by index.html: {src}'
        page.add_script_tag(content=js.read_text())
    page.wait_for_timeout(150)
    assert not errors, 'page errors: '+repr(errors)
    return errors

FIXTURE = {
 'personal': {'fullName':'Café — résumé জুবায়ের আহমেদ','title':'Financial Analyst','email':'alex@example.com','phone':'+49 123','location':'Zürich, Straße 1','website':'https://example.com/portfolio','linkedin':'https://linkedin.com/in/example','photo':'','summary':'Unicode summary Café — résumé Straße Zürich জুবায়ের আহমেদ'},
 'experience':[{'id':'e1','jobTitle':'Analyst','company':'Example GmbH','location':'Berlin','startDate':'Jan 2025','endDate':'','current':True,'description':'Improved reporting quality\nBuilt dashboard','include':True}],
 'education':[{'id':'ed1','degree':'BBA Finance','school':'Example University','location':'','startDate':'2020','endDate':'2023','description':'Finance','include':True}],
 'skills':['Excel','Financial Analysis'], 'tools':['SAP S/4HANA (learning)'],
 'languages':[{'id':'l1','name':'German','level':'A1','include':True},{'id':'l2','name':'English','level':'C1','include':True}],
 'certificates':[{'id':'c1','name':'Project Management','issuer':'Example','year':'2026','credentialURL':'https://example.com/cert','include':True}],
 'projects':[{'id':'p1','name':'UNICODE-PROJECT','link':'https://example.com/project','description':'Project result','include':True}],
 'achievements':[{'id':'a1','title':'UNIQUE-ACHIEVEMENT','description':'Award detail','include':True}],
 'hobbies':[{'id':'h1','name':'UNIQUE-HOBBY','include':True}],
 'volunteering':[{'id':'v1','role':'UNIQUE-VOLUNTEER','organization':'Example Org','dates':'2024','description':'Helped','include':True}],
 'publications':[{'id':'pub1','title':'UNIQUE-PUBLICATION','venue':'Journal','year':'2026','include':True}],
 'coursework':[{'id':'cw1','name':'UNIQUE-COURSEWORK','institution':'University','year':'2026','include':True}],
 'references':[{'id':'r1','name':'UNIQUE-REFERENCE','contact':'Manager','include':True}],
 'customSections':[{'id':'x1','title':'UNIQUE-CUSTOM','content':'Custom unicode জুবায়ের','include':True}],
 'coverLetter': {}
}

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    load_app(page)
    axe_available = install_axe(page)
    assert page.locator('#p-name').input_value()==''
    assert page.locator('.tpl-card').count() >= 7
    # fixture + all-template content preservation
    page.evaluate("d => { state.data=rfNormalizeData(d); const cv=currentCV(); cv.data=clone(state.data); renderResume(); }", FIXTURE)
    templates=page.evaluate("Object.keys(TEMPLATES)")
    required=['UNICODE-PROJECT','UNIQUE-ACHIEVEMENT','UNIQUE-HOBBY','UNIQUE-VOLUNTEER','UNIQUE-PUBLICATION','UNIQUE-COURSEWORK','UNIQUE-REFERENCE','UNIQUE-CUSTOM']
    for tpl in templates:
        page.evaluate("t => {state.template=t; renderResume();}", tpl)
        text=page.locator('#resume').inner_text()
        missing=[x for x in required if x not in text]
        assert not missing, f'{tpl} omitted {missing}'
    # hostile data stays inert
    hostile='\"><img src=x onerror=window.__PWNED=1>'
    page.evaluate("x => {state.data.personal.fullName=x; state.data.customSections=[{id:'bad',title:'Bad',content:x,include:true}]; renderResume();}", hostile)
    assert page.evaluate("window.__PWNED || 0") == 0
    assert page.locator('#resume img[src="x"]').count()==0
    assert '<img' in page.locator('#resume').inner_text()
    # language-level negative case
    page.evaluate("d => {state.data=rfNormalizeData(d);}", FIXTURE)
    result=page.evaluate("analyzeJD('Requirements:\\n• German B2 required\\n• Strong Microsoft Excel skills', state.data)")
    german=[r for r in result['reqs'] if r['cat']=='language'][0]
    assert german['matched'] is False and 'A1' in german['evidence'] and 'B2' in german['evidence']
    # per-CV order preference isolation
    page.evaluate("""() => {
      const a=currentCV(); a.preferences=Object.assign({},prefsFromState(),{sectionOrder:['education','experience']});
      const b={...JSON.parse(JSON.stringify(a)),id:'cv_b',name:'B',preferences:Object.assign({},a.preferences,{sectionOrder:['experience','education']})};
      workspace.cvs=[a,b]; workspace.currentCVId=a.id; loadCVIntoState(a);
    }""")
    assert page.evaluate("AI_PREFS.sectionOrder.join(',')")=='education,experience'
    page.evaluate("loadCVIntoState(workspace.cvs[1])")
    assert page.evaluate("AI_PREFS.sectionOrder.join(',')")=='experience,education'
    if axe_available:
        page.evaluate("state.template='corporate'; renderResume();")
        assert_axe_clean(page, 'main editor')
    # modal accessibility + keyboard close
    page.evaluate("openModal('ovl-cvs')")
    assert page.locator('#ovl-cvs .modal').get_attribute('role') == 'dialog'
    assert page.locator('#ovl-cvs .modal').get_attribute('aria-modal') == 'true'
    page.wait_for_timeout(60)
    assert page.evaluate("document.querySelector('#ovl-cvs').contains(document.activeElement)")
    if axe_available:
        assert_axe_clean(page, 'CV library dialog')
    page.keyboard.press('Escape')
    page.wait_for_timeout(20)
    assert page.locator('#ovl-cvs').evaluate("e => e.classList.contains('hidden')")
    # narrow mobile viewport remains operable and does not create runaway horizontal overflow
    page.set_viewport_size({'width':390,'height':844})
    page.evaluate("window.scrollTo(0,0)")
    overflow=page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 6, f'mobile horizontal overflow: {overflow}px'
    assert page.locator('#p-name').is_visible()
    page.set_viewport_size({'width':1440,'height':1000})

    # DOCX bytes fixture
    page.evaluate("d => {state.data=rfNormalizeData(d); state.template='corporate'; AI_PREFS.pageBreak='education'; AI_PREFS.sectionOrder=['summary','experience','education','projects','skills','tools','languages','certificates','achievements','hobbies','volunteering','publications','coursework','references']; renderResume();}", FIXTURE)
    data=page.evaluate("Array.from(__rfBuildDocxBytes())")
    (OUT/'resume.docx').write_bytes(bytes(data))
    # PDF via Chromium print from the same rendered canonical template
    page.emulate_media(media='print')
    page.pdf(path=str(OUT/'resume.pdf'), format='A4', print_background=True, prefer_css_page_size=True)
    browser.close()

# OOXML package assertions
with zipfile.ZipFile(OUT/'resume.docx') as z:
    names=set(z.namelist())
    assert {'word/document.xml','word/numbering.xml','word/_rels/document.xml.rels'} <= names
    doc=z.read('word/document.xml').decode('utf-8')
    rel=z.read('word/_rels/document.xml.rels').decode('utf-8')
    num=z.read('word/numbering.xml').decode('utf-8')
    for text in ['Café — résumé','Straße','Zürich','জুবায়ের আহমেদ','UNIQUE-CUSTOM','UNIQUE-REFERENCE']:
        assert text in doc, text
    assert '<w:numPr>' in doc and 'w:numId w:val="1"' in doc
    assert '<w:pageBreakBefore/>' in doc
    assert 'TargetMode="External"' in rel and 'https://example.com/project' in rel
    assert '<w:numFmt w:val="bullet"' in num

# External validators available in release environment
subprocess.run(['pdfinfo', str(OUT/'resume.pdf')], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
text=subprocess.run(['pdftotext', str(OUT/'resume.pdf'), '-'], check=True, stdout=subprocess.PIPE).stdout.decode('utf-8','replace')
for token in ['Café','résumé','Straße','Zürich','UNICODE-PROJECT','UNIQUE-CUSTOM']:
    assert token in text, f'PDF missing {token!r}: {text[:500]!r}'
# Bengali extraction depends on system fallback font; require no mojibake replacement in source-derived Latin fixture.
assert '???' not in text
print('PASS: browser workflows, all templates, hostile input, CEFR matching, DOCX, PDF')
