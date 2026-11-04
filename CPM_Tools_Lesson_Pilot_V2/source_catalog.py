"""Read local, teacher-licensed CPM eBook HTML. No downloads, no external connections.
Extract full source cards from a selected lesson on demand, preserving source IDs,
text, tables, TeX, and relative figures when local companion assets exist.
"""
from __future__ import annotations
import html, json, os, re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote
from functools import lru_cache

COURSES = {
 'cc1':('CC1','Core Connections 1','cc1'),
 'cc2':('CC2','Core Connections 2','cc2'),
 'cc3':('CC3','Core Connections 3','cc3_v4'),
 'algebra1':('Algebra 1','CPM Core Connections','cc_algebra'),
 'geometry':('Geometry','Geometry','cc_geometry'),
 'algebra2':('Algebra 2','Algebra 2','cc_algebra2'),
 'precalculus':('Precalculus','Precalculus','cc_precalculus')
}
LESSON_RX=re.compile(r'(\d{1,2})[.\-](\d{1,2})[.\-](\d{1,2})\.html$',re.I)
VOID={'img','br','hr','meta','input','link','source','area','param','col','embed','wbr','track'}

def source_root(root):
  root=Path(root).resolve()
  if not root.is_dir(): return None
  return root if any((root / spec[2]).is_dir() for spec in COURSES.values()) else None

def chapter_path(root,course,chapter):
  if course not in COURSES or not 1<=int(chapter)<=6:return None
  base=Path(root)/COURSES[course][2]
  if not base.is_dir():return None
  for entry in base.iterdir():
    if entry.is_dir() and re.fullmatch(r'ch0?'+str(int(chapter)),entry.name,re.I):return entry
  return None

def lessons(root,course,chapter):
  folder=chapter_path(root,course,chapter)
  if folder is None:return []
  matches={}
  for f in folder.iterdir():
    if not f.is_file() or f.suffix.lower()!='.html':continue
    if 'teacher' in f.name.lower() or 'teach_' in f.name.lower():continue
    match=LESSON_RX.search(f.name)
    if not match or int(match[1])!=int(chapter):continue
    lid='.'.join(str(int(i)) for i in match.groups())
    # Prefer the larger complete eBook capture if a lesson has duplicate aliases.
    if lid not in matches or f.stat().st_size > matches[lid].stat().st_size:
      matches[lid]=f
  return [{'id':k,'label':'Lesson '+k,'file':v.name,'path':str(v)} for k,v in sorted(matches.items(),key=lambda x:tuple(map(int,x[0].split('.'))))]

def course_catalog(root):
  output=[]
  for id,(label,desc,folder) in COURSES.items():
    chapters=[]
    for ch in range(1,7):
      path=chapter_path(root,id,ch) if root else None
      chapters.append({'number':ch,'ready':bool(path),'lessons':len(lessons(root,id,ch)) if path else 0})
    output.append({'id':id,'name':label,'description':desc,'chapters':chapters,'lesson_count':sum(c['lessons'] for c in chapters)})
  return output

def strip_tags(text):
  text=re.sub(r'<[^>]+>',' ',text)
  return ' '.join(html.unescape(text).split())

def lesson_title(document,lesson_id):
  m=re.search(r'<header\b[^>]*class=["\'][^"\']*lessonTitle[^"\']*["\'][^>]*>.*?<h1[^>]*>(.*?)</h1>',document,re.I|re.S)
  if m:
    value=strip_tags(m.group(1));value=re.sub(r'^'+re.escape(lesson_id)+r'\s*','',value)
    return value[:220] or 'Lesson '+lesson_id
  modern=re.search(r'<h1\b[^>]*>(.*?)</h1>',document,re.I|re.S)
  if modern:
    label=strip_tags(modern.group(1))
    if label and len(label)<180:return label
  return 'Lesson '+lesson_id

class Parts(HTMLParser):
  def __init__(self):
    super().__init__(convert_charrefs=False)
    self.records=[];self.active=None;self.depth=0
  def handle_starttag(self,tag,attrs):
    d=dict(attrs)
    if self.active is None and tag=='div' and ('contentContainerReference' in d.get('class','').split() or 'sidebar' in d.get('class','').split()):
      self.active={'html':[],'attrs':d,'tag':tag};self.depth=0
    if self.active is not None:
      self.active['html'].append(self.get_starttag_text())
      if tag=='div':self.depth+=1
  def handle_startendtag(self,tag,attrs):
    if self.active is not None:self.active['html'].append(self.get_starttag_text())
  def handle_endtag(self,tag):
    if self.active is not None:
      self.active['html'].append('</'+tag+'>')
      if tag=='div':
        self.depth-=1
        if self.depth==0:
          self.records.append(self.active);self.active=None
  def handle_data(self,data):
    if self.active is not None:self.active['html'].append(data)
  def handle_entityref(self,name):
    if self.active is not None:self.active['html'].append('&'+name+';')
  def handle_charref(self,name):
    if self.active is not None:self.active['html'].append('&#'+name+';')
  def handle_comment(self,data):
    pass

