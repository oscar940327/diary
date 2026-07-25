# Integrate Frontend into the Existing GitHub Pages Site

## Context

The owner already publishes a static personal website from the `personal_website` repository through GitHub Pages. Diary must appear in that site's Sidebar with the label `DIARY`, below `JOURNEY` and above `MktAgent`, while FastAPI remains separately deployed to Azure Container Apps. Embedding a separately hosted application would introduce nested scrolling, mobile-layout, navigation, and authentication-redirect problems for a diary interface built around continuous scrolling.

## Options

1. Host the frontend separately on Azure Static Web Apps and link to it from the personal website.
2. Embed a separately hosted frontend in the personal website through an iframe.
3. Add Diary as a first-class page and frontend application in the existing GitHub Pages site while keeping FastAPI on Azure.

## Decision

Diary is integrated directly into the existing `personal_website` GitHub Pages site as a first-class page. Its Sidebar entry is labeled `DIARY` and appears immediately below `JOURNEY` and above `MktAgent`. The page renders the Diary interface directly rather than through an iframe. Browser requests authenticate through Supabase Auth and call the separately deployed Azure FastAPI API with a Supabase access token.

## Consequences

- The Diary frontend deploys with the existing personal website and shares its navigation, origin, and visual shell.
- The complex interface must fit GitHub Pages static-hosting constraints; backend execution remains on Azure.
- GitHub Pages contains no backend or AI secrets. Only the Supabase publishable key and public API URL may appear in frontend configuration.
- FastAPI must enforce owner authorization independently of the public frontend and allow only explicitly configured frontend origins through CORS.
- Supabase Auth redirect URLs must include the deployed GitHub Pages page and approved local-development URLs.
- Sidebar source copies and responsive navigation sizing must be updated consistently when implementation begins.
- The personal website and Diary backend remain separately deployable and can fail independently.
