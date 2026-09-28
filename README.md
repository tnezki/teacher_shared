# Algebra 1 Shared Teacher Repository

This repository is the **read-only shared teacher companion** to the public Algebra 1 course repository.

It is intended for the course co-teacher. It is deliberately separate from the local Teacher Tools / Planner system.

## Three visibility levels

1. **Student** — safe for the public Algebra repository and Student Agenda.
2. **Teacher shared** — safe for this private repository and the co-teacher: exact teacher guides, assessment files/links, answer keys, and other shared instructional resources.
3. **Teacher local** — personal/local tools and data. These never belong in this repository.

## What this repository should contain

- A generated, read-only Teacher Agenda at `index.html`.
- The exact student-facing resources used on each day.
- Teacher-only rows showing the matching teacher guide(s), Quick Check / assessment link, Summative Assessment link, answer key, or other teacher resource actually used.
- Secure course artifacts under `resources/` as they are migrated or created.
- A small private artifact registry at `data/private_artifacts.json`.

## What this repository should never contain

- Planner editing controls or local Teacher Tools links.
- Local Planner state that exposes personal tools.
- Student names, grades, evidence, reports, email data, or other student information.
- Passwords, tokens, API keys, or credentials.

## Intended publishing workflow

The local Planner remains the source of truth. A later Planner update will publish two static views from the same saved schedule:

- Public Student Agenda -> `algebra/agenda/index.html`
- Shared Teacher View -> `algebra_teacher_shared/index.html`

You then review and push each repository with GitHub Desktop.

The shared Teacher View is static HTML so the co-teacher can clone the private repository and open `index.html` without gaining access to the Planner or local Teacher Tools.

## First-time private repository setup

1. Run `Initialize Private Repo.command` once.
2. In GitHub Desktop, use **File -> Add Local Repository** and select this folder.
3. Publish the repository to GitHub and keep it **Private**.
4. Invite the co-teacher as a collaborator with the access level you want.
5. The co-teacher can clone the private repository and double-click `Open Teacher Portal.command` or `index.html`.

Do not publish this folder through a public GitHub Pages site. The repository itself is the access boundary.
