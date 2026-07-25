# Mount a React Application Inside the Existing Static Site

## Context

The existing personal website, MktAgent, and VideoNote are implemented with vanilla HTML, CSS, and JavaScript and should remain unchanged. Diary has substantially more interconnected client state: authentication, bidirectional diary loading, calendar navigation, Entry revisions, asynchronous AI states, search filters, Agent conversations, and exact-revision citations. Implementing that state in another large page-level script would reduce locality and testability, while rewriting the entire personal website would expand the project without improving the existing pages.

## Options

1. Implement Diary with the same page-level vanilla JavaScript approach as the existing tools.
2. Rewrite the entire personal website as a React application.
3. Keep the existing static site unchanged and mount a React and TypeScript application, built with Vite, only inside the Diary page body.

## Decision

Diary uses React and TypeScript with Vite. The application mounts directly in a dedicated root inside the existing Diary static page, while the shared personal-site shell and all existing pages remain on their current vanilla implementation. The GitHub Pages deployment builds the Diary assets and publishes the existing static files unchanged.

## Consequences

- Diary can model its interconnected state as testable, focused Modules without forcing a site-wide migration.
- Existing HOME, PROJECT, JOURNEY, MktAgent, and VideoNote behavior and animation remain outside the Diary implementation scope.
- The personal website repository gains Node dependencies, a Vite configuration, and a GitHub Actions build step.
- Vite must use the GitHub Pages repository base path so generated asset URLs work under `/my-personal-website/`.
- The build workflow must preserve and publish all existing static pages and assets in addition to the Diary bundle.
- Frontend and backend remain separately deployed: GitHub Pages serves compiled browser assets, while Azure Container Apps serves FastAPI.
