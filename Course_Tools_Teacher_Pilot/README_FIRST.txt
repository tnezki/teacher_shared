COURSE TOOLS TEACHER PILOT — NOVEMBER 2026
=========================================
PURPOSE
A portable, local-only demonstration of working Lesson Builder + Assessment
Builder for teachers starting new courses next week. It does not change the
installed CPM Tools Algebra 1 application and does not use any Portfolio data.

START ON MAC
1. Keep this folder together. Double-click "Start Course Tools Pilot.command".
   A Terminal window opens and automatically launches the local browser index.
   If macOS blocks opening a downloaded launcher, use right-click > Open.
2. If the launcher reports missing Python 3, ask IT to provide Python 3.
3. The address starts with http://127.0.0.1: and cannot be opened from another
   device. Keep the Terminal window open while using the app.

TEACHER WORKFLOW
1. INDEX: Select your course, then Lesson Builder or Assessment Builder.
2. SOURCE: Browse a lesson, check source cards/questions, Add selected.
   Choose "Write new card" to add original content; upload optional figures.
3. ASSEMBLE: Reorder, remove, edit prompts and private answers, adjust figure
   size and student workspace. Both builders use the same shared controls.
4. PREVIEW: Switch Student/Teacher and check the content and printed layout.
5. SAVE HTML + PDF: Saves an editable JSON, student.html, teacher.html, and,
   when Chrome/Chromium is installed, student.pdf and teacher.pdf.
   If the browser PDF engine is not installed, open saved HTML and use
   Print > Save as PDF. You can also Print / Save as PDF from live preview.
6. SAVED LIBRARY: Reopen a saved editable project.

COURSE COVERAGE / SOURCE LIMITATION
- Pilot includes a small original sample lesson and six sample questions
  for each of seven courses: CC1, CC2, CC3, Geometry, Algebra 1, Algebra 2,
  and Precalculus. THESE ARE DEMONSTRATIONS, NOT CPM TEXTBOOK CARDS OR
  TEACHER-APPROVED ASSESSMENT BANKS. Teachers MUST review questions/keys.
- Import your own authorized local "course-tools-pilot-pack/1" JSON to bring
  in real lesson cards and assessment questions. See the template in data/.
- Do not distribute proprietary textbook content or teacher answer keys
  publicly without appropriate permission.

STORAGE / PRIVACY
- Saved documents are written only inside this pilot folder's saved/ directory.
- Uploaded course packs are written only to data/teacher_course_pack.json.
- Temporary browser drafts are in local browser storage; Saved Library files
  are the authoritative, portable copies.
- No student names, rosters, grades, student data, cloud service calls, login,
  email, AI model calls, Portfolio sync, or automated grading.
- Teacher HTML/PDF files are PRIVATE. Share only student.html/student.pdf.
- The MathJax renderer is bundled locally so math notation works offline.

PILOT VS PRODUCTION CPM TOOLS
This is a separate, minimal interoperable pilot. It retains the shared card
assembly model and print controls (32% default figure, 72 pt workspace), but
it does not attempt to reproduce the full Algebra 1 bank/Portfolio system.
The current installed CPM Tools and its data are not modified.

NOTES FOR REVIEW
Test the complete workflow: write/edit a card, import a local course pack,
select questions, reorder, generate teacher key, save PDF and reopen a project.
Record any failure with the course, action, and screenshot for the next patch.

HOW TO SHARE WITH PILOT TEACHERS
The folder includes PILOT_SHARE_WITH_TEACHERS.zip. Share that ZIP privately
with teachers or copy the whole application folder. Teachers unzip and use
the launcher locally; their own saved documents are stored in their copy.
The pilot uses no district login or network account integration.
