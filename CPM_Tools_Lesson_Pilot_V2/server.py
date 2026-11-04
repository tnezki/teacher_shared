#!/usr/bin/env python3
"""CPM Tools Lesson Builder Pilot. Mac/local server, no cloud or Git actions.
Reads the owner's existing authorized cpm_textbooks mirror on demand.
"""
from __future__ import annotations
import argparse, base64, html, json, mimetypes, os, re, shutil, subprocess, sys, threading, time, uuid, webbrowser, signal
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
from source_catalog import COURSES, chapter_path, course_catalog, extract, lessons, source_root

ROOT=Path(__file__).resolve().parent
RUNTIME=ROOT/'.runtime'; SAVED=ROOT/'saved'; CONFIG=RUNTIME/'source_root.json'
MAX_BYTES=22_000_000
SAVE_JOBS={}
SAVE_LOCK=threading.Lock()
ALLOWED_TYPES={'focus','intro','vocabulary','math-notes','question','example','yti','launch','review-preview','teacher-directions','reference','other'}
ALLOWED_MEDIA={'.png','.jpg','.jpeg','.webp','.gif','.svg'}
ROOT_OVERRIDE=None

def esc(v):return html.escape(str(v or ''),quote=True)
def clamp(v,default=72,low=0,high=396):
 try:return max(low,min(high,int(float(v))))
 except (ValueError,TypeError,OverflowError):return default

def configured_root():
 if ROOT_OVERRIDE:
  return source_root(ROOT_OVERRIDE)
 try:
  source=json.loads(CONFIG.read_text(encoding='utf8')).get('source_root')
  if source and source_root(source):return source_root(source)
 except (ValueError,OSError,TypeError):pass
 probes=[ROOT.parent.parent/'cpm_textbooks',Path.home()/'GitHub'/'cpm_textbooks',Path.home()/'Documents'/'cpm_textbooks']
 probes += [p/'cpm_textbooks' for p in [ROOT.parent,ROOT.parent.parent.parent]]
 for p in probes:
  if source_root(p):return source_root(p)
 return None

def artifact_filename(path,course,chapter,name):
 folder=chapter_path(path,course,chapter)
 if not folder:raise ValueError('Chapter source folder is missing')
 if not name or len(name)>350 or '\\' in name or name.startswith('/') or '..' in Path(name).parts:
  raise ValueError('Unsafe source asset path')
 target=(folder/name).resolve()
 if folder.resolve() not in target.parents or target.suffix.lower() not in ALLOWED_MEDIA or not target.is_file():
  raise ValueError('Source figure unavailable')
 return target

def plain(v,limit):return str(v if v is not None else '')[:limit]
def sanitized_fragment(value):
 s=plain(value,170000)
 s=re.sub(r'<(?:script|iframe|object|form|embed)\b[^>]*>.*?</(?:script|iframe|object|form|embed)>','',s,flags=re.I|re.S)
 s=re.sub(r'\s+on[a-z]+\s*=\s*(?:"[^"]*"|\'[^\']*\')','',s,flags=re.I)
 s=re.sub(r'(?i)javascript\s*:','',s)
 return s

def inline_figures(content,source):
 def embed(match):
  raw=html.unescape(match.group(2));params=urlsplit(raw)
  if params.path!='/api/asset':return match.group(0)
  q=parse_qs(params.query)
  try:
   file=artifact_filename(source,(q.get('course') or [''])[0],int((q.get('chapter') or ['0'])[0]),(q.get('name') or [''])[0])
   if file.stat().st_size>3_000_000:return match.group(0)
   suffix=file.suffix.lower();media='image/svg+xml' if suffix=='.svg' else mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
   return match.group(1)+ 'data:'+media+';base64,'+base64.b64encode(file.read_bytes()).decode('ascii')+match.group(3)
  except (ValueError,OSError,TypeError):return match.group(0)
 return re.sub(r'(\bsrc\s*=\s*")([^"]+)(")',embed,content,flags=re.I)

def document_html(doc,teacher=False):
 course=esc(doc['course_name']);title=esc(doc['title']);entries=doc['items'];parts=[]
 vendor=(ROOT/'vendor'/'tex-mml-svg.js').read_text(encoding='utf8')
 sr=configured_root()
 for i,card in enumerate(entries,1):
  typ=card.get('type','question')
  if typ=='teacher-directions' and not teacher:continue
  body=sanitized_fragment(card.get('body',''))
  if sr:body=inline_figures(body,sr)
  ans=sanitized_fragment(card.get('answer',''))
  if sr:ans=inline_figures(ans,sr)
  if not body.strip():body='<p>_____________________________________</p>'
  parts.append('<section class="card"><h2>'+esc(card.get('title') or 'Card '+str(i))+'</h2>'+
               ('<div class="source-meta">'+esc(card.get('lesson',''))+' · '+esc(card.get('problem_number',''))+'</div>' if card.get('problem_number') else '')+
               '<div class="content">'+body+'</div>'+
               ('<div class="answer"><b>Teacher answer / notes</b><div>'+ans+'</div></div>' if teacher and ans else '')+
               ('<div class="write-lines" style="height:'+str(clamp(card.get('workspace_pt'),72))+'pt"></div>' if not teacher and typ not in ('teacher-directions','intro','focus','vocabulary','math-notes') and clamp(card.get('workspace_pt'),72)>0 else '')+'</section>')
 section=esc('Teacher guide' if teacher else 'Student lesson')
 return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>'''+title+''' - '''+section+'''</title><style>
