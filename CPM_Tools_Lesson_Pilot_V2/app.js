/* CPM Tools pilot: actual course dashboard + original full-source lesson card picker.
   The only active builder in this revision is Lesson Builder. */
(()=>{'use strict';
const $=id=>document.getElementById(id), esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state={catalog:[],sourceRoot:'',course:'algebra1',chapter:1,lesson:'',source:[],selected:new Map(),items:[],kind:'lesson',teacher:false,title:'',editing:-1,mode:'home',returnFromPicker:false,busy:false};
const courseNames={cc1:'CC1',cc2:'CC2',cc3:'CC3',algebra1:'Algebra 1',geometry:'Geometry',algebra2:'Algebra 2',precalculus:'Precalculus'};
const modules=[
 ['Planner','▦','Course calendar and planning','Not included in this pilot',''],
 ['Assessment Plans','☷','Review course learning goals and assessment plans','Next phase',''],
 ['Lesson Builder','▤','Build from full CPM source cards, edit, preview, and save','Pilot ready','lesson'],
 ['Visuals & Printables','▧','Graphs, number lines, tables, and figures','Next phase',''],
 ['Assessments','☑','Practice, Quick Checks, Checkpoints, Tests, Custom','Next phase — after Lesson Builder',''],
 ['Question Banks','▥','CPM-aligned question banks for assessment assembly','Next phase',''],
 ['Mastery & Evidence','▥','Portfolio, evidence, grading, and reports','Not included in this pilot',''],
 ['Launches & More','◇','Launches, explores, and activity strategies','Next phase',''],
 ['Library','▣','Open previously saved lessons and teacher guides','Pilot ready','saved'],
 ['Course Setup','⚙','Connect your local licensed textbook mirror','Pilot ready','setup']
];
const cardTypes={'intro':'Introduction','question':'Investigation problem','math-notes':'Math Notes / Methods & Meanings','reference':'Reference / Sidebar','review-preview':'Review & Preview','focus':'Learning Focus','vocabulary':'Vocabulary','example':'Example','yti':'You Try It','launch':'Launch','teacher-directions':'Teacher directions','other':'Custom card'};
const newUid=()=>`teacher-${Date.now()}-${Math.random().toString(36).slice(2,9)}`;
const clone=x=>JSON.parse(JSON.stringify(x));
const course=()=>state.catalog.find(c=>c.id===state.course)||{id:state.course,name:courseNames[state.course],chapters:[]};
const itemsKey=()=>`cpm-pilot-v2:${state.course}:draft`;
function toast(msg,bad=false){const t=$('toast');t.textContent=msg;t.style.background=bad?'#923e40':'#163d5f';t.hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.hidden=true,6500);}
function setSave(msg,bad=false){$('saveStatus').textContent=msg;$('saveStatus').classList.toggle('error',bad)}
function page(name){state.mode=name;for(const id of ['homePage','workspacePage','builderPicker','builderAssembly','savedPage','setupPage'])$(id).hidden=(id!==name);$('topline').hidden=true;window.scrollTo(0,0);}
function courseWorkspace(){const c=course();$('courseHeading').textContent=c.name+' Workspace';$('courseCrumb').textContent=c.name;
 let available=c.chapters.filter(x=>x.ready).length;
 $('courseDescription').textContent=available?'Lesson Builder can use actual local textbook files for '+available+' of the first six chapters. Select a module below.':'This course needs a local textbook source folder before lesson cards will appear.';
 $('moduleGrid').innerHTML=modules.map(([title,glyph,description,status,action])=>`<button class="tile module" ${action?`data-module="${action}"`:'disabled'}><span class="glyph">${glyph}</span><span class="tile-main"><strong>${esc(title)}</strong><span class="descr">${esc(description)}</span><span class="tile-status">${esc(status)}</span></span><span class="chevron">${action?'›':''}</span></button>`).join('');page('workspacePage');}
function home(){const out=state.catalog.map(c=>{const ready=c.chapters.filter(ch=>ch.ready).length;const status=ready===6?`Chapters 1–6 indexed · ${c.lesson_count} lessons`:ready?`${ready} of 6 chapters found · ${c.lesson_count} lessons`:'Textbook mirror not connected';return `<button class="tile" data-course-id="${c.id}"><span class="glyph">▤</span><span class="tile-main"><strong>${esc(c.name)}</strong><span class="descr">${esc(c.description)}</span><span class="tile-status">${esc(status)}</span></span><span class="chevron">›</span></button>`;}).join('');$('courseGrid').innerHTML=out;page('homePage')}
async function api(url,opts){const r=await fetch(url,opts);let data;try{data=await r.json()}catch(_){throw Error('Server did not return expected JSON')}if(!r.ok)throw Error(data.error||`Request failed (${r.status})`);return data;}
async function refreshCatalog(){const data=await api('/api/catalog');state.catalog=data.courses;state.sourceRoot=data.source_root||'';return data;}
function storeDraft(){const d={items:state.items,title:state.title,lesson:state.lesson,chapter:state.chapter};try{localStorage.setItem(itemsKey(),JSON.stringify(d))}catch(_){} }
function loadDraft(){try{const d=JSON.parse(localStorage.getItem(itemsKey())||'null');state.items=Array.isArray(d?.items)?d.items:[];state.title=String(d?.title||'');state.chapter=Number(d?.chapter)||1;state.lesson=String(d?.lesson||'');}catch(_){state.items=[];state.title='';}}
function ensureTitle(){if(!state.title){const first=state.source.find(x=>x.lesson===state.lesson);state.title=course().name+' · Lesson '+(state.lesson||'');} }
function normCard(c){return {...clone(c),uid:newUid(),figure_width:Math.max(0,Math.min(100,Number(c.figure_width)||60)),workspace_pt:Math.max(0,Math.min(396,Number(c.workspace_pt??72))),answer:c.answer||''};}
async function picker(openedFromAssembly=false){state.returnFromPicker=openedFromAssembly;$('pickerTopCourse').textContent=course().name+' · Lesson Builder';$('sourceEyebrow').textContent=course().name.toUpperCase()+' STUDENT SOURCE LIBRARY';page('builderPicker');populateChapters();await changeChapter();}
function populateChapters(){const c=course();let selected=c.chapters.some(x=>x.number===state.chapter&&x.ready)?state.chapter:(c.chapters.find(x=>x.ready)?.number||1);state.chapter=selected;$('chapterFilter').innerHTML=c.chapters.map(ch=>`<option value="${ch.number}">${'Chapter '+ch.number} · ${ch.ready?`${ch.lessons} lessons`:'source missing'}</option>`).join('');$('chapterFilter').value=String(selected);}
async function changeChapter(){state.chapter=Number($('chapterFilter').value||state.chapter)||1;state.source=[];$('lessonFilter').innerHTML='<option>Loading lessons…</option>';$('sourceStatus').textContent='Checking original textbook folder…';renderSource();try{const data=await api('/api/lessons?course='+state.course+'&chapter='+state.chapter);const choices=data.lessons||[];$('lessonFilter').innerHTML=choices.map(row=>`<option value="${esc(row.id)}">Lesson ${esc(row.id)}</option>`).join('');if(choices.length){state.lesson=choices.some(x=>x.id===state.lesson)?state.lesson:choices[0].id;$('lessonFilter').value=state.lesson;await changeLesson();}else{state.lesson='';$('sourceTitle').textContent='No source lessons found';$('sourceStatus').textContent=data.ready?'The chapter exists but no matching student lesson HTML files were found.':'Chapter source folder missing. Open Course Setup to connect your mirrored textbooks.';renderSource();}}catch(e){$('sourceStatus').textContent=e.message;renderSource();}}
async function changeLesson(){state.lesson=$('lessonFilter').value;$('sourceStatus').textContent='Reading original lesson cards…';$('sourceTitle').textContent='Lesson '+state.lesson;state.source=[];renderSource();if(!state.lesson)return;try{const data=await api('/api/cards?course='+state.course+'&chapter='+state.chapter+'&lesson='+encodeURIComponent(state.lesson));state.source=data.cards||[];$('sourceTitle').textContent='Lesson '+state.lesson+' — '+data.title;$('sourceStatus').textContent=state.source.length+' original source cards from '+data.file+'.';renderSource();}catch(e){$('sourceStatus').textContent=e.message;renderSource();toast(e.message,true)}}
function visibleCards(){const q=$('sourceSearch').value.trim().toLowerCase(),t=$('cardTypeFilter').value;return state.source.filter(x=>(t==='all'||x.type===t)&&(!q||[x.title,x.problem_number,x.source,x.body.replace(/<[^>]+>/g,' ')].join(' ').toLowerCase().includes(q)));}
function renderSource(){const shown=visibleCards();const n=state.source.length;$('sourceSummary').textContent=n?`${n} complete cards in this lesson; choose any combination. Original order is preserved on selection.`:'Choose a source lesson. No sample or invented cards are shown.';$('cardCount').textContent=n+' cards';$('selectionBadge').textContent=state.selected.size+' selected';$('sourceCards').innerHTML=shown.length?shown.map(c=>{
 const isSelected=state.selected.has(c.id);const plain=c.body.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ');return `<article class="source-card ${isSelected?'selected':''}" data-source-id="${esc(c.id)}"><div class="source-head"><input type="checkbox" id="pick-${esc(c.id)}" data-pick="${esc(c.id)}" ${isSelected?'checked':''}><label for="pick-${esc(c.id)}"><strong>${esc(c.title)}</strong><small>${esc(cardTypes[c.type]||c.type)} · CPM ${esc(c.lesson)}</small></label></div><div class="source-body" data-preview="${esc(c.id)}">${c.body}</div><button type="button" class="more" data-expand="${esc(c.id)}">Show full card ↓</button><div class="small-note">${esc(c.source)}</div></article>`}).join(''):'<p>There are no cards matching this filter or this lesson has not been loaded.</p>';
 typeset($('sourceCards'));}
let mathTicket=0;
function typeset(node){const ticket=++mathTicket;const work=()=>{if(ticket!==mathTicket||!node.isConnected)return;if(window.MathJax?.typesetPromise){try{window.MathJax.typesetClear?.([node]);window.MathJax.typesetPromise([node]).catch(()=>{});}catch(_){}}};if(window.MathJax?.startup?.promise){window.MathJax.startup.promise.then(work).catch(()=>{});}else setTimeout(work,40)}
function choose(cards){for(const c of cards)state.selected.set(c.id,clone(c));renderSource();toast(cards.length+' source cards selected.')}
function buildAssembly(){if(state.selected.size){const used=new Set(state.items.map(x=>x.id));for(const c of state.selected.values())if(!used.has(c.id))state.items.push(normCard(c));state.selected.clear();}if(!state.items.length){toast('Select source cards or create a custom card first.',true);return;}ensureTitle();state.teacher=false;showAssembly();storeDraft();}
function showAssembly(){page('builderAssembly');$('assemblyTopCourse').textContent=course().name+' · Lesson Builder';$('lessonTitle').value=state.title||course().name+' Lesson';$('studentMode').classList.toggle('active',!state.teacher);$('teacherMode').classList.toggle('active',state.teacher);renderAssembly();renderPreview()}
function renderAssembly(){const target=$('assemblyCards');target.innerHTML=state.items.length?state.items.map((card,i)=>`<div class="assembly-card" data-index="${i}"><div class="assembly-title"><small>${String(i+1).padStart(2,'0')}</small><span>${esc(card.title)}</span></div><div class="assembly-ops"><button title="Move up" data-up="${i}" ${i===0?'disabled':''}>↑</button><button title="Move down" data-down="${i}" ${i===state.items.length-1?'disabled':''}>↓</button><button title="Edit source card copy" data-edit="${i}">✎ Edit</button><button title="Remove" data-remove="${i}">×</button></div><label>Figure width · ${card.figure_width??60}%<input type="range" min="0" max="100" data-figure="${i}" value="${card.figure_width??60}"></label><label>Workspace · ${card.workspace_pt??72} pt<input type="range" min="0" max="396" step="12" data-workspace="${i}" value="${card.workspace_pt??72}"></label></div>`).join(''):'<p>Select source cards to assemble a lesson.</p>';}
function renderPreview(){const paper=$('paper'),title=$('lessonTitle').value.trim()||state.title||course().name+' Lesson';const main=`<header class="paper-header"><h1>${esc(title)}</h1><div class="section">${state.teacher?'TEACHER GUIDE':'STUDENT LESSON'}</div><p class="paper-name">Name: _______________________________________ Date: _______________</p></header>`;
 const rows=state.items.filter(c=>state.teacher||c.type!=='teacher-directions').map((c,i)=>{let answer=state.teacher&&c.answer?`<div class="answer"><b>Teacher answer / notes</b><div>${c.answer.replace(/\n/g,'<br>')}</div></div>`:'';const ws=!state.teacher&&!['intro','focus','vocabulary','math-notes','reference','teacher-directions'].includes(c.type)&&Number(c.workspace_pt)>0?`<div class="workspace" style="height:${Math.min(396,Number(c.workspace_pt))}pt"></div>`:'';
 return `<article class="paper-card" style="--figure:${Number(c.figure_width??60)}%"><div class="paper-card-heading">${esc(c.title)}<small>${esc(cardTypes[c.type]||c.type)}</small></div><div class="paper-body">${c.body||'<p>________________________</p>'}</div>${answer}${ws}</article>`}).join('');paper.innerHTML=main+rows+'<div class="paper-footer">CPM Tools · Lesson Builder Pilot · '+esc(course().name)+'</div>';typeset(paper)}
function openEditor(i=-1,template=null){state.editing=i;const obj=i>=0?state.items[i]:template||{type:'other',title:'New card',body:'<p>Write your directions here.</p>',answer:'',lesson:state.lesson};$('editTitle').textContent=i>=0?'Edit assembled card':'Add custom lesson card';$('editHeading').value=obj.title||'';$('editType').value=cardTypes[obj.type]?obj.type:'other';$('editContent').innerHTML=obj.body||'<p></p>';$('editSolution').value=obj.answer||'';$('cardEditor').hidden=false;}
function closeEditor(){$('cardEditor').hidden=true;state.editing=-1;}
function applyEditor(){const idx=state.editing,old=idx>=0?state.items[idx]:{},obj={...old,id:old.id||newUid(),uid:old.uid||newUid(),type:$('editType').value,title:$('editHeading').value.trim()||'Untitled card',body:$('editContent').innerHTML,answer:$('editSolution').value,lesson:old.lesson||state.lesson,workspace_pt:old.workspace_pt??72,figure_width:old.figure_width??60,source:old.source||'Teacher-authored'};if(idx>=0)state.items[idx]=obj;else state.items.push(obj);closeEditor();renderAssembly();renderPreview();storeDraft();toast(idx>=0?'Edited assembled card. Source remains unchanged.':'Custom card added.')}
function addExamplePair(){const pair=newUid();state.items.push({id:pair+'-example',uid:newUid(),title:'Example',type:'example',lesson:state.lesson,pair_id:pair,body:'<p>Show and explain the example.</p>',answer:'',workspace_pt:100,figure_width:60,source:'Teacher-authored'}, {id:pair+'-yti',uid:newUid(),title:'You Try It',type:'yti',lesson:state.lesson,pair_id:pair,body:'<p>Complete a matching problem with new values.</p>',answer:'',workspace_pt:100,figure_width:60,source:'Teacher-authored'});renderAssembly();renderPreview();storeDraft();toast('Example and matching You Try It added.')}
function download(obj,name){const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),uri=URL.createObjectURL(blob),a=document.createElement('a');a.href=uri;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(uri),3000)}
function doc(){return {schema:'cpm-lesson-pilot-project/2',kind:'lesson',course:state.course,course_name:course().name,title:$('lessonTitle').value.trim()||state.title,items:clone(state.items)}}
function showSavedFiles(files){
 const rows=Object.entries(files||{});
 $('saveLinks').hidden=!rows.length;
 $('saveLinks').innerHTML=rows.map(([name,url])=>`<a target="_blank" rel="noopener" href="${esc(url)}">${esc(name)}</a>`).join('');
}
async function checkPdfJob(id){
 for(let i=0;i<24;i++){
  await new Promise(resolve=>setTimeout(resolve,i===0?500:2000));
  if(!$('builderAssembly') || $('builderAssembly').hidden)return;
  try{
   const result=await api('/api/save-status?id='+encodeURIComponent(id));
   showSavedFiles(result.files);
   if(result.state==='finished'){
    const warnings=result.warnings||[];
    if(warnings.length)setSave('Editable lesson and HTML saved. '+warnings.join(' '),true);
    else setSave('Editable lesson, student/teacher HTML and both PDFs saved in one folder.');
    return;
   }
   setSave('Editable lesson and HTML saved. Rendering PDFs separately; you can keep editing.');
  }catch(e){setSave('Lesson and HTML saved. PDF status check: '+e.message,true);return;}
 }
 setSave('Editable lesson and HTML saved. PDF rendering is still pending. Use Saved Lessons to check PDFs or print the self-contained HTML.');
}
async function saveLesson(){
 if(state.busy)return;
 if(!state.items.length){toast('No assembled cards',true);return;}
 state.busy=true;const b=$('saveLesson');b.disabled=true;
 b.textContent='Saving student and teacher copies…';
 setSave('Saving the editable lesson, student HTML, and teacher HTML…');
 $('saveLinks').hidden=true;
 try{
  const data=await api('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(doc())});
  showSavedFiles(data.files);
  if(data.state==='rendering'){
   setSave('Editable lesson and both HTML files saved. Rendering PDFs separately; you can keep editing.');
   if(data.id)void checkPdfJob(data.id);
  }else setSave('Saved '+Object.keys(data.files||{}).length+' files. '+(data.warnings?.join(' ')||''));
  toast('Lesson saved. Student and teacher copies share the same local folder.');
 }catch(e){setSave('SAVE FAILED: '+e.message,true);toast(e.message,true)}
 finally{b.disabled=false;b.textContent='Save lesson · HTML + PDF';state.busy=false}
}
async function savedPage(){page('savedPage');$('savedList').innerHTML='<p>Opening saved lesson library…</p>';try{const d=await api('/api/saved');$('savedList').innerHTML=d.saved.length?d.saved.map(x=>`<div class="saved-row"><div><strong>${esc(x.title)}</strong><small>${esc(courseNames[x.course]||x.course)} · ${esc(x.saved_at)}</small></div><div class="actions"><button data-reopen="${esc(x.id)}">Reopen editable</button><a href="/saved/${esc(x.id)}/student.html" target="_blank">Student HTML</a><a href="/saved/${esc(x.id)}/teacher.html" target="_blank">Teacher HTML</a>${x.student_pdf?`<a href="/saved/${esc(x.id)}/student.pdf" target="_blank">Student PDF</a>`:''}${x.teacher_pdf?`<a href="/saved/${esc(x.id)}/teacher.pdf" target="_blank">Teacher PDF</a>`:''}</div></div>`).join(''):'<p>No saved lessons yet. Build a lesson and choose Save lesson.</p>';}catch(e){$('savedList').textContent=e.message;}}
async function reopen(id){try{const doc=await api('/api/saved/'+encodeURIComponent(id));state.course=doc.course;state.items=clone(doc.items||[]);state.title=doc.title;state.chapter=Number(state.items.find(c=>/^\d/.test(c.lesson||''))?.lesson.split('.')[0])||1;state.lesson=state.items.find(c=>/^\d/.test(c.lesson||''))?.lesson||'';storeDraft();showAssembly();toast('Reopened editable lesson: '+state.title)}catch(e){toast(e.message,true)}}
function setupPage(){page('setupPage');$('sourceRoot').value=state.sourceRoot||'';$('setupCurrent').textContent=state.sourceRoot?'Current mirror: '+state.sourceRoot:'No recognized source folder found. Enter a local cpm_textbooks folder.';}
async function saveRoot(){try{const d=await api('/api/source-root',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:$('sourceRoot').value})});await refreshCatalog();$('setupMessage').textContent='Connected: '+d.source_root;toast('Textbook source ready.');}catch(e){$('setupMessage').textContent='Could not connect: '+e.message;toast(e.message,true)}}
function goBack(){if(state.items.length)showAssembly();else picker()}
function choiceHandler(e){const x=e.target.closest('[data-course-id]');if(x){state.course=x.dataset.courseId;state.selected.clear();loadDraft();courseWorkspace();}}
$('courseGrid').addEventListener('click',choiceHandler);
$('moduleGrid').addEventListener('click',e=>{const btn=e.target.closest('[data-module]');if(!btn)return;const target=btn.dataset.module;if(target==='lesson')picker();else if(target==='saved')savedPage();else if(target==='setup')setupPage();});
for(const b of document.querySelectorAll('[data-home]'))b.addEventListener('click',home);
for(const b of document.querySelectorAll('[data-course]'))b.addEventListener('click',courseWorkspace);
$('chapterFilter').addEventListener('change',changeChapter);$('lessonFilter').addEventListener('change',changeLesson);$('sourceSearch').addEventListener('input',renderSource);$('cardTypeFilter').addEventListener('change',renderSource);
$('sourceCards').addEventListener('change',e=>{const input=e.target.closest('[data-pick]');if(!input)return;const c=state.source.find(c=>c.id===input.dataset.pick);if(!c)return;if(input.checked)state.selected.set(c.id,clone(c));else state.selected.delete(c.id);$('selectionBadge').textContent=state.selected.size+' selected';const row=input.closest('.source-card');row?.classList.toggle('selected',input.checked);});
$('sourceCards').addEventListener('click',e=>{const btn=e.target.closest('[data-expand]');if(!btn)return;const body=btn.parentElement.querySelector('.source-body');body.classList.toggle('expanded');btn.textContent=body.classList.contains('expanded')?'Collapse card ↑':'Show full card ↓';});
$('selectVisible').onclick=()=>choose(visibleCards());$('selectLesson').onclick=()=>choose(state.source);$('clearSelected').onclick=()=>{state.selected.clear();renderSource()};
$('assembleBtn').onclick=buildAssembly;$('pickerConfig').onclick=setupPage;$('pickerSaved').onclick=savedPage;
$('backPicker').onclick=()=>picker(true);$('backPickerTop').onclick=()=>picker(true);$('insertSourceCards').onclick=()=>picker(true);$('assemblySaved').onclick=savedPage;
$('lessonTitle').oninput=()=>{state.title=$('lessonTitle').value;storeDraft();renderPreview()};
$('studentMode').onclick=()=>{state.teacher=false;showAssembly()};$('teacherMode').onclick=()=>{state.teacher=true;showAssembly()};
$('assemblyCards').addEventListener('click',e=>{const btn=e.target.closest('button');if(!btn)return;const d=btn.dataset,i=Number(d.up??d.down??d.edit??d.remove);if(d.up!==undefined&&i>0){[state.items[i-1],state.items[i]]=[state.items[i],state.items[i-1]];}else if(d.down!==undefined&&i<state.items.length-1){[state.items[i],state.items[i+1]]=[state.items[i+1],state.items[i]];}else if(d.edit!==undefined){openEditor(i);return;}else if(d.remove!==undefined){state.items.splice(i,1);}renderAssembly();renderPreview();storeDraft();});
$('assemblyCards').addEventListener('input',e=>{const x=e.target;if(x.dataset.workspace!==undefined)state.items[Number(x.dataset.workspace)].workspace_pt=Number(x.value);if(x.dataset.figure!==undefined)state.items[Number(x.dataset.figure)].figure_width=Number(x.value);renderPreview();storeDraft();const row=x.closest('.assembly-card');row?.querySelector('label')?.dispatchEvent(new Event('change'));});
$('globalFigure').oninput=()=>{const n=Number($('globalFigure').value);$('globalFigureVal').textContent=n+'%';state.items.forEach(c=>c.figure_width=n);renderAssembly();renderPreview();storeDraft()};
$('globalWorkspace').oninput=()=>{const n=Number($('globalWorkspace').value);$('globalWorkspaceVal').textContent=n+' pt';state.items.forEach(c=>c.workspace_pt=n);renderAssembly();renderPreview();storeDraft()};
$('clearAssembly').onclick=()=>{if(!state.items.length||confirm('Clear all assembled cards? Your source textbook will not change.')){state.items=[];renderAssembly();renderPreview();storeDraft()}};
$('addNewCard').onclick=()=>openEditor(-1);$('addExamplePair').onclick=addExamplePair;
$('printLesson').onclick=()=>window.print();$('downloadEditable').onclick=()=>download(doc(),(state.title||'lesson').replace(/[^a-z0-9_-]/gi,'-').slice(0,60)+'_editable.json');$('saveLesson').onclick=saveLesson;
$('closeEditor').onclick=closeEditor;$('editBackdrop').onclick=closeEditor;$('cancelEdit').onclick=closeEditor;$('saveEdit').onclick=applyEditor;
$('editToolbar').addEventListener('click',e=>{const b=e.target.closest('[data-command]');if(!b)return;e.preventDefault();$('editContent').focus();document.execCommand(b.dataset.command,false,null)});
$('insertTable').onclick=()=>{$('editContent').focus();document.execCommand('insertHTML',false,'<table><tbody><tr><th>x</th><th>y</th></tr><tr><td>&nbsp;</td><td>&nbsp;</td></tr><tr><td>&nbsp;</td><td>&nbsp;</td></tr></tbody></table>')};
$('savedBack').onclick=goBack;$('saveSourceRoot').onclick=saveRoot;$('setupBack').onclick=goBack;
$('savedList').addEventListener('click',e=>{const b=e.target.closest('[data-reopen]');if(b)reopen(b.dataset.reopen)});
$('editableImport').onchange=async e=>{const f=e.target.files?.[0];if(!f)return;try{const d=JSON.parse(await f.text());if(!['cpm-lesson-pilot-project/2','course-tools-pilot-project/1'].includes(d.schema)||d.kind!=='lesson'||!Array.isArray(d.items))throw Error('Not a saved editable lesson');if(state.items.length&&!confirm('Replace the current assembled cards with the imported lesson?'))return;state.course=d.course;state.items=clone(d.items);state.title=d.title||'Imported lesson';state.chapter=Number(d.items[0]?.lesson?.split('.')[0])||1;storeDraft();showAssembly();toast('Editable lesson imported.');}catch(err){toast(err.message,true)}finally{e.target.value=''}};
window.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('cardEditor').hidden)closeEditor()});
async function start(){try{await refreshCatalog();state.course='algebra1';loadDraft();home();}catch(e){$('courseGrid').innerHTML='<p>Could not start the source catalog. Use the local Start command. '+esc(e.message)+'</p>';toast(e.message,true)}}start();
})();
