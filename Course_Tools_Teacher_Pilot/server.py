#!/usr/bin/env python3
"""Local-only Course Tools Pilot: safe editable save + PDF generation.
Standard library except an optional installed Chrome/Chromium for PDFs.
Binds only 127.0.0.1; no remote/school/student services.
"""
from __future__ import annotations
import argparse, html, json, os, re, shutil, subprocess, sys, threading, time, uuid, webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT=Path(__file__).resolve().parent
SAVED=ROOT/'saved'
BASE=ROOT/'data'/'sample_course_pack.json'
LOCAL=ROOT/'data'/'teacher_course_pack.json'
MAX_BYTES=18*1024*1024
SLUG=re.compile(r'^[a-zA-Z0-9_-]{1,65}$')


def jdump(v):return json.dumps(v,ensure_ascii=False,indent=2)
def as_text(v,limit=30000):return str(v if v is not None else '')[:limit]
def clean_id(v):return re.sub(r'[^a-z0-9_-]+','-',str(v).lower()).strip('-')[:48] or 'untitled'
def esc(v):return html.escape(as_text(v),quote=True)
def content(v):return esc(v).replace('\n','<br>')
def n_int(v,default=72,lo=0,hi=396):
    try:return max(lo,min(hi,int(v)))
    except:return default


def safe_image(src):
    src=as_text(src,2_500_000)
    if re.match(r'^data:image/(png|jpeg|gif|webp|svg\+xml);base64,[a-zA-Z0-9+/=\s]{4,}$',src):return src
    return ''


def document_html(doc,teacher=False):
    mode=doc['kind']; course=esc(doc['course_name']); title=esc(doc['title']); entries=doc['items']
    blocks=[]
    for i,entry in enumerate(entries,1):
        kind=esc(entry.get('type','notes'))
        heading=esc(entry.get('title') or f'Question {i}')
        body=content(entry.get('body',''))
        choices=entry.get('choices') or []
        choices_markup=''
        if choices and entry.get('type')=='mc':
            choices_markup='<ol type="A" class="options">'+''.join(f'<li>{content(opt)}</li>' for opt in choices[:6])+'</ol>'
        image_src=safe_image(entry.get('image',''))
        image_markup=(f'<img src="{esc(image_src)}" alt="{esc(entry.get("image_alt") or "Question illustration")}" style="max-width:{n_int(entry.get("figure_width"),32,10,100)}%;">' if image_src else '')
        answer=as_text(entry.get('answer',''),30000)
        # Student example is deliberately blank for teacher modeling.
        solution_markup=('<div class="solution"><strong>Teacher answer / model:</strong> '+content(answer or 'Answer not supplied: teacher review required.')+'</div>') if teacher else ''
        workspace=n_int(entry.get('workspace_pt'),72,0,396)
        pad=f'<div class="workspace" style="height:{workspace}pt"></div>' if (workspace and not teacher) else ''
        ican=f'<div class="can">{esc(entry.get("ican",""))}</div>' if entry.get('ican') else ''
        blocks.append(f'<article class="item"><div class="item-head"><span>{i:02d} &nbsp; {heading}</span><span class="kind">{kind.replace("-"," ").upper()}</span></div>{ican}<div class="prompt">{body}</div>{image_markup}{choices_markup}{solution_markup}{pad}</article>')
    foot_note=('TEACHER COPY • DO NOT SHARE AS STUDENT HANDOUT' if teacher else 'STUDENT COPY')
    vendor=(ROOT/'vendor'/'tex-mml-svg.js').read_text(encoding='utf-8')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title} — {foot_note}</title>