@page{size:Letter;margin:.52in .58in}.sheet{font:12pt/1.45 Arial,Helvetica,sans-serif;color:#19344e}*{box-sizing:border-box}body{margin:0;background:white}h1{font:800 22pt/1.13 Arial, sans-serif;color:#173f66;margin:0 0 9pt}.header{border-bottom:3pt solid #285e8a;margin:0 0 16pt;padding:0 0 13pt}.section{font:800 13pt Arial;color:#275980;text-transform:uppercase}.name{font-size:10pt;color:#445c72;margin-top:15pt}h2{font-size:14pt;margin:0 0 8pt;color:#173e63}.card{padding:12pt 13pt;border:1pt solid #d1dee8;border-radius:8pt;margin:0 0 14pt;break-inside:avoid;page-break-inside:avoid;overflow:hidden}.content{font-size:11.5pt;line-height:1.42}.content p{margin:7pt 0}.content img{max-width:100%;max-height:3.2in;height:auto;object-fit:contain}.content .row{display:flex;gap:10pt;flex-wrap:wrap}.content .row>div{flex:1;min-width:100pt}.content table{border-collapse:collapse;font-size:10.5pt}.content th,.content td{border:1pt solid #a1b6c8;padding:4pt 6pt}.content .contentContainerReference-title{font-weight:800;color:#17416a}.content .sidebar{background:#f4f8fb;border-left:3pt solid #9bbad0;padding:8pt}.source-meta{color:#6d869b;font-size:8.5pt;margin-bottom:6pt}.answer{border-left:3pt solid #6b8fab;background:#f3f7fa;padding:8pt 10pt;font-size:10pt;margin-top:10pt}.write-lines{margin-top:10pt;border-top:1px solid #e1e8ee;border-bottom:1px solid #e1e8ee;background:repeating-linear-gradient(to bottom,#fff 0,#fff 25pt,#e2e8ed 26pt)}.foot{border-top:1px solid #d8e3ed;color:#8394a0;font-size:8pt;padding-top:6pt;margin-top:20pt}.cpm-tex{white-space:normal}.source-meta:empty{display:none}a{color:#265e87}
@media screen{body{background:#e6eef4}.sheet{margin:20px auto;width:min(100%,8.5in);padding:.56in;background:white;box-shadow:0 5px 18px #173c5922}}
@media print{.sheet{width:auto;margin:0;padding:0;box-shadow:none}.write-lines{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style><script>window.MathJax={tex:{inlineMath:[["\\(","\\)"]],displayMath:[["\\[","\\]"]]},svg:{fontCache:"none"}};</script><script>'''+vendor+'''</script></head><body><main class="sheet"><header class="header"><h1>'''+title+'''</h1><div class="section">'''+section+'''</div><div class="name">Name: ___________________________________________ &nbsp; Date: ______________</div></header>'''+''.join(parts)+'''<footer class="foot">CPM Tools · Lesson Builder · '''+section+'''</footer></main></body></html>'''

def chrome_binary():
 for n in ['chromium','chromium-browser','google-chrome','google-chrome-stable']:
  x=shutil.which(n)
  if x:return x
 for x in ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/Applications/Chromium.app/Contents/MacOS/Chromium']:
  if Path(x).is_file():return x
 return None

def make_pdf(inp,out):
 # For documents without textbook TeX, the stable HTML renderer gives a
 # high-quality letter-sized PDF without launching a heavyweight browser.
 # For TeX use Chrome (which executes our bundled offline MathJax).
 has_tex=bool(re.search(r'<span[^>]*class=[\"\']cpm-tex',inp.read_text(encoding='utf8'),re.I))
 if not has_tex:
  try:
   from weasyprint import HTML
   HTML(filename=str(inp)).write_pdf(str(out))
   if out.is_file() and out.stat().st_size>1800:return ''
  except (OSError,ImportError,ValueError,TypeError):pass
 chrome=chrome_binary()
 if chrome:
  cmd=[chrome,'--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-background-networking','--allow-file-access-from-files','--no-pdf-header-footer','--virtual-time-budget=2500','--print-to-pdf='+str(out),inp.resolve().as_uri()]
  if sys.platform.startswith('linux'):cmd.insert(1,'--no-sandbox');cmd.insert(2,'--disable-dev-shm-usage')
  try:
   # Do not capture inherited Chrome pipe descriptors: otherwise orphaned
   # renderer processes can leave a teacher's Save request hanging forever.
   proc=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
   try:proc.wait(timeout=13)
   except subprocess.TimeoutExpired:
    try:
     if hasattr(os,'killpg'):os.killpg(proc.pid,signal.SIGKILL)
     else:proc.kill()
    except OSError:pass
    try:proc.wait(timeout=2)
    except subprocess.TimeoutExpired:pass
   if out.is_file() and out.stat().st_size>1800:return ''
  except OSError:pass
 # An unrendered TeX formula would be worse than an explicit PDF warning.
 # Teacher can always print the fully typeset self-contained HTML in Chrome.
 if not has_tex:
  try:
   from weasyprint import HTML
   HTML(filename=str(inp)).write_pdf(str(out))
   if out.is_file() and out.stat().st_size>1800:return ''
  except (OSError,ImportError,ValueError,TypeError):pass
 return 'Automatic PDF export unavailable. Editable JSON and self-contained HTML are saved; open HTML in Chrome, then Print > Save as PDF.'


def render_job(ident):
 folder=SAVED/ident;messages=[]
 for copy in ('student','teacher'):
  try:
   warning=make_pdf(folder/(copy+'.html'),folder/(copy+'.pdf'))
  except Exception as e:
   warning='PDF render failed: '+str(e)[:160]
  if warning:messages.append(copy+': '+warning)
 with SAVE_LOCK:
  SAVE_JOBS[ident]={'state':'finished','warnings':messages,'files':{f:'/saved/'+ident+'/'+f for f in ['editable.json','student.html','teacher.html','student.pdf','teacher.pdf'] if (folder/f).exists()}}


def validate_doc(data):
 if data.get('kind')!='lesson' or data.get('course') not in COURSES:raise ValueError('Only the Lesson Builder is enabled in this pilot')
 cards=data.get('items')
 if not isinstance(cards,list) or not 1<=len(cards)<=120:raise ValueError('Select 1–120 lesson cards before saving')
 clean=[]
 for c in cards:
  if not isinstance(c,dict):continue
  typ=c.get('type') if c.get('type') in ALLOWED_TYPES else 'other'
  clean.append({'id':plain(c.get('id'),120),'type':typ,'title':plain(c.get('title'),250),'lesson':plain(c.get('lesson'),50),'problem_number':plain(c.get('problem_number'),50),'source':plain(c.get('source'),300),'body':sanitized_fragment(c.get('body')),'answer':sanitized_fragment(c.get('answer')),'workspace_pt':clamp(c.get('workspace_pt'),72),'figure_width':clamp(c.get('figure_width'),60,0,100)})
 if not clean:raise ValueError('No valid source cards')
 return {'schema':'cpm-lesson-pilot-project/2','kind':'lesson','course':data['course'],'course_name':COURSES[data['course']][0], 'title':plain(data.get('title') or 'Lesson',160),'items':clean,'saved_at':time.strftime('%Y-%m-%d %H:%M:%S')}

class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def log_message(self,fmt,*args):pass
 def send_json(self,obj,status=200):
  content=json.dumps(obj,ensure_ascii=False).encode('utf8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(content)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(content)
 def do_GET(self):
  url=urlsplit(self.path);path=url.path;args=parse_qs(url.query)
  try:
   if path=='/api/catalog':
    root=configured_root();return self.send_json({'source_root':str(root) if root else '', 'courses':course_catalog(root)})
   if path=='/api/lessons':
    root=configured_root();course=(args.get('course') or [''])[0];ch=int((args.get('chapter') or ['0'])[0]);return self.send_json({'lessons':[{k:v for k,v in row.items() if k!='path'} for row in lessons(root,course,ch)] if root else [],'ready':bool(root and chapter_path(root,course,ch))})
   if path=='/api/cards':
    root=configured_root()
    if not root:return self.send_json({'error':'Connect a local textbook mirror in Source setup.'},404)
    c=(args.get('course') or [''])[0];ch=int((args.get('chapter') or ['0'])[0]);lid=(args.get('lesson') or [''])[0]
    return self.send_json(extract(root,c,ch,lid))
   if path=='/api/asset':
    root=configured_root()
    if not root:return self.send_error(404)
    c=(args.get('course') or [''])[0];ch=int((args.get('chapter') or ['0'])[0]);name=(args.get('name') or [''])[0]
    file=artifact_filename(root,c,ch,name)
    if file.stat().st_size>7_000_000:return self.send_error(413)
    data=file.read_bytes();mime=mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
    self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data);return
   if path=='/api/save-status':
    ident=(args.get('id') or [''])[0]
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,75}',ident):return self.send_json({'error':'Invalid saved lesson ID'},400)
    with SAVE_LOCK:job=SAVE_JOBS.get(ident)
    if not job:return self.send_json({'error':'Save job not found'},404)
    return self.send_json(job)
   if path=='/api/saved':
    records=[]
    for item in sorted(SAVED.glob('*/editable.json'),key=lambda x:x.stat().st_mtime,reverse=True):
     try:
      d=json.loads(item.read_text(encoding='utf8'))
      records.append({'id':item.parent.name,'title':d.get('title',''),'course':d.get('course',''),'saved_at':d.get('saved_at',''),'student_pdf':(item.parent/'student.pdf').is_file(),'teacher_pdf':(item.parent/'teacher.pdf').is_file()})
     except (OSError,ValueError):pass
    return self.send_json({'saved':records})
   m=re.fullmatch(r'/api/saved/([A-Za-z0-9_-]{1,75})',path)
   if m:
    f=SAVED/m.group(1)/'editable.json'
    if not f.is_file():return self.send_json({'error':'Saved lesson not found'},404)
    return self.send_json(json.loads(f.read_text(encoding='utf8')))
   if path.startswith('/.runtime') or path.startswith('/source_catalog.py') or path.startswith('/server.py'):
    return self.send_error(404)
   if path.startswith('/saved/') or path.startswith('/vendor/') or path in ('/','/index.html','/app.css','/app.js'):
    return super().do_GET()
   return self.send_error(404)
  except (ValueError,TypeError,OSError) as e:return self.send_json({'error':str(e)},400)
 def read_payload(self):
  n=int(self.headers.get('Content-Length','0'))
  if not 1<=n<=MAX_BYTES:raise ValueError('Request is empty or too large')
  return json.loads(self.rfile.read(n).decode('utf8'))
 def do_POST(self):
  try:
   if self.path=='/api/source-root':
    d=self.read_payload();raw=d.get('path','')
    if not isinstance(raw,str) or len(raw)>900:raise ValueError('Invalid source folder')
    source=source_root(Path(raw).expanduser())
    if not source:raise ValueError('Folder must contain at least one recognized CPM course directory (cc1, cc2, cc3_v4, cc_algebra, etc.).')
    RUNTIME.mkdir(exist_ok=True);(RUNTIME/'source_root.json').write_text(json.dumps({'source_root':str(source)}),encoding='utf8');return self.send_json({'ok':True,'source_root':str(source)})
   if self.path=='/api/save':
    d=validate_doc(self.read_payload())
    SAVED.mkdir(exist_ok=True)
    ident=time.strftime('%Y%m%d_%H%M%S')+'_'+re.sub(r'[^a-z0-9-]+','-',d['title'].lower())[:26].strip('-')+'_'+uuid.uuid4().hex[:6]
    folder=SAVED/ident;folder.mkdir(parents=True)
    (folder/'editable.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    (folder/'student.html').write_text(document_html(d,False),encoding='utf8')
    (folder/'teacher.html').write_text(document_html(d,True),encoding='utf8')
    with SAVE_LOCK:
     SAVE_JOBS[ident]={'state':'rendering','warnings':[],'files':{f:'/saved/'+ident+'/'+f for f in ['editable.json','student.html','teacher.html']}}
    threading.Thread(target=render_job,args=(ident,),daemon=True).start()
    return self.send_json({'ok':True,'id':ident,'state':'rendering','warnings':[],'files':SAVE_JOBS[ident]['files']})
   return self.send_json({'error':'Unknown endpoint'},404)
  except (ValueError,TypeError,OSError) as e:return self.send_json({'error':str(e)},400)

def main():
 global ROOT_OVERRIDE
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=0);parser.add_argument('--source-root',default='');parser.add_argument('--no-browser',action='store_true');args=parser.parse_args();ROOT_OVERRIDE=args.source_root or None
 SAVED.mkdir(exist_ok=True);RUNTIME.mkdir(exist_ok=True)
 http=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);url='http://127.0.0.1:'+str(http.server_port)+'/index.html'
 print('CPM TOOLS — LESSON BUILDER PILOT\n'+url+'\nSource root: '+str(configured_root() or '(not configured)')+'\nClose Terminal to stop the pilot.',flush=True)
 if not args.no_browser:threading.Timer(.3,lambda:webbrowser.open(url)).start()
 try:http.serve_forever()
 except KeyboardInterrupt:pass
 finally:http.server_close()
if __name__=='__main__':main()