def clean_fragment(raw,course,chapter):
  # Source math uses SVG references to the eBook page's symbol defs. Recreate
  # exact original TeX in a self-contained offline MathJax rendering instead.
  def media(m):
    inner=m.group(1)
    src=re.search(r'<script[^>]*type=["\']math/tex[^"\']*["\'][^>]*>(.*?)</script>',inner,re.S|re.I)
    if src:
      tex=html.unescape(src.group(1)).strip()
      return '<span class="cpm-tex">\\('+html.escape(tex,quote=False)+'\\)</span>'
    return inner
  raw=re.sub(r'<c3po-media\b[^>]*>(.*?)</c3po-media>',media,raw,flags=re.S|re.I)
  raw=re.sub(r'<script\b[^>]*>.*?</script>','',raw,flags=re.S|re.I)
  raw=re.sub(r'<(?:iframe|form)\b[^>]*>.*?</(?:iframe|form)>','',raw,flags=re.S|re.I)
  raw=re.sub(r'\s+on(?:click|mouseover|load|error|change|submit)\s*=\s*(?:"[^"]*"|\'[^\']*\')','',raw,flags=re.I)
  # Textbook images are supplied by the local synced companion _files folders.
  def image_url(m):
    before,rel,after=m.group(1),html.unescape(m.group(2)),m.group(3)
    if re.match(r'^(?:https?:|data:|//)',rel,re.I):return m.group(0)
    path=rel.strip('./').replace('\\','/')
    if not path or path.startswith('/') or '..' in path.split('/'):
      return before+'""'+after
    return before+'"/api/asset?course='+quote(course)+'&chapter='+str(chapter)+'&name='+quote(path,safe='')+'"'+after
  raw=re.sub(r'(\bsrc\s*=\s*")([^"]+)(")',image_url,raw,flags=re.I)
  return raw


class ModernRows(HTMLParser):
  """Extract CPM Learning Platform V4 row containers (CC3)."""
  def __init__(self):super().__init__(convert_charrefs=False);self.rows=[];self.active=None;self.depth=0
  def handle_starttag(self,tag,attrs):
    a=dict(attrs)
    if self.active is None and tag=='div' and any('_flexHalfRow_' in x for x in a.get('class','').split()):
      self.active=[];self.depth=0
    if self.active is not None:
      self.active.append(self.get_starttag_text())
      if tag=='div':self.depth+=1
  def handle_startendtag(self,tag,attrs):
    if self.active is not None:self.active.append(self.get_starttag_text())
  def handle_endtag(self,tag):
    if self.active is not None:
      self.active.append('</'+tag+'>')
      if tag=='div':
        self.depth-=1
        if self.depth==0:self.rows.append(''.join(self.active));self.active=None
  def handle_data(self,value):
    if self.active is not None:self.active.append(value)
  def handle_entityref(self,name):
    if self.active is not None:self.active.append('&'+name+';')
  def handle_charref(self,name):
    if self.active is not None:self.active.append('&#'+name+';')

def modern_cards(document,course,chapter,lesson_id):
  rows=ModernRows();rows.feed(document)
  cards=[];current=None;intro_parts=[];seq=0;in_review=False
  def finish():
    nonlocal current
    if not current:return
    body=clean_fragment(''.join(current['parts']),course,chapter)
    # The modern capture includes display-only UI controls and fullscreen
    # styling. Keep the actual prose and diagrams, not the eBook app chrome.
    body=re.sub(r'<button\b[^>]*>.*?</button>','',body,flags=re.S|re.I)
    body=re.sub(r'<source\b[^>]*>','',body,flags=re.I)
    body=re.sub(r'\s+style\s*=\s*(?:"[^"]*"|\'[^\']*\')','',body,flags=re.I)
    body=re.sub(r'\s+contenteditable\s*=\s*(?:"[^"]*"|\'[^\']*\')','',body,flags=re.I)
    cards.append({'id':course+'-'+lesson_id+'-'+current['number'],'type':current['kind'],
       'title':'Problem '+current['number'],'lesson':lesson_id,'problem_number':current['number'],
       'body':body,'source':'CPM Learning Platform V4 / '+lesson_id+' / '+current['number'],
       'has_figure':'<img' in body,'has_math':'<math' in body})
    current=None
  for row in rows.rows:
    label=re.search(r'<h2[^>]*class=["\'][^"\']*contentContainerReference-title[^"\']*["\'][^>]*>(.*?)</h2>',row,re.I|re.S)
    tag=strip_tags(label.group(1)) if label else ''
    question=re.fullmatch(r'(\d{1,2}-\d{1,3})\.',tag)
    if question:
      finish();current={'number':question.group(1),'kind':'review-preview' if in_review else 'question','parts':[row]};seq+=1
    elif 'Closure activity' in strip_tags(row) or 'Review & Preview' in strip_tags(row):
      finish();in_review=True
    elif current is not None:
      current['parts'].append(row)
    else:
      intro_parts.append(row)
  finish()
  if intro_parts:
    intro=''.join(intro_parts)
    intro=re.sub(r'<button\b[^>]*>.*?</button>','',intro,flags=re.I|re.S)
    intro=re.sub(r'<source\b[^>]*>','',intro,flags=re.I)
    intro=re.sub(r'\s+style\s*=\s*(?:"[^"]*"|\'[^\']*\')','',intro,flags=re.I)
    intro=clean_fragment(intro,course,chapter)
    if strip_tags(intro):cards.insert(0,{'id':course+'-'+lesson_id+'-intro','type':'intro','title':'Lesson introduction', 'lesson':lesson_id,'problem_number':'','body':intro,'source':'CPM Learning Platform V4 / lesson introduction'})
  # Modern source contains a Review & Preview section with problem numbers,
  # but some chapter exports omit the marker. Keep ambiguous problems as
  # investigation cards instead of guessing a false classification.
  return cards

