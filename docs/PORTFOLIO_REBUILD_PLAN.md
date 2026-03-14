# Portfolio Rebuild Plan — Astro + GitHub Pages (MARS as Anchor)

> Generated: 2026-02-17
> Target executor: Copilot agent mode (GPT-5.2)
> Target outcome: Replace legacy multi-project portfolio with a modern site featuring **MARS as the only featured project** at launch, plus **About** and **Contact** — while keeping the code/content structure intentionally ready to add new projects later (drop-in Markdown entries).
> Hosting: GitHub Pages
> Repo: new repo (clean slate)
> Estimated effort: 2–4 focused sessions

---

## Table of Contents

1. [Phase 0: Decisions & Assets](#phase-0-decisions--assets)
2. [Phase 1: New Site Scaffold (Astro)](#phase-1-new-site-scaffold-astro)
3. [Phase 2: Content (MARS + About + Contact)](#phase-2-content-mars--about--contact)
4. [Phase 3: Deploy & Cutover](#phase-3-deploy--cutover)

---

## Phase 0: Decisions & Assets

**Goal:** Lock the minimum scope and gather assets so the build is fast and consistent.

### Task 0.1: Confirm Site Scope (MVP)

**Why:** Prevent scope creep. The portfolio should be simple, modern, and focused on showcasing MARS.

**Checklist:**
- [ ] Pages: Home, Project (MARS), About, Contact
- [ ] Navigation includes exactly: Home, Project, About, Contact
- [ ] Only one featured project at launch (MARS). No “All projects” section.
- [ ] Project content architecture supports easy future additions (e.g., a `projects/` content folder with one Markdown file per project)
- [ ] External links: GitHub, LinkedIn, Streamlit demo
- [ ] Confirm whether Resume is included (if not, omit entirely)

**Prompt for Copilot (GPT-5.2):**

```
We are rebuilding a data science portfolio site.

REQUIREMENTS:
- Only these pages: Home, Project (MARS), About, Contact.
- MARS is the only featured project at launch.
- The structure must support adding future projects easily (content-driven; minimal/no code changes).
- No blog, no gallery, no extra sections.
- Site should feel modern and professional.

Before coding anything:
1) Restate the final page list.
2) Confirm nav items.
3) List the external links we will include.
```

---

### Task 0.2: Collect Required Assets + Copy

**Why:** The fastest way to ship a polished site is to have assets ready (headshot, MARS screenshot, and short written copy).

**Checklist:**
- [ ] A professional headshot image (or decide to omit)
- [ ] A clean MARS screenshot (re-use `app/assets/demo_screenshot.png` or export a more “portfolio-like” shot)
- [ ] MARS links:
  - Streamlit Community Cloud demo URL
  - GitHub repo URL
- [ ] Short “elevator pitch” paragraphs:
  - 1–2 lines for the Home hero
  - 4–6 lines for About
- [ ] Contact method:
  - email address
  - optional LinkedIn

**Prompt for Copilot (GPT-5.2):**

```
Create a short content inventory checklist for a portfolio site with:
- Home hero copy
- MARS project summary copy
- About copy
- Contact copy

Keep it concise and professional.
```

---

## Phase 1: New Site Scaffold (Astro)

**Goal:** Create a clean Astro site that builds and deploys to GitHub Pages reliably.

### Task 1.1: Create New Repo + Scaffold Astro Site

**Why:** A new repo avoids legacy theme constraints and makes the cutover clean.

**Checklist:**
- [ ] Create a new repo (e.g., `daedwards06/portfolio`)
- [ ] Scaffold an Astro site (choose a simple portfolio template)
- [ ] Add a projects content structure that scales (Astro Content Collections or a simple `src/content/projects/*.md` convention)
- [ ] Ensure local dev works (`npm install`, `npm run dev`)
- [ ] Ensure a production build works (`npm run build`, `npm run preview`)

**Prompt for Copilot (GPT-5.2):**

```
I need to scaffold a new Astro portfolio site.

CONTEXT:
- This is a new repository for a personal portfolio.
- Pages: Home, Project (MARS), About, Contact.
- Content will be mostly Markdown or simple components.

REQUIREMENTS:
1) Use Astro.
2) Keep the template minimal and easy to extend.
3) Ensure adding a new project later is trivial (ideally: add one Markdown file and it auto-renders).
3) Ensure `npm run build` succeeds.

OUTPUT:
- A working Astro site scaffold with the page routes stubbed.
```

---

### Task 1.2: Configure GitHub Pages (Correct Base Path)

**Why:** GitHub Pages often serves from `/<repo>/` which breaks assets/links unless configured.

**Checklist:**
- [ ] Configure Astro `site` and `base` (or equivalent) for GitHub Pages
- [ ] Ensure assets resolve correctly in `npm run preview`
- [ ] Ensure internal links work in both dev and production

**Prompt for Copilot (GPT-5.2):**

```
I’m deploying an Astro site to GitHub Pages for a repository named `portfolio`.

REQUIREMENTS:
- Configure Astro so the built site works at https://daedwards06.github.io/portfolio/
- Ensure internal links and static assets work.
- Document the exact config changes.

Deliver:
- The `astro.config.*` changes and any necessary adjustments.
```

---

### Task 1.3: Add Basic SEO + Social Preview

**Why:** Recruiters often see your site via shared links. A clean title/description and OG image helps.

**Checklist:**
- [ ] Set global site title/description
- [ ] Add OpenGraph/Twitter metadata
- [ ] Ensure each page has an appropriate title

**Prompt for Copilot (GPT-5.2):**

```
Add basic SEO metadata to an Astro portfolio site.

REQUIREMENTS:
- A consistent default title + per-page titles.
- meta description.
- OpenGraph + Twitter card tags.
- Use a single OG image asset.

Avoid adding analytics or complex SEO tooling.
```

---

## Phase 2: Content (MARS + About + Contact)

**Goal:** Ship crisp content that highlights MARS as a serious end-to-end system.

### Task 2.1: Home Page (Single Clear Pitch)

**Why:** Home should communicate: who you are, what you do, and where to click next in 5 seconds.

**Checklist:**
- [ ] Hero: Name + short tagline
- [ ] Primary CTA: “View MARS” (links to project page)
- [ ] Secondary links: GitHub + LinkedIn
- [ ] One short “What I build” section (2–3 bullets)

**Prompt for Copilot (GPT-5.2):**

```
Implement the Home page for an Astro portfolio.

REQUIREMENTS:
- Hero: Dominique Edwards + 1–2 line DS tagline.
- One primary CTA linking to the MARS project page.
- Simple section describing strengths (2–3 bullets).
- Links to GitHub and LinkedIn.

No extra sections (no blog, no project grid).
```

---

### Task 2.2: MARS Project Page (Deep, but Scannable)

**Why:** This is the centerpiece. It should read like a clean case study.

**Checklist:**
- [ ] Above the fold: “MARS — My Anime Recommendation System” + demo link
- [ ] 3–5 bullets: what makes it technically strong
- [ ] 1 architecture diagram image OR reuse the Mermaid diagram as an embedded screenshot
- [ ] “Results” section: a small table or 3–4 metric callouts (reuse the README numbers)
- [ ] “Tech stack” list
- [ ] Links: GitHub repo, Streamlit demo, Model Card (optional)
- [ ] MARS content is sourced from the same “projects” content system that future projects will use (even if only MARS is displayed today)

**Prompt for Copilot (GPT-5.2):**

```
Create a project case-study page for MARS.

CONSTRAINTS:
- Keep it scannable: short sections, bullets, and a few key metrics.
- Use the MARS README as the source of truth for results and features.
- Include links to:
  - Streamlit demo
  - GitHub repo

AVOID:
- Adding other projects.
- Long narrative walls of text.
```

---

### Task 2.3: About Page (Updated, Professional)

**Why:** Your current About copy is strong but reads like a 2022 snapshot. Refreshing it signals active growth.

**Checklist:**
- [ ] 1–2 paragraph professional summary
- [ ] Skills/stack list (short)
- [ ] Optional: a single line on what you’re looking for (roles/industries)

**Prompt for Copilot (GPT-5.2):**

```
Write and implement an About page for Dominique Edwards.

REQUIREMENTS:
- Professional tone.
- 1–2 paragraphs summary.
- Short skills list.
- No resume download.

Do not mention outdated dates like 2022.
```

---

### Task 2.4: Contact Page (Simple)

**Why:** Reduce friction—make it easy to reach you.

**Checklist:**
- [ ] Email address
- [ ] LinkedIn link
- [ ] Optional short line: “Best way to reach me is email”

**Prompt for Copilot (GPT-5.2):**

```
Implement a Contact page.

REQUIREMENTS:
- Show email and LinkedIn.
- No contact form.
- Minimal content.
```

---

## Phase 3: Deploy & Cutover

**Goal:** Deploy reliably and retire the old site without breaking your public links.

### Task 3.1: Add GitHub Actions Deploy to GitHub Pages

**Why:** A repeatable deploy pipeline prevents “it works locally” issues.

**Checklist:**
- [ ] Add a GitHub Actions workflow to build and deploy Astro to GitHub Pages
- [ ] Confirm it deploys to `daedwards06.github.io/portfolio/`
- [ ] Ensure the deployed site loads assets and routes correctly

**Prompt for Copilot (GPT-5.2):**

```
Add a GitHub Actions workflow that deploys an Astro static site to GitHub Pages.

REQUIREMENTS:
- Trigger on push to main.
- Build step and deploy step.
- Works for repo pages at /portfolio/.

Deliver:
- Workflow file(s) and any required config updates.
```

---

### Task 3.2: Decide Cutover Strategy for the Old Site

**Why:** You currently have a public site at `daedwards06.github.io/dedwards_portfolio/`. You can keep it, redirect it, or replace it.

**Options:**
- Option A: Keep the old site as-is (least effort, but still visible)
- Option B: Add a banner link on the old site pointing to the new site
- Option C: Replace the old site entirely (requires moving new site into the old repo or changing Pages settings)

**Checklist:**
- [ ] Choose A/B/C
- [ ] If B: add a simple “New portfolio here” banner
- [ ] If C: plan the migration steps carefully (Pages settings + repo change)

**Prompt for Copilot (GPT-5.2):**

```
Help me choose a cutover strategy.

CONTEXT:
- Old site is at /dedwards_portfolio/ with older projects.
- New site will be at /portfolio/.

I want the cleanest public-facing outcome with minimal risk.
Give a short recommendation among A/B/C and the exact steps.
```

---

### Task 3.3: Final QA Pass

**Why:** Small issues (broken links, weird spacing, missing titles) are what reviewers remember.

**Checklist:**
- [ ] Check navigation on all pages
- [ ] Verify external links
- [ ] Verify mobile layout is readable
- [ ] Ensure page titles are correct
- [ ] Confirm no placeholder text remains

**Prompt for Copilot (GPT-5.2):**

```
Perform a QA checklist for the portfolio site.

REQUIREMENTS:
- Identify broken links and missing content.
- Validate page titles and navigation.
- Keep feedback as a short actionable checklist.
```
