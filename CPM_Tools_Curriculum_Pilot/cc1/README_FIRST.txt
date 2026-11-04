CC1 CPM TOOLS ASSESSMENT CONTENT - CHAPTERS 1-6
November 3, 2026

PURPOSE
This is the first course-content production batch using the EXISTING
CPM Tools cpm-family-bank-plan/v1 and cpm-family-bank-manifest/v1 contracts.
No new assessment engine, user interface, renderer or question structure
has been invented.

INVENTORY
- CC1 AP1-AP6 assessment plans, one for each chapter, with 36 independent
  teacher-created exemplars each (216 questions in total).
- Four priority chapter evidence targets per chapter, with 3 reasoning,
  3 direct, and 3 spiral question families per target.
- Stable family IDs, source CPM lesson links, I Can text, answers,
  source-basis, variable-selection guidance and evidence-stage notes.
- Teacher answer field never appears in the student_html field.

COURSE ALIGNMENT
Chapter source authority is the teacher's current CC1 Chapter 01-06
Unit Plans, CC1 Assessment Evidence, and CC1 Learning Ladders on the
Google Drive mirror. Original numerical questions are NOT copied CPM text.
The chapter map keeps first checks, partial evidence and expected
proficiency separate, as specified in those sources.

PILOT POLICY
Operationally available by default: review follows usage, not before it.
'TEACHER_APPROVED' is the runtime compatibility status used under the
teacher-directed pilot baseline; it does NOT mean questions were individually
proofread by the teacher. When a question is flagged, update the canonical
family in-place while retaining its stable ID; downstream uses inherit it.

INSTALL AND INTEGRATION STATUS
This is a COURSE CONTENT packet, not a replacement application.
Transfer root is teacher_shared because the active Curriculum Transfer
contract does not establish a CPM_Tools root alias in the verified seed.
The packet is staged at:
  teacher_shared/CPM_Tools_Curriculum_Pilot/cc1/
The current installed CPM Tools active-course manifest remains Algebra 1;
these CC1 banks are not automatically active in its bank selector yet.
They use its JSON contract and can be bound after course configuration
is safely enabled through an approved-root system change.

Existing Algebra 1 AP1/AP2 are NOT modified.
No student data or textbook copies are included.
