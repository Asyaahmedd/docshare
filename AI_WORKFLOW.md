# AI Workflow Note

## Tools used

I used Claude (claude.ai) as a development assistant during the assessment. I used it to help plan the project structure, work through implementation tasks, generate and review code, and draft some of the documentation.

I also used Git and GitHub for version control, Vercel for deployment, and Neon for the production database.

## Where AI sped me up

- Getting the initial FastAPI application structure and database models in place.
- Building the frontend around Quill and connecting it to the backend API.
- Working through implementation details for document sharing, permissions, and file imports.
- Helping investigate errors and understand deployment issues.
- Reviewing and improving the project documentation.

## What I changed or decided myself

- I kept authentication simple and used mocked users instead of implementing a full login system. This allowed me to focus on the document features and sharing permissions within the assessment time.
- I limited file imports to `.txt`, `.md`, and `.docx` rather than trying to support every file format. I also documented what is and isn't preserved when importing a Word document.
- I kept the editor as a simple single-page application using plain HTML, CSS, and JavaScript rather than introducing a frontend framework and build process.
- I decided not to implement real-time collaborative editing. The current version uses a last-save-wins approach, and I documented this limitation rather than presenting it as real-time collaboration.
- During deployment, I checked the Vercel runtime logs when the application failed to start. The logs showed that the PostgreSQL driver was missing, so I added the required Psycopg dependency and pushed the fix.

## How I verified correctness

- Ran the automated test suite using `python -m pytest`. All 5 tests passed.
- The tests cover API behavior, document access and sharing permissions, HTML sanitization, and upload validation.
- Started the application locally and checked that the frontend and API were running.
- Deployed the application to Vercel and checked that the live application loads successfully.
- Reviewed deployment logs to identify and fix the missing PostgreSQL driver.

The automated tests and manual checks helped me catch issues during development. I have documented the remaining limitations in the README rather than claiming functionality that hasn't been implemented.
