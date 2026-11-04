CPM TOOLS - LESSON BUILDER PILOT V2 (November 3, 2026)
======================================================

PURPOSE
This pilot follows the familiar CPM Tools screens: seven-course dashboard,
course workspace with module tiles, separate Lesson Builder source picker,
and editable assembly/print preview. It is intentionally NOT a replacement
for the existing CPM Tools application. Assessment Builder and other modules
are not part of this revision.

START ON MAC
Double-click "Start CPM Tools Lesson Pilot.command" in this folder.
A Terminal window opens a local server and your browser opens the pilot.
Close Terminal (or Ctrl+C) to stop the pilot.

The program binds to 127.0.0.1 only, runs locally and makes no Git commits,
pushes, pulls or changes to your existing CPM Tools application.

SOURCE TEXTBOOKS -- CHAPTERS 1-6
The pilot reads lesson HTML from your already-synced, authorized local
cpm_textbooks mirror on demand. It does NOT distribute purchased textbook
copies. It automatically looks for the mirror at your GitHub root:

  ~/GitHub/cpm_textbooks/

Expected subdirectories:
  cc1/   cc2/   cc3_v4/   cc_algebra/   cc_geometry/
  cc_algebra2/   cc_precalculus/

Each course's chapter folders should be named ch01...ch06 (case-insensitive).
The local source parser accepts both 1.1.1.html and 1-1-1.html lesson names.
CPM textbook content and companion figures must be available locally;
missing figures are not fabricated. Chapters without lesson files show as
unavailable. Use Course Setup > Source setup to point to another source root.
For other teachers, provide access only to textbook content they are
individually authorized to use. The source itself is not in this software ZIP.

LESSON WORKFLOW
1. From CPM Tools, click a course. Choose Lesson Builder.
2. Pick Chapter, Lesson, card types, or search by problem number.
3. Check the cards you want, or use Whole lesson.
4. Build this lesson > Assembly. Reorder cards; edit a card's copied content;
   add custom cards, teacher notes or Example + You Try It; adjust workspace
   and figure sizes. This never alters the source textbook.
5. Preview Student / Teacher. Enter your own teacher solutions and notes.
6. Choose Save lesson. Editable JSON, student.html, and teacher.html are
   written together immediately; student.pdf and teacher.pdf are prepared
   separately. PDF links appear when the local renderer finishes.
7. If a PDF renderer is not available or times out, open the saved HTML
   in Google Chrome and choose Print > Save as PDF. The HTML is self-contained
   and includes the local MathJax renderer.
8. Open Saved Lessons to reopen editable JSON or import a colleague's
   authorized exported project. Do not publish private teacher solutions.

LIMITATIONS / NEXT PHASE
- This uses real available lesson source captures; it is not a generic demo
  question bank. Chapters 1-6 are indexed for all seven courses, and full
  selected problem content is loaded when you choose a lesson.
- Every captured problem/figure still needs gradual source and rendering QA.
  Current validation was a multi-course sample, not all textbook lessons.
- Approved Assessment Builder banks and their full first-six-chapter coverage
  will be built as the next phase; they are not falsely marked ready here.
- Other module tiles are present to match CPM Tools but not activated in this
  isolated Lesson Builder pilot.
- Local browser/Chrome compatibility is still part of teacher pilot testing.

PRIVACY AND SAVE LOCATION
Work stays in this folder:
  saved/<lesson_id>/editable.json
  saved/<lesson_id>/student.html and student.pdf (when available)
  saved/<lesson_id>/teacher.html and teacher.pdf (when available)

The local saved/ and .runtime/ folders are ignored in Git. Do not share the
entire local saved folder if it contains teacher solutions or private content.

For issues, note the course, chapter, lesson, and card/problem number, plus
what was expected. That lets us fix source extraction and printed layout
without rebuilding the user interface each time.