<style>
@page {{size:Letter;margin:.52in .55in .57in}}
*{{box-sizing:border-box}}body{{font:12pt/1.35 Arial,Helvetica,sans-serif;color:#172b40;background:#fff;margin:0}}
.container{{max-width:8.5in;margin:auto;padding:.30in .48in}}.banner{{border-bottom:3px solid #2e587e;padding-bottom:12px;margin-bottom:17px}}
.kicker{{font-size:9pt;font-weight:800;color:#365c82;letter-spacing:.09em;text-transform:uppercase;margin-bottom:4px}}
h1{{font-size:21pt;line-height:1.14;margin:0;color:#193f66}}.subtitle{{font-size:10pt;color:#637184;margin-top:5px}}
.name{{font-size:10pt;margin:11px 0 8px}}.item{{border:1px solid #c9d5df;border-radius:7px;margin:0 0 15pt;padding:12pt 13pt;break-inside:avoid;page-break-inside:avoid;overflow:hidden;background:#fff}}
.item-head{{display:flex;justify-content:space-between;align-items:baseline;gap:14px;font-weight:800;color:#173f65;font-size:13.3pt;margin-bottom:8px}}
.kind{{font:800 8pt Arial,sans-serif;color:#59748c;letter-spacing:.04em;white-space:nowrap}}.prompt{{margin:8px 0 8px;line-height:1.42;white-space:normal}}
.can{{font-size:9pt;color:#587289;margin:6px 0}}.item img{{height:auto;display:block;margin:10px auto;max-height:3in}}
.options{{padding-left:22pt;margin-top:8pt;list-style-type:upper-alpha}}.options li{{padding:3pt 0}}.workspace{{margin-top:11px;border-bottom:1px solid #e0e6eb;background:repeating-linear-gradient(to bottom,#fff 0,#fff 25pt,#e4e9ee 26pt);}}
.solution{{border-left:3px solid #7798b3;background:#f3f7fa;padding:8px 11px;margin:9px 0;color:#1f3a54;font-size:10.5pt;line-height:1.45}}
.footer{{font-size:8pt;color:#70808d;padding-top:9px;border-top:1px solid #d8e2e9;margin-top:20px}}
@media screen{{body{{background:#dfe7ed}}.container{{background:#fff;min-height:11in;box-shadow:0 4px 15px #1f354226;margin:20px auto}}}}
@media print{{body{{background:#fff}}.container{{padding:0;max-width:none;box-shadow:none;margin:0}}.item{{break-inside:avoid}}.solution{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}}}
</style>
<script>window.MathJax={{tex:{{inlineMath:[['\\\\(','\\\\)'],['$','$']],displayMath:[['\\\\[','\\\\]']],processEscapes:true}},svg:{{fontCache:'none'}},startup:{{typeset:true}}}};</script>
<script>{vendor}</script></head><body><main class="container"><header class="banner"><div class="kicker">{course} · {esc(mode.replace('-',' '))} · {esc(doc.get('assessment_type',''))}</div><h1>{title}</h1><div class="subtitle">{foot_note}</div><div class="name">Name: _______________________________________ &nbsp; Date: ________________</div></header>
{''.join(blocks)}<footer class="footer">Course Tools Pilot · Local teacher copy · {foot_note}</footer></main></body></html>'''


def locate_chrome():
    for name in ('chromium','chromium-browser','google-chrome','google-chrome-stable','chrome'):
        found=shutil.which(name)
        if found:return found
    for path in ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                 '/Applications/Chromium.app/Contents/MacOS/Chromium',
                 str(Path.home()/'Applications/Google Chrome.app/Contents/MacOS/Google Chrome')):
        if Path(path).is_file():return path
    return None


def render_pdf(src,dest):
    # Prefer local HTML/CSS renderer when available; otherwise use installed Chrome.
    # No PDF renderer is required to retain the editable project + HTML files.
    try:
        from weasyprint import HTML
        HTML(filename=str(src)).write_pdf(str(dest))
        if dest.is_file() and dest.stat().st_size>1500:return ''
    except ImportError:pass
    except Exception as exc:
        # A malformed SVG/HTML should never block the save of the editable source.
        pass
    chrome=locate_chrome()
    if not chrome:return 'Automatic PDF engine not installed; open saved HTML and Print > Save as PDF.'
    cmd=[chrome,'--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
         '--disable-background-networking','--no-pdf-header-footer','--virtual-time-budget=3000',
         '--print-to-pdf='+str(dest),str(src.resolve().as_uri())]
    if sys.platform.startswith('linux'):cmd.insert(1,'--no-sandbox');cmd.insert(2,'--disable-dev-shm-usage')
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=14)
        if dest.is_file() and dest.stat().st_size>1500:return ''
        return 'Chrome could not export a PDF. Use Print > Save as PDF from saved HTML.'
    except subprocess.TimeoutExpired:
        return 'Chrome PDF export timed out. Editable HTML/JSON were saved; use Print > Save as PDF.'
    except Exception:
        return 'Automatic PDF export unavailable; use Print > Save as PDF from saved HTML.'


def validate_doc(obj):
    if not isinstance(obj,dict) or obj.get('kind') not in ('lesson','assessment'):raise ValueError('Unknown artifact type')
    items=obj.get('items')
    if not isinstance(items,list) or not 1<=len(items)<=70:raise ValueError('Choose 1-70 cards before saving')
    valid_types={'focus','notes','vocabulary','example','you-try','launch','review','question','mc','frq','activity'}
    cleaned=[]
    for item in items:
        if not isinstance(item,dict):continue
        t=item.get('type','question')
        if t not in valid_types:t='question'
        cleaned.append({'id':as_text(item.get('id'),90),'type':t,'title':as_text(item.get('title'),250),'body':as_text(item.get('body'),30000),'answer':as_text(item.get('answer'),30000),'choices':[as_text(x,1500) for x in (item.get('choices') or [])[:6]],'ican':as_text(item.get('ican'),250),'lesson':as_text(item.get('lesson'),80),'workspace_pt':n_int(item.get('workspace_pt'),72),'figure_width':n_int(item.get('figure_width'),32,10,100),'image':safe_image(item.get('image')),'image_alt':as_text(item.get('image_alt'),250)})
    if not cleaned:raise ValueError('No valid cards in assembly')
    return {'schema':'course-tools-pilot-project/1','kind':obj['kind'],'course':as_text(obj.get('course'),80),'course_name':as_text(obj.get('course_name'),150),'title':as_text(obj.get('title'),180) or 'Untitled','assessment_type':as_text(obj.get('assessment_type'),60),'items':cleaned,'saved_at':time.strftime('%Y-%m-%d %H:%M:%S')}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def log_message(self,fmt,*a):print('Pilot:',fmt%a)
    def send_json(self,data,status=200):
        b=jdump(data).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        p=urlparse(self.path).path
        if p=='/api/pack':
            try:self.send_json(json.loads((LOCAL if LOCAL.exists() else BASE).read_text(encoding='utf-8')))
            except Exception as e:self.send_json({'error':str(e)},500)
            return
        if p=='/api/saved':
            docs=[]
            for f in sorted(SAVED.glob('*/editable.json'),key=lambda x:x.stat().st_mtime,reverse=True):
                try:
                    d=json.loads(f.read_text(encoding='utf-8'))
                    docs.append({'id':f.parent.name,'title':d.get('title',''),'kind':d.get('kind',''),'course':d.get('course_name',''),'saved_at':d.get('saved_at',''),'pdf_student':(f.parent/'student.pdf').exists(),'pdf_teacher':(f.parent/'teacher.pdf').exists()})
                except:pass
            self.send_json({'saved':docs});return
        m=re.fullmatch(r'/api/saved/([A-Za-z0-9_-]{1,65})',p)
        if m:
            file=SAVED/m.group(1)/'editable.json'
            if not file.is_file():self.send_json({'error':'Project not found'},404);return
            self.send_json(json.loads(file.read_text(encoding='utf-8')));return
        if p.startswith('/saved/'):
            # Static serving is restricted to actual safe paths by SimpleHTTPRequestHandler.
            return super().do_GET()
        return super().do_GET()
    def read_body(self):
        n=int(self.headers.get('Content-Length','0'))
        if n<1 or n>MAX_BYTES:raise ValueError('Request too large or empty')
        return json.loads(self.rfile.read(n).decode('utf-8'))
    def do_POST(self):
        try:
            if self.path=='/api/pack':
                pack=self.read_body()
                if pack.get('schema')!='course-tools-pilot-pack/1':raise ValueError('Invalid course-pack schema')
                for field in ('courses','cards','questions'):
                    if not isinstance(pack.get(field),list):raise ValueError('Invalid course-pack '+field)
                    if len(pack[field])>2000:raise ValueError('Pilot limit reached')
                LOCAL.parent.mkdir(parents=True,exist_ok=True)
                temp=LOCAL.with_suffix('.tmp');temp.write_text(jdump(pack),encoding='utf-8');temp.replace(LOCAL)
                self.send_json({'ok':True,'courses':len(pack['courses']),'cards':len(pack['cards']),'questions':len(pack['questions'])});return
            if self.path=='/api/save':
                doc=validate_doc(self.read_body())
                SAVED.mkdir(parents=True,exist_ok=True)
                ident=time.strftime('%Y%m%d_%H%M%S')+'_'+clean_id(doc['title'])[:22]+'_'+uuid.uuid4().hex[:6]
                folder=SAVED/ident;folder.mkdir()
                (folder/'editable.json').write_text(jdump(doc),encoding='utf-8')
                (folder/'student.html').write_text(document_html(doc,False),encoding='utf-8')
                (folder/'teacher.html').write_text(document_html(doc,True),encoding='utf-8')
                warnings=[]
                for who in ('student','teacher'):
                    warn=render_pdf(folder/(who+'.html'),folder/(who+'.pdf'))
                    if warn:warnings.append(who+': '+warn)
                self.send_json({'ok':True,'id':ident,'warnings':warnings,'files':{n:'/saved/'+ident+'/'+n for n in ('editable.json','student.html','teacher.html','student.pdf','teacher.pdf') if (folder/n).exists()}});return
            self.send_json({'error':'Unknown action'},404)
        except Exception as e:self.send_json({'error':str(e)},400)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=0);ap.add_argument('--no-browser',action='store_true');a=ap.parse_args()
    SAVED.mkdir(exist_ok=True)
    app=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
    url=f'http://127.0.0.1:{app.server_port}/index.html'
    print('\nCOURSE TOOLS TEACHER PILOT\nLocal address: '+url+'\nClose Terminal to stop the pilot. Teacher files stay in saved/.\n',flush=True)
    if not a.no_browser:threading.Timer(.5,lambda:webbrowser.open(url)).start()
    try:app.serve_forever()
    except KeyboardInterrupt:pass
    finally:app.server_close()
if __name__=='__main__':main()
