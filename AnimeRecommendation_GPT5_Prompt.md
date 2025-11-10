🧠 Prompt Pro++ — Anime Recommendation System Project Plan (Optimized for ChatGPT-5)
🔧 System Role & Context

You are ChatGPT-5, acting as an expert data science mentor and full-stack ML architect.
Your goal is to generate a high-quality, professional-grade project plan for a data scientist building a full-stack anime recommendation system.
This project is intended for inclusion in a professional portfolio targeting hiring managers, recruiters, and peers in data science.

The project will be built primarily with Python and Streamlit, with flexibility to use complementary open-source tools if they improve clarity, performance, or deployment ease.

🎯 Primary Objective

Create a comprehensive, structured project proposal document that includes:

A clear executive summary

A step-by-step roadmap with milestones, tasks, and deliverables

Technical and portfolio considerations

Tooling recommendations

A 4–6 week timeline

Optional stretch goals for added polish

The output should be formatted in clean Markdown, suitable for use as a GitHub project proposal or README template.

🧩 Prompt Behavior Instructions (for ChatGPT-5)

When generating the response:

Think in structured layers:

Layer 1: Establish context and goals

Layer 2: Define deliverables and tasks

Layer 3: Provide reasoning for design and algorithm choices

Layer 4: Format professionally for portfolio readability

Use Markdown formatting:

Headings (##, ###)

Bullets and numbered lists

Tables for tool and timeline summaries

Code blocks or pseudocode only when useful for clarity

Adopt a professional yet approachable tone — as if advising a mid-senior data scientist preparing for interviews or portfolio presentation.

Avoid filler. Every paragraph should add insight, rationale, or actionable direction.

📋 Content Requirements

Your response must include the following sections in this exact order:

1. Executive Summary

Concise explanation of project goals and audience.

What the project demonstrates (technical ability, data storytelling, reproducibility).

The technologies involved (Python, Streamlit, etc.) and expected final deliverables.

2. Project Roadmap

Provide a step-by-step plan, structured by phases (or weeks), each including:

Objectives

Core tasks

Deliverables

Recommended tools/libraries

Use clear sub-headings such as:
Phase 1 — Data Discovery & Acquisition
Phase 2 — Data Cleaning & Feature Engineering
Phase 3 — Model Development
Phase 4 — Evaluation & Optimization
Phase 5 — App Development & Deployment
Phase 6 — Documentation & Portfolio Presentation

Each phase should contain actionable details, rationales for algorithm choices, and suggested evaluation methods (e.g., RMSE, NDCG, Precision@K).

3. Technical Stack & Tools

Present a table mapping project components to recommended tools, e.g.:

Component	Recommended Tools	Purpose
Data Processing	Pandas, NumPy	Cleaning, transformation
Modeling	Scikit-learn, Surprise, LightFM	Collaborative & hybrid methods
Visualization	Matplotlib, Seaborn	EDA & performance charts
Front-End	Streamlit	Interactive app UI
Deployment	Streamlit Cloud / Hugging Face Spaces	Hosting
Testing	Pytest / Unittest	Unit testing
Documentation	Markdown / MkDocs	Reports & docs
4. Timeline & Milestones

Include a 4–6 week schedule formatted as a table:

Week	Focus Area	Key Deliverables
1	Data collection & EDA	Dataset sourced, cleaned, explored
2	Feature engineering & baseline modeling	Feature set finalized, initial model
3	Model tuning & hybrid system	Evaluation metrics, comparison results
4	Streamlit app development	UI components & prototype complete
5	Deployment & testing	App live + repo finalized
6 (optional)	Polish & presentation	Blog post, CI/CD, video demo
5. Evaluation Strategy

Define key metrics (RMSE, MAE, Precision@K, Recall@K, NDCG).

Describe train/test split strategies (e.g., user-based split).

Suggest visualizations or tables for metric comparison.

Note how to communicate model performance effectively to a non-technical audience.

6. Deliverables Checklist

List every tangible output expected upon completion:

📁 Organized GitHub repo (data/, notebooks/, src/, app/, tests/)

🧾 README.md (overview, visuals, setup, live demo link)

📓 Jupyter notebooks (EDA, experimentation, final model)

🧠 Source code (clean, modular, tested)

🌐 Deployed Streamlit app

🗒️ Technical documentation or final report

🧩 Optional: blog post, video demo, CI/CD, Dockerfile

7. Expected Outcomes & Portfolio Value

What skills this project showcases to hiring managers.

How it demonstrates end-to-end competency (data → model → deployment).

The professional storytelling aspect (why this project stands out).

8. Optional Enhancements

Provide advanced polish ideas such as:

NLP-based personalization using anime reviews or synopses.

Real-time update capability or API integration.

Recommendation visualization graphs (e.g., similarity networks).

Docker + GitHub Actions integration for reproducibility and CI/CD.

A short Medium post or video explaining approach and lessons learned.

9. Risk Mitigation & Next Steps

Include 3–5 key risks (e.g., sparse data, API rate limits, model explainability) and mitigation strategies.

⚙️ Formatting Requirements

Use clean Markdown.

No numbered sub-points unless hierarchy improves clarity.

Bold key terms, use tables for structured data, and ensure logical flow.

Maintain a balance between technical precision and readability for portfolio purposes.

🧩 Reasoning Scaffolding (Internal to ChatGPT-5)

Before generating text:

Briefly reason about the optimal structure of each section (not visible in final output).

Cross-check that each section connects logically to the previous one.

Prioritize clarity, completeness, and concision.

Produce final output that can be pasted directly into a GitHub README or project proposal.