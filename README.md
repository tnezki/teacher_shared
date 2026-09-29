# Teacher Shared

This repository is the **public, unlinked, read-only co-teacher companion** for the curriculum system.

It is intentionally separate from the local Teacher Tools / Planner system.

## Hosted co-teacher agendas

The local Planners generate the teacher views, but the canonical published files live here:

- Algebra 1: `algebra/index.html`
- Physics: `physics/index.html`
- AP Calculus AB: `calc/index.html`

The hosted site is:

- `https://tnezki.github.io/teacher_shared/`
- `https://tnezki.github.io/teacher_shared/algebra/`
- `https://tnezki.github.io/teacher_shared/physics/`
- `https://tnezki.github.io/teacher_shared/calc/`

A localhost `/shared/...` route is only a teacher preview/troubleshooting surface. It is not the link supplied to the co-teacher.

## What belongs here

- Generated read-only co-teacher agendas.
- Exact teacher guides and approved shared instructional resources.
- Approved assessment links/files intended for the co-teacher.
- Teacher Library pages.
- Shared course resources that contain no student-specific data.

## What never belongs here

- Planner editing controls.
- Local Teacher Tools controls.
- Student names, grades, evidence, reports, email data, or other student information.
- Passwords, tokens, API keys, or credentials.

## Publishing workflow

1. Edit the schedule in the local Planner.
2. Use **Apply Changes + Update Agendas**.
3. The Planner updates:
   - the student agenda in the course repository;
   - the co-teacher agenda in this `teacher_shared` repository.
4. Use **Local Tools -> Commit + Push All Repos**.
5. GitHub Pages deploys the updated `teacher_shared` site.

The repository is the durable source. GitHub Pages is the hosted co-teacher view.