def extract(root,course,chapter,lesson_id):
  candidates=lessons(root,course,chapter)
  target=next((x for x in candidates if x['id']==lesson_id),None)
  if target is None: raise ValueError('Lesson does not exist in the selected chapter')
  doc=Path(target['path']).read_text(encoding='utf-8',errors='replace')
  # Only the lesson resource, excluding embedded navigation and calculator UI.
  content=re.search(r'<div\s+id=["\']contents["\']\s*>(.*?)(?:<div\s+class=["\']modal\b|</div>\s*<div\s+id=["\']page)',doc,flags=re.I|re.S)
  raw=content.group(1) if content else doc
  p=Parts();p.feed(raw)
  if not p.records and ('_flexHalfRow_' in doc or 'contentContainerReference-title_' in doc):
    return {'course':course,'chapter':int(chapter),'lesson':lesson_id,'title':lesson_title(doc,lesson_id),'file':target['file'],'cards':modern_cards(doc,course,chapter,lesson_id)}
  cards=[];seen=set();note_n=0
  # The original lesson intro is a source card, not invented teaching content.
  hdr=re.search(r'</header>\s*((?:<p\b[^>]*>.*?</p>){1,2})',raw,re.S|re.I)
  if hdr:
    intro=clean_fragment(hdr.group(1),course,chapter)
    if strip_tags(intro):
      cards.append({'id':course+'-'+lesson_id+'-intro','type':'intro','title':'Lesson introduction','problem_number':'','lesson':lesson_id,'body':intro,'source':'CPM textbook / lesson introduction','has_figure':'<img' in intro})
  for item in p.records:
    attrs=item['attrs'];markup=''.join(item['html']);ident=attrs.get('id','').strip()
    if 'sidebar' in attrs.get('class','').split():
      note_n+=1;ident=f'note-{note_n}'
      label=re.search(r'<h[1-4][^>]*>(.*?)</h[1-4]>',markup,re.I|re.S)
      heading=strip_tags(label.group(1))[:110] if label else 'Sidebar reference'
      is_math=bool(re.search(r'math notes|methods?\s+(?:and|&)\s+meanings|key concepts|definitions',heading,re.I))
      kind='math-notes' if is_math else 'reference'
      title=heading if heading else ('Math Notes / Methods & Meanings' if is_math else 'Sidebar reference')
    else:
      kind='review-preview' if ('Homework Help' in markup or 'homework-help' in markup.lower()) else 'question'
      if not ident:ident=f'item-{len(cards)+1}'
      title='Problem '+ident if ident[:1].isdigit() else ident
    if ident in seen:continue
    seen.add(ident)
    cleaned=clean_fragment(markup,course,chapter)
    cards.append({'id':course+'-'+lesson_id+'-'+ident,'type':kind,'title':title,'problem_number':ident if kind not in ('math-notes','reference') else '', 'lesson':lesson_id,'body':cleaned, 'source':f'CPM textbook / {lesson_id} / {ident}', 'has_figure':'<img' in cleaned,'has_math':'cpm-tex' in cleaned})
  return {'course':course,'chapter':int(chapter),'lesson':lesson_id,'title':lesson_title(doc,lesson_id),'file':target['file'],'cards':cards}

if __name__=='__main__':
  import sys
  root=Path(sys.argv[1]);print(json.dumps(course_catalog(root),indent=2))
