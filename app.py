# --- AI Career Mentor Page ---
import os
import requests
from dotenv import load_dotenv
load_dotenv()
def render_ai_career_mentor():
    require_auth()
    st.title("AI Career Mentor")
    with st.container():
        col1, col2 = st.columns([2,1])
        with col1:
            st.info("This AI provides guidance only. It does not change your skills, career, roadmap, or progress.")
        with col2:
            st.markdown("#### Quick Tips")
            st.markdown("- Ask about learning strategies\n- Get advice for your current phase\n- Request explanations for skills or tasks")
    st.divider()
    user_id = st.session_state['auth_user']['id']
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    # Read-only context assembly
    c.execute('SELECT selected_career, hours_per_week FROM users WHERE id=?', (user_id,))
    row = c.fetchone()
    selected_career = row[0] if row else None
    hours_per_week = row[1] if row else None
    c.execute('SELECT skill_name, user_level FROM user_skills WHERE user_id=?', (user_id,))
    skills = {name: level for name, level in c.fetchall()}
    c.execute('SELECT phase, status FROM roadmap_tasks WHERE user_id=? ORDER BY id', (user_id,))
    roadmap = c.fetchall()
    # Determine current phase and progress summary
    phase_order = ["Foundation", "Core Skills", "Projects", "Job Readiness"]
    current_phase = None
    phase_counts = {p: 0 for p in phase_order}
    phase_completed = {p: 0 for p in phase_order}
    for phase, status in roadmap:
        if phase in phase_counts:
            phase_counts[phase] += 1
            if status == 'Completed':
                phase_completed[phase] += 1
    for p in phase_order:
        if phase_counts[p] and phase_completed[p] < phase_counts[p]:
            current_phase = p
            break
    if not current_phase:
        current_phase = phase_order[-1]
    total = sum(phase_counts.values())
    total_done = sum(phase_completed.values())
    progress_summary = f"{total_done} of {total} tasks completed"
    with st.container():
        col1, col2 = st.columns([2,1])
        with col1:
            st.markdown(f"**Career:** {selected_career if selected_career else 'Not set'}")
            st.markdown(f"**Skills:** {', '.join([f'{k} ({v})' for k,v in skills.items()]) if skills else 'None'}")
            st.markdown(f"**Current Roadmap Phase:** {current_phase}")
            st.markdown(f"**Progress:** {progress_summary}")
            st.markdown(f"**Time Availability:** {hours_per_week if hours_per_week else 'Not set'} hours/week")
        with col2:
            st.markdown("#### Status")
            st.metric("Phase", current_phase)
            st.metric("Tasks Done", f"{total_done}/{total}")
    st.divider()
    # Chat UI
    if 'mentor_history' not in st.session_state:
        st.session_state['mentor_history'] = []
    with st.container():
        for msg in st.session_state['mentor_history']:
            st.chat_message(msg['role']).write(msg['content'])
        # Suggested prompt buttons
        st.markdown("**Suggested Prompts:**")
        col1, col2, col3 = st.columns(3)
        suggested = None
        if col1.button("What should I do this week?"):
            suggested = "What should I do this week?"
        if col2.button("Explain this roadmap phase"):
            suggested = "Explain this roadmap phase"
        if col3.button("How to learn faster?"):
            suggested = "How to learn faster?"
        # Prevent page jump: store current page before chat input
        current_page = st.session_state.get('page', 'AI Career Mentor')
        user_input = st.chat_input("Ask the AI Career Mentor a question...")
        # Use suggested prompt if clicked
        if suggested:
            user_input = suggested
        if user_input:
            # System prompt
            system_prompt = (
                "You are an AI Career Mentor.\n"
                "You provide guidance, explanations, and learning strategies based on the user’s current career, skills, roadmap phase, progress, and time availability.\n"
                "You must NOT modify system data, suggest changing careers, or trigger updates to skills, roadmap, or progress.\n"
                "Your role is advisory only.\n"
                "Respond clearly, practically, and concisely."
            )
            context = {
                "selected_career": selected_career,
                "skills": skills,
                "current_roadmap_phase": current_phase,
                "progress_summary": progress_summary,
                "time_availability_hours_per_week": hours_per_week
            }
            # Compose prompt
            prompt = f"{system_prompt}\n\nUser context: {context}\n\nUser question: {user_input}"
            # Groq AI API call (no secrets in code)
            GROQ_API_KEY = os.getenv("GROQ_API_KEY")
            if not GROQ_API_KEY:
                ai_reply = "[AI Mentor unavailable: GROQ_API_KEY not set in environment.]"
            else:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "openai/gpt-oss-20b",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"User context: {context}\n\nUser question: {user_input}"}
                    ]
                }
                try:
                    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=30)
                    response.raise_for_status()
                    ai_reply = response.json().get('choices', [{}])[0].get('message', {}).get('content', '[No response from Groq API]')
                except Exception as e:
                    ai_reply = f"[AI Mentor unavailable: {e}]"
            st.session_state['mentor_history'].append({"role": "user", "content": user_input})
            st.session_state['mentor_history'].append({"role": "assistant", "content": ai_reply})
            st.session_state['page'] = current_page  # Restore page after chat
            st.chat_message("assistant").write(ai_reply)
    conn.close()
    st.stop()
# --- Career Insights Page ---
def render_career_insights():
    require_auth()
    st.title("Career Insights: Market Trends Dashboard")
    st.caption("Career insights are based on curated industry datasets and publicly available job trend summaries.")

    user_id = st.session_state['auth_user']['id']
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT selected_career FROM users WHERE id=?', (user_id,))
    row = c.fetchone()
    selected_career = row[0] if row else None
    conn.close()

    tab1, tab2, tab3, tab4 = st.tabs(["Roles", "Skills", "Skill Mapping", "Comparison"])

    with tab1:
        with st.container(border=True):
            st.subheader("Trending Career Roles")
            st.write("High-demand roles in the current job market (Market Insight Dataset)")
            trending_roles = pd.DataFrame([
                {"Role": "Data Analyst", "Demand": 85, "Level": "Fresher"},
                {"Role": "Data Scientist", "Demand": 92, "Level": "1–3 yrs"},
                {"Role": "ML Engineer", "Demand": 88, "Level": "1–3 yrs"},
                {"Role": "Full Stack Developer", "Demand": 90, "Level": "1–3 yrs"},
                {"Role": "Cybersecurity Engineer", "Demand": 80, "Level": "3+ yrs"},
                {"Role": "DevOps Engineer", "Demand": 78, "Level": "3+ yrs"},
            ])
            # Highlight user's career
            def highlight_role(row):
                if selected_career and row['Role'].lower() in selected_career.lower():
                    return ["font-weight: bold; background-color: #ffe066"]*len(row)
                return [""]*len(row)
            st.bar_chart(trending_roles.set_index("Role")["Demand"], use_container_width=True)
            st.dataframe(
                trending_roles.rename(columns={"Demand": "Demand Score", "Level": "Typical Experience"})
                .style.apply(highlight_role, axis=1),
                hide_index=True, use_container_width=True)

    with tab2:
        with st.container(border=True):
            st.subheader("Skill Demand Trends")
            st.write("Most frequently required skills across roles (Market Insight Dataset)")
            skill_trends = pd.DataFrame([
                {"Skill": "Python", "Demand": 95},
                {"Skill": "SQL", "Demand": 90},
                {"Skill": "Machine Learning", "Demand": 88},
                {"Skill": "Cloud (AWS/GCP)", "Demand": 85},
                {"Skill": "Data Visualization", "Demand": 80},
                {"Skill": "Linux", "Demand": 75},
            ])
            st.bar_chart(skill_trends.set_index("Skill")["Demand"], use_container_width=True)
            st.dataframe(skill_trends.rename(columns={"Demand": "Demand Score"}), hide_index=True, use_container_width=True)

    with tab3:
        with st.container(border=True):
            st.subheader("Career vs Skill Mapping")
            st.write("Which skills matter most for which roles")
            mapping = pd.DataFrame([
                {"Career Role": "Data Analyst", "Top Required Skills": "SQL, Excel, Visualization"},
                {"Career Role": "ML Engineer", "Top Required Skills": "Python, ML, DL"},
                {"Career Role": "Cybersecurity Engineer", "Top Required Skills": "Networking, Security Tools"},
                {"Career Role": "Full Stack Developer", "Top Required Skills": "JS, React, Node, DBs"},
                {"Career Role": "DevOps Engineer", "Top Required Skills": "Linux, CI/CD, Cloud"},
            ])
            def highlight_mapping(row):
                if selected_career and row['Career Role'].lower() in selected_career.lower():
                    return ["font-weight: bold; background-color: #ffe066"]*len(row)
                return [""]*len(row)
            st.dataframe(
                mapping.style.apply(highlight_mapping, axis=1),
                hide_index=True, use_container_width=True)

    with tab4:
        with st.container(border=True):
            st.subheader("Career Comparison")
            st.write("Compare roles across practical dimensions")
            comparison = pd.DataFrame([
                {"Role": "Data Analyst", "Learning Curve": "Easy", "Technical Depth": "Medium", "Growth": "High", "Stability": "High"},
                {"Role": "ML Engineer", "Learning Curve": "Hard", "Technical Depth": "High", "Growth": "High", "Stability": "Medium"},
                {"Role": "Cybersecurity Engineer", "Learning Curve": "Medium", "Technical Depth": "High", "Growth": "Medium", "Stability": "High"},
                {"Role": "Full Stack Developer", "Learning Curve": "Medium", "Technical Depth": "Medium", "Growth": "High", "Stability": "High"},
                {"Role": "DevOps Engineer", "Learning Curve": "Medium", "Technical Depth": "High", "Growth": "High", "Stability": "Medium"},
            ])
            def highlight_comparison(row):
                if selected_career and row['Role'].lower() in selected_career.lower():
                    return ["font-weight: bold; background-color: #ffe066"]*len(row)
                return [""]*len(row)
            st.dataframe(
                comparison.rename(columns={"Growth": "Career Growth", "Stability": "Market Stability"})
                .style.apply(highlight_comparison, axis=1),
                hide_index=True, use_container_width=True)

    st.markdown("---")
    st.caption("This dashboard is informational and does not generate personalized recommendations or roadmaps.")
    st.stop()

import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from database import init_db

if 'page' not in st.session_state:
    st.session_state['page'] = 'Login'


# --- Imports and helpers (move to top) ---
import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from database import init_db

if 'page' not in st.session_state:
    st.session_state['page'] = 'Login'

init_db()

def set_page(page):
    st.session_state['page'] = page

def require_auth():
    if not st.session_state.get('auth_user'):
        st.warning("Please login to access this page.")
        st.stop()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(email, password):
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT id, name, email, password_hash FROM users WHERE email=?', (email,))
    row = c.fetchone()
    conn.close()
    if row and row[3] == hash_password(password):
        return {"id": row[0], "name": row[1], "email": row[2]}
    return None

def register_user(name, email, password, education, experience, goal, hours_per_week):
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO users (name, email, password_hash, education, experience, goal, hours_per_week) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (name, email, hash_password(password), education, experience, goal, hours_per_week))
        conn.commit()
        user_id = c.lastrowid
    except sqlite3.IntegrityError:
        user_id = None
    conn.close()
    return user_id

if 'auth_user' not in st.session_state:
    st.session_state['auth_user'] = None

st.set_page_config(page_title="AI/ML Career Advisor", layout="wide")

def sidebar_router():
    if st.session_state['auth_user']:
        st.sidebar.title(f"Welcome, {st.session_state['auth_user']['name']}")
        user_id = st.session_state['auth_user']['id']
        conn = sqlite3.connect('data/career_advisor.db')
        c = conn.cursor()
        # Quiz completion
        c.execute('SELECT 1 FROM quiz_scores WHERE user_id=?', (user_id,))
        quiz_done = c.fetchone() is not None
        # Skill input completion
        c.execute('SELECT 1 FROM user_skills WHERE user_id=?', (user_id,))
        skills_done = c.fetchone() is not None
        # Recommendations available
        c.execute('SELECT selected_career FROM users WHERE id=?', (user_id,))
        selected_career = c.fetchone()[0]
        conn.close()
        # State-based navigation
        nav_options = ["Profile"]
        if not quiz_done:
            nav_options += ["Quiz"]
        if quiz_done:
            nav_options += ["Skill Input", "Career Recommendations"]
        if quiz_done and skills_done:
            nav_options += ["Career Selection"]
        if selected_career:
            nav_options += ["Roadmap Dashboard", "Progress Tracker"]
        nav_options += ["Career Insights", "AI Career Mentor"]
        # Remove duplicates, preserve order
        nav_options = [x for i, x in enumerate(nav_options) if x not in nav_options[:i]]
        # Defensive: ensure current page is valid
        current_page = st.session_state.get('page', nav_options[0])
        if current_page not in nav_options:
            current_page = nav_options[0]
            st.session_state['page'] = current_page
        nav = st.sidebar.radio("Go to", nav_options, index=nav_options.index(current_page))
        if nav != st.session_state['page']:
            set_page(nav)

sidebar_router()


# --- Page Functions (continued) ---
def render_career_recommendations():
    require_auth()
    st.title("Career Recommendations (Advisory Only)")
    user_id = st.session_state['auth_user']['id']
    import modules.ml_engine as ml_engine
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM quiz_scores WHERE user_id=?', (user_id,))
    quiz_done = c.fetchone()[0] > 0
    if not quiz_done:
        st.warning("You must complete the Aptitude Quiz before viewing career recommendations.")
        st.stop()
    c.execute('SELECT COUNT(*) FROM user_skills WHERE user_id=?', (user_id,))
    skills_done = c.fetchone()[0] > 0
    if not skills_done:
        st.warning("You must submit your skills before viewing career recommendations.")
        st.stop()
    top3, similarities = ml_engine.recommend_careers(user_id)
    if top3:
        st.subheader("Top 3 Career Recommendations:")
        for idx, (career, score) in enumerate(top3, 1):
            st.write(f"{idx}. {career} (Similarity Confidence: {score*100:.0f}%)")
        st.info("These are ML-based recommendations. Please proceed to the next step to select and confirm your career goal.")
    else:
        st.warning("No career recommendations available. Complete quiz and skill input first.")
    conn.close()
    st.stop()

def render_career_selection():
    require_auth()
    st.title("Career Selection & Confirmation")
    st.write("Select and confirm your target career from the ML recommendations. This will lock your goal and enable roadmap generation.")
    user_id = st.session_state['auth_user']['id']
    import modules.ml_engine as ml_engine
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM user_skills WHERE user_id=?', (user_id,))
    skills_done = c.fetchone()[0] > 0
    if not skills_done:
        st.warning("You must submit your skills before selecting a career goal.")
        conn.close()
        st.stop()
    c.execute('SELECT COUNT(*) FROM quiz_scores WHERE user_id=?', (user_id,))
    quiz_done = c.fetchone()[0] > 0
    if not quiz_done:
        st.warning("You must complete the Aptitude Quiz before selecting a career goal.")
        conn.close()
        st.stop()
    top3, similarities = ml_engine.recommend_careers(user_id)
    if not top3:
        st.warning("No career recommendations available. Complete quiz and skill input first.")
        conn.close()
        st.stop()
    c.execute('SELECT selected_career FROM users WHERE id=?', (user_id,))
    already = c.fetchone()[0]
    if already:
        st.subheader("Current Career Goal")
        st.success(f"{already}")
        st.warning("To change, reset your profile. This will erase your roadmap and recommendations.")
        st.stop()
    st.subheader("Select Your Career Goal")
    career_options = [career for career, _ in top3]
    selected = st.radio("Career Options", career_options, key="career_select_confirm")
    if st.button("Confirm Career Goal"):
        c.execute('UPDATE users SET selected_career=? WHERE id=?', (selected, user_id))
        conn.commit()
        # --- Generate personalized roadmap tasks ---
        from data.career_skills import CAREER_SKILLS
        c.execute('DELETE FROM roadmap_tasks WHERE user_id=?', (user_id,))
        # --- Standardized Phases ---
        phases = [
            ("Foundation", "Learn fundamentals and basics"),
            ("Core Skills", "Build core technical skills for your track"),
            ("Projects", "Career-specific projects"),
            ("Job Readiness", "Resume, portfolio, applications, networking"),
        ]
        skills = CAREER_SKILLS.get(selected, [])
        # --- Foundation: first 2 skills ---
        for skill in skills[:2]:
            skill_name, group, req_prof, imp = skill
            task = f"{skill_name} ({group})"
            c.execute('INSERT INTO roadmap_tasks (user_id, phase, task, status) VALUES (?, ?, ?, ?)',
                      (user_id, "Foundation", task, 'Pending'))
        # --- Core Skills: next 2-4 skills ---
        for skill in skills[2:6]:
            skill_name, group, req_prof, imp = skill
            task = f"{skill_name} ({group})"
            c.execute('INSERT INTO roadmap_tasks (user_id, phase, task, status) VALUES (?, ?, ?, ?)',
                      (user_id, "Core Skills", task, 'Pending'))
        # --- Projects: career-specific projects ---
        project_map = {
            "Data Scientist": [
                ("End-to-end ML Project", "Build and deploy a machine learning model from scratch.", "Deployed ML solution with documentation."),
                ("Data Analysis Case Study", "Analyze a real-world dataset and present insights.", "Insightful report and visualizations."),
            ],
            "Cybersecurity Engineer": [
                ("Vulnerability Assessment Lab", "Identify and assess vulnerabilities in a test environment.", "Vulnerability report and mitigation plan."),
                ("Incident Response Simulation", "Respond to a simulated security incident.", "Incident report and lessons learned."),
            ],
            "AI Research Engineer": [
                ("Research Paper Implementation", "Reproduce results from a published AI paper.", "Working codebase and comparison report."),
                ("Novel Experimentation", "Design and run a new experiment in AI research.", "Experiment results and analysis."),
            ],
            "Machine Learning Engineer": [
                ("Production ML Pipeline", "Build a scalable ML pipeline for deployment.", "Automated pipeline and deployment scripts."),
                ("Model Optimization Project", "Optimize an existing ML model for performance.", "Improved model and benchmarking report."),
            ],
            "Data Analyst": [
                ("Business Data Dashboard", "Create a dashboard for business insights.", "Interactive dashboard and summary report."),
                ("Reporting Automation", "Automate regular data reporting tasks.", "Automated reports and scripts."),
            ],
            "DevOps / Cloud Engineer": [
                ("CI/CD Pipeline Setup", "Implement CI/CD for a sample project.", "Working CI/CD pipeline and documentation."),
                ("Cloud Migration Project", "Migrate an app to the cloud.", "Cloud-deployed app and migration report."),
            ],
            "Product Manager": [
                ("Product Launch Plan", "Develop a launch plan for a new product.", "Launch roadmap and stakeholder presentation."),
                ("Market Analysis Report", "Analyze market trends for a product area.", "Market analysis report and recommendations."),
            ],
            "Software Engineer": [
                ("System Design Project", "Design and implement a scalable system.", "System architecture and codebase."),
                ("Open Source Contribution", "Contribute to an open source project.", "Accepted pull request and contribution summary."),
            ],
            "Web / Full Stack Developer": [
                ("Full Stack Web App", "Build a full stack web application.", "Deployed web app and documentation."),
                ("UI/UX Redesign", "Redesign the UI/UX of an existing app.", "Improved UI/UX and user feedback report."),
            ],
        }
        for proj in project_map.get(selected, []):
            title, objective, outcome = proj
            task = f"{title}: {objective} (Expected: {outcome})"
            c.execute('INSERT INTO roadmap_tasks (user_id, phase, task, status) VALUES (?, ?, ?, ?)',
                      (user_id, "Projects", task, 'Pending'))
        # --- Job Readiness: always include these ---
        job_ready_tasks = [
            ("Resume Building", "Draft and polish your professional resume.", "Completed resume ready for applications."),
            ("Portfolio Preparation", "Create or update your project portfolio.", "Online portfolio with project showcases."),
            ("Mock Interviews", "Participate in mock interviews for your target role.", "Interview feedback and improvement plan."),
            ("Job Applications", "Apply to relevant job openings.", "List of applications submitted."),
            ("Networking / Referrals", "Reach out to professionals and seek referrals.", "Networking log and referral outcomes."),
        ]
        for title, objective, outcome in job_ready_tasks:
            task = f"{title}: {objective} (Expected: {outcome})"
            c.execute('INSERT INTO roadmap_tasks (user_id, phase, task, status) VALUES (?, ?, ?, ?)',
                      (user_id, "Job Readiness", task, 'Pending'))
        conn.commit()
        st.success(f"Career goal set to: {selected}. Your personalized roadmap has been generated.")
        st.rerun()
    conn.close()
    st.stop()

def render_roadmap():
    require_auth()
    st.title("Career Roadmap Dashboard")
    user_id = st.session_state['auth_user']['id']
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT selected_career FROM users WHERE id=?', (user_id,))
    selected_career = c.fetchone()[0]
    if not selected_career:
        st.warning("You must confirm your career goal before generating a roadmap.")
        conn.close()
        st.stop()
    c.execute('SELECT phase, task, status FROM roadmap_tasks WHERE user_id=? ORDER BY id', (user_id,))
    tasks = c.fetchall()
    if not tasks:
        st.info("No roadmap generated yet. Please confirm your career goal to generate a roadmap.")
        conn.close()
        st.stop()

    # --- Standardized Phases ---
    phase_defs = [
        {"name": "Foundation", "desc": "Core programming / fundamentals", "icon": "🟦", "range": "0–2 months"},
        {"name": "Core Skills", "desc": "Domain-specific skills", "icon": "🟧", "range": "2–4 months"},
        {"name": "Projects", "desc": "Career-specific projects", "icon": "🟪", "range": "4–6 months"},
        {"name": "Job Readiness", "desc": "Resume, portfolio, applications, networking", "icon": "🟩", "range": "6+ months"},
    ]
    # --- Assign tasks to phases ---
    phase_task_map = {p['name']: [] for p in phase_defs}
    for phase, task, status in tasks:
        if phase in phase_task_map:
            phase_task_map[phase].append((task, status))
    # --- Progress Calculation ---
    total_tasks = sum(len(phase_task_map[p['name']]) for p in phase_defs)
    total_completed = sum(1 for p in phase_defs for _, status in phase_task_map[p['name']] if status == 'Completed')
    # --- Current Phase ---
    current_phase = None
    for p in phase_defs:
        if any(status != 'Completed' for _, status in phase_task_map[p['name']]):
            current_phase = p['name']
            break
    if not current_phase:
        current_phase = phase_defs[-1]['name']
    st.subheader(f"Roadmap for {selected_career}")
    st.progress(total_completed/total_tasks if total_tasks else 0, text=f"Overall Progress: {total_completed} of {total_tasks} tasks completed")
    st.divider()
    # --- Visual Timeline: Phase Cards ---
    for p in phase_defs:
        phase_name = p['name']
        phase_tasks = phase_task_map[phase_name]
        completed = sum(1 for _, status in phase_tasks if status == 'Completed')
        total = len(phase_tasks)
        percent = completed/total if total else 0
        is_current = (phase_name == current_phase)
        with st.container():
            st.subheader(f"{p['icon']} {phase_name} ({p['range']})")
            st.caption(p['desc'])
            st.progress(percent, text=f"{completed} of {total} tasks completed")
            if is_current:
                st.markdown(":green[You are here]")
            if not phase_tasks:
                st.caption("No tasks in this phase.")
            else:
                for task, status in phase_tasks:
                    st.write(f"- {task}")
            st.divider()
    conn.close()
    st.stop()

# --- Helper for updating roadmap task status ---
def update_roadmap_task_status(tid, checked):
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('UPDATE roadmap_tasks SET status=? WHERE id=?', ('Completed' if checked else 'Pending', tid))
    conn.commit()
    conn.close()
    st.rerun()

def render_progress_tracker():
    require_auth()
    st.title("Progress Tracker")
    user_id = st.session_state['auth_user']['id']
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT selected_career FROM users WHERE id=?', (user_id,))
    selected_career = c.fetchone()[0]
    if not selected_career:
        st.warning("You must confirm your career goal before tracking progress.")
        conn.close()
        st.stop()
    c.execute('SELECT id, phase, task, status FROM roadmap_tasks WHERE user_id=? ORDER BY id', (user_id,))
    tasks = c.fetchall()
    if not tasks:
        st.info("No roadmap generated yet. Please confirm your career goal to generate a roadmap.")
        conn.close()
        st.stop()

    # --- Completion Summary Card ---
    total_tasks = len(tasks)
    completed_tasks = sum(1 for _, _, _, status in tasks if status == 'Completed')
    # For demo, we use +0 today (could be improved with timestamp tracking)
    st.metric("Tasks Completed", f"{completed_tasks} / {total_tasks}")
    st.divider()

    # --- Phase-wise Progress ---
    phase_defs = [
        {"name": "Foundation", "desc": "Core programming / fundamentals"},
        {"name": "Core Skills", "desc": "Domain-specific skills"},
        {"name": "Projects", "desc": "Career-specific projects"},
        {"name": "Job Readiness", "desc": "Resume, portfolio, applications, networking"},
    ]
    phase_task_map = {p['name']: [] for p in phase_defs}
    for tid, phase, task, status in tasks:
        if phase in phase_task_map:
            phase_task_map[phase].append((tid, task, status))

    # Balloons: only trigger if a phase is just now fully completed
    if 'completed_phases' not in st.session_state:
        st.session_state['completed_phases'] = set()
    show_balloons = False
    for p in phase_defs:
        phase_name = p['name']
        phase_tasks = phase_task_map[phase_name]
        total = len(phase_tasks)
        completed = sum(1 for _, _, status in phase_tasks if status == 'Completed')
        percent = completed/total if total else 0
        with st.container():
            st.subheader(f"{phase_name}")
            st.caption(p['desc'])
            st.progress(percent, text=f"{completed} of {total} tasks completed")
            # Checkboxes for each task
            for tid, task, status in phase_tasks:
                checked = (status == 'Completed')
                if st.checkbox(task, value=checked, key=f"progress_{tid}"):
                    if not checked:
                        c.execute('UPDATE roadmap_tasks SET status=? WHERE id=?', ('Completed', tid))
                        conn.commit()
                        completed += 1
                else:
                    if checked:
                        c.execute('UPDATE roadmap_tasks SET status=? WHERE id=?', ('Pending', tid))
                        conn.commit()
                        completed -= 1
            # Balloons logic: only show if phase just completed and wasn't before
            if total > 0 and completed == total and phase_name not in st.session_state['completed_phases']:
                show_balloons = True
                st.session_state['completed_phases'].add(phase_name)
        st.divider()
    if show_balloons:
        st.balloons()
    st.success("Progress updated.")
    conn.close()
    st.stop()

def render_profile():
    require_auth()
    st.title("Profile")
    user_id = st.session_state['auth_user']['id']
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT name, email, education, experience, goal, hours_per_week, selected_career FROM users WHERE id=?', (user_id,))
    user_row = c.fetchone()
    # Progress bar logic
    c.execute('SELECT 1 FROM quiz_scores WHERE user_id=?', (user_id,))
    quiz_done = c.fetchone() is not None
    c.execute('SELECT 1 FROM user_skills WHERE user_id=?', (user_id,))
    skills_done = c.fetchone() is not None
    career_selected = user_row[6] is not None
    c.execute('SELECT 1 FROM roadmap_tasks WHERE user_id=?', (user_id,))
    roadmap_active = c.fetchone() is not None
    conn.close()
    # Progress calculation
    progress = 0.0
    if quiz_done and skills_done:
        progress = 0.3
    if career_selected:
        progress = 0.6
    if roadmap_active:
        progress = 1.0
    st.progress(progress, text=f"Profile: {int(progress*100)}% complete")
    st.divider()
    with st.container():
        col1, col2 = st.columns([2,1])
        with col1:
            st.subheader("User Information")
            st.write(f"**Name:** {user_row[0]}")
            st.write(f"**Email:** {user_row[1]}")
            st.write(f"**Education:** {user_row[2]}")
            st.write(f"**Experience:** {user_row[3]}")
            st.write(f"**Goal:** {user_row[4]}")
            st.write(f"**Hours/Week:** {user_row[5]}")
        with col2:
            st.subheader("Status")
            if user_row[6]:
                st.metric("Career Goal", user_row[6], "Locked")
            else:
                st.metric("Career Goal", "Not set", "Unlocked")
    st.divider()
    st.subheader("Career Goal Status")
    if user_row[6]:
        st.success(f"Locked Career Goal: {user_row[6]}")
        st.caption("Selected after ML recommendations. To change, reset your profile.")
    else:
        st.warning("No career goal selected yet.")
    st.divider()
    st.subheader("Update Quiz Responses")
    st.warning("Updating quiz responses will regenerate career recommendations and roadmap.")
    if st.button("Update Quiz"):
        set_page("Quiz")
        conn = sqlite3.connect('data/career_advisor.db')
        c = conn.cursor()
        c.execute('DELETE FROM quiz_scores WHERE user_id=?', (user_id,))
        conn.commit()
        conn.close()
        st.session_state['page'] = "Quiz"
        st.stop()
    st.divider()
    st.subheader("Update Time Availability")
    new_hours = st.number_input("Update Hours per Week", min_value=1, max_value=80, value=user_row[5], key="profile_hours")
    if st.button("Save Time Availability"):
        conn = sqlite3.connect('data/career_advisor.db')
        c = conn.cursor()
        c.execute('UPDATE users SET hours_per_week=? WHERE id=?', (new_hours, user_id))
        conn.commit()
        conn.close()
        st.success("Time availability updated. Roadmap will adapt to new value.")
    st.divider()
    st.subheader("Reset / Re-evaluate")
    reset_confirmed = st.checkbox("I understand this will erase my quiz responses, career goal, and roadmap.")
    if st.button("Reset Profile (Quiz & Roadmap)"):
        if reset_confirmed:
            conn = sqlite3.connect('data/career_advisor.db')
            c = conn.cursor()
            c.execute('DELETE FROM quiz_scores WHERE user_id=?', (user_id,))
            c.execute('DELETE FROM roadmap_tasks WHERE user_id=?', (user_id,))
            c.execute('UPDATE users SET selected_career=NULL WHERE id=?', (user_id,))
            conn.commit()
            conn.close()
            st.success("Profile reset. Please re-complete quiz and career selection.")
            set_page("Quiz")
            st.session_state['page'] = "Quiz"
            st.stop()
        else:
            st.warning("Please confirm by checking the box above before resetting.")
    st.divider()
    st.subheader("Skill Management")
    st.info("Want to update your skills? Go to Skill Input.")
    if st.button("Go to Skill Input"):
        set_page("Skill Input")
        st.session_state['page'] = "Skill Input"
        st.stop()
    st.divider()
    st.subheader("Logout")
    if st.button("Logout"):
        st.session_state['auth_user'] = None
        set_page("Login")
        st.rerun()
        st.session_state['page'] = "Login"
        st.stop()
    st.stop()

def render_quiz():
    require_auth()
    st.title("Psychometric / Interest Quiz")
    user_id = st.session_state['auth_user']['id']
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT 1 FROM quiz_scores WHERE user_id=?', (user_id,))
    quiz_exists = c.fetchone() is not None
    conn.close()
    if quiz_exists:
        st.info("Quiz already completed. Update available in Profile section.")
        st.stop()
    st.write("Answer the following 12 questions to help us understand your interests and aptitude.")
    import numpy as np
    quiz_questions = [
        {"q": "Which activity do you enjoy most?", "options": [
            ("Solving puzzles", [1,0,0,0,0]),
            ("Drawing or writing", [0,1,0,0,0]),
            ("Building gadgets", [0,0,1,0,0]),
            ("Talking with people", [0,0,0,1,0])]},
        {"q": "What describes you best?", "options": [
            ("Logical thinker", [1,0,0,0,0]),
            ("Imaginative", [0,1,0,0,0]),
            ("Hands-on", [0,0,1,0,0]),
            ("Curious learner", [0,0,0,0,1])]},
        {"q": "Preferred project type?", "options": [
            ("Data analysis", [1,0,0,0,0]),
            ("Creative design", [0,1,0,0,0]),
            ("System building", [0,0,1,0,0]),
            ("Team leadership", [0,0,0,1,0])]},
        {"q": "You are praised for:", "options": [
            ("Problem solving", [1,0,0,0,0]),
            ("Original ideas", [0,1,0,0,0]),
            ("Technical skills", [0,0,1,0,0]),
            ("Communication", [0,0,0,1,0])]},
        {"q": "You prefer to:", "options": [
            ("Analyze data", [1,0,0,0,0]),
            ("Brainstorm", [0,1,0,0,0]),
            ("Assemble things", [0,0,1,0,0]),
            ("Teach others", [0,0,0,1,0])]},
        {"q": "Which is most appealing?", "options": [
            ("Finding patterns", [1,0,0,0,0]),
            ("Inventing", [0,1,0,0,0]),
            ("Engineering", [0,0,1,0,0]),
            ("Exploring new topics", [0,0,0,0,1])]},
        {"q": "You excel at:", "options": [
            ("Critical thinking", [1,0,0,0,0]),
            ("Artistic work", [0,1,0,0,0]),
            ("Technical tasks", [0,0,1,0,0]),
            ("Empathy", [0,0,0,1,0])]},
        {"q": "You value:", "options": [
            ("Accuracy", [1,0,0,0,0]),
            ("Innovation", [0,1,0,0,0]),
            ("Efficiency", [0,0,1,0,0]),
            ("Curiosity", [0,0,0,0,1])]},
        {"q": "Best describes your study style:", "options": [
            ("Structured", [1,0,0,0,0]),
            ("Experimental", [0,1,0,0,0]),
            ("Practical", [0,0,1,0,0]),
            ("Discussion-based", [0,0,0,1,0])]},
        {"q": "You are motivated by:", "options": [
            ("Solving challenges", [1,0,0,0,0]),
            ("Creating something new", [0,1,0,0,0]),
            ("Building systems", [0,0,1,0,0]),
            ("Learning new things", [0,0,0,0,1])]},
        {"q": "You prefer to work:", "options": [
            ("Independently", [1,0,0,0,0]),
            ("On creative tasks", [0,1,0,0,0]),
            ("With machines", [0,0,1,0,0]),
            ("With people", [0,0,0,1,0])]},
        {"q": "You are most interested in:", "options": [
            ("Data & logic", [1,0,0,0,0]),
            ("Design & arts", [0,1,0,0,0]),
            ("Technology", [0,0,1,0,0]),
            ("Exploring ideas", [0,0,0,0,1])]
        }
    ]
    quiz_answers = []
    with st.form("quiz_form"):
        for idx, q in enumerate(quiz_questions):
            options = [opt[0] for opt in q["options"]]
            answer = st.radio(q["q"], options, key=f"q{idx}")
            quiz_answers.append(answer)
        submitted = st.form_submit_button("Submit Quiz")
    if submitted:
        feature_vec = np.zeros(5)
        for idx, answer in enumerate(quiz_answers):
            for opt, vec in quiz_questions[idx]["options"]:
                if answer == opt:
                    feature_vec += np.array(vec)
        feature_vec = feature_vec / len(quiz_questions)
        conn = sqlite3.connect('data/career_advisor.db')
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO quiz_scores (user_id, analytical, creativity, engineering, communication, curiosity) VALUES (?, ?, ?, ?, ?, ?)''',
                  (user_id, float(feature_vec[0]), float(feature_vec[1]), float(feature_vec[2]), float(feature_vec[3]), float(feature_vec[4])))
        conn.commit()
        conn.close()
        st.success(f"Quiz submitted! Your feature vector: {np.round(feature_vec,2).tolist()}")
        st.stop()

def render_register():
    st.title("Register")
    with st.form("register_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        education = st.selectbox("Education Level", ["Student", "Fresher", "Working Professional"])
        experience = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Advanced"])
        goal = st.selectbox("Career Goal", ["First job", "Switch", "Promotion", "Higher studies"])
        hours_per_week = st.number_input("Time Availability (hours per week)", min_value=1, max_value=80, value=5)
        submitted = st.form_submit_button("Register")
    if submitted:
        if not (name and email and password):
            st.warning("Please fill all fields.")
        else:
            user_id = register_user(name, email, password, education, experience, goal, hours_per_week)
            if user_id:
                st.success("Registration successful! Please login.")
                set_page("Login")
                st.session_state['page'] = "Profile"
                st.stop()
            else:
                st.error("Email already registered.")
    # Add Back to Login button
    if st.button("Back to Login"):
        set_page("Login")
        st.session_state['page'] = "Login"
        st.rerun()
    st.stop()

def render_login():
    st.title("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        user = check_login(email, password)
        if user:
            st.session_state['auth_user'] = user
            set_page("Profile")
            st.session_state['page'] = "Profile"
            st.stop()
        else:
            st.error("Invalid email or password.")
    if st.button("New user? Register here"):
        set_page("Register")
        st.session_state['page'] = "Register"
        st.rerun()
    st.stop()



# --- Move render_skill_input above main router ---
def render_skill_input():
    require_auth()
    st.title("Skill Input")
    st.info("Skills represent where you are today. They affect roadmap difficulty, task depth, and learning pace — not your career choice.")
    user_id = st.session_state['auth_user']['id']
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_skills (
        user_id INTEGER,
        skill_name TEXT,
        user_level REAL,
        PRIMARY KEY (user_id, skill_name),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    # --- CRUD Logic ---
    st.subheader("Your Skills")
    c.execute('SELECT skill_name, user_level FROM user_skills WHERE user_id=?', (user_id,))
    skills = c.fetchall()
    edit_skill = st.session_state.get('edit_skill')
    # Table UI with st.dataframe
    import numpy as np
    if skills:
        skill_df = pd.DataFrame([
            {
                "Skill Name": name,
                "Proficiency (%)": int(level*100),
                "Actions": ""
            } for name, level in skills
        ])
        # Add action buttons inline
        for idx, (name, level) in enumerate(skills):
            cols = st.columns([3,2,1,1])
            cols[0].write(name)
            cols[1].progress(level, text=f"{int(level*100)}%")
            edit_key = f"edit_{user_id}_{name}"
            del_key = f"del_{user_id}_{name}"
            if cols[2].button("✏️ Edit", key=edit_key):
                st.session_state['edit_skill'] = name
                st.session_state['edit_level'] = level
                st.rerun()
            if cols[3].button("🗑 Delete", key=del_key):
                c.execute('DELETE FROM user_skills WHERE user_id=? AND skill_name=?', (user_id, name))
                conn.commit()
                st.toast(f"Deleted skill: {name}")
                st.session_state.pop('edit_skill', None)
                st.rerun()
    else:
        st.warning("No skills added yet. Please input your current skills.")
    st.divider()
    # Add/Edit Form
    with st.form("skill_input_form"):
        if edit_skill:
            st.write(f"Editing skill: {edit_skill}")
            skill_name = edit_skill
            level = st.slider("Proficiency", 0.0, 1.0, float(st.session_state.get('edit_level', 0.5)), step=0.05)
        else:
            skill_name = st.text_input("Skill Name")
            level = st.slider("Proficiency", 0.0, 1.0, 0.5, step=0.05)
        submitted = st.form_submit_button("Save Skill")
    if submitted:
        if skill_name:
            # Prevent duplicate add
            c.execute('SELECT 1 FROM user_skills WHERE user_id=? AND skill_name=?', (user_id, skill_name))
            exists = c.fetchone()
            if exists and not edit_skill:
                st.warning(f"Skill '{skill_name}' already exists. Please use edit to update proficiency.")
            else:
                c.execute('INSERT OR REPLACE INTO user_skills (user_id, skill_name, user_level) VALUES (?, ?, ?)',
                          (user_id, skill_name, level))
                conn.commit()
                st.toast(f"Skill '{skill_name}' saved!")
                st.session_state.pop('edit_skill', None)
                st.session_state.pop('edit_level', None)
                st.rerun()
        else:
            st.warning("Skill name required.")
    conn.close()
    st.stop()

# --- Main Router (after all render_* functions) ---
if st.session_state['page'] == "Skill Input":
    render_skill_input()
elif st.session_state['page'] == "Career Recommendations":
    render_career_recommendations()
elif st.session_state['page'] == "Career Selection":
    render_career_selection()
elif st.session_state['page'] == "Roadmap Dashboard":
    render_roadmap()
elif st.session_state['page'] == "Progress Tracker":
    render_progress_tracker()
elif st.session_state['page'] == "Profile":
    render_profile()
elif st.session_state['page'] == "Quiz":
    render_quiz()
elif st.session_state['page'] == "Register":
    render_register()
elif st.session_state['page'] == "Login":
    render_login()
elif st.session_state['page'] == "Career Insights":
    render_career_insights()
elif st.session_state['page'] == "AI Career Mentor":
    render_ai_career_mentor()
else:
    st.error("Unknown page. Please use the sidebar to navigate.")
    st.stop()

## (No code here; all logic is inside functions. Remove stray code block that causes NameError.)
phase_task_map = {p['name']: [] for p in phases}
phase_order = [p['name'] for p in phases]
n_tasks = len(tasks)
n_phases = len(phases)
per_phase = [n_tasks // n_phases + (1 if x < n_tasks % n_phases else 0) for x in range(n_phases)]
idx = 0
for phase_idx, count in enumerate(per_phase):
    for _ in range(count):
        if idx < n_tasks:
            tid, task, status = tasks[idx]
            phase_task_map[phases[phase_idx]['name']].append((tid, task, status))
            idx += 1

# --- Determine current phase (first with incomplete task) ---
    current_phase = None
    for p in phase_order:
        if any(status != 'Completed' for _, _, status in phase_task_map[p]):
            current_phase = p
            break
    if not current_phase:
        current_phase = phase_order[-1]

    # --- Overall Progress ---
    total_tasks = sum(len(phase_task_map[p]) for p in phase_order)
    total_completed = sum(1 for p in phase_order for _, _, status in phase_task_map[p] if status == 'Completed')
    st.subheader(f"Roadmap for {selected_career}")
    st.progress(total_completed/total_tasks if total_tasks else 0, text=f"Overall Progress: {total_completed} of {total_tasks} tasks completed")

    for phase in phases:
        phase_name = phase['name']
        phase_tasks = phase_task_map[phase_name]
        total = len(phase_tasks)
        completed = sum(1 for _, _, status in phase_tasks if status == 'Completed')
        is_current = (phase_name == current_phase)
        with st.container():
            st.markdown(f"#### {phase['icon']} {phase_name} ({phase['range'][0]}–{phase['range'][1] if phase['range'][1]<12 else '+'} months)")
            st.caption(phase['desc'])
            st.progress(completed/total if total else 0, text=f"{completed} of {total} tasks completed")
            if total == 0:
                st.caption("No tasks in this phase.")
    conn.close()
    st.stop()
    conn.close()
    st.stop()

def render_career_selection():
    require_auth()
    st.title("Career Selection & Confirmation")
    st.write("Select and confirm your target career from the ML recommendations. This will lock your goal and enable roadmap generation.")
    user_id = st.session_state['auth_user']['id']
    import modules.ml_engine as ml_engine
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM user_skills WHERE user_id=?', (user_id,))
    skills_done = c.fetchone()[0] > 0
    if not skills_done:
        st.warning("You must submit your skills before selecting a career goal.")
        conn.close()
        st.stop()
    c.execute('SELECT COUNT(*) FROM quiz_scores WHERE user_id=?', (user_id,))
    quiz_done = c.fetchone()[0] > 0
    if not quiz_done:
        st.warning("You must complete the Aptitude Quiz before selecting a career goal.")
        conn.close()
        st.stop()
    top3, similarities = ml_engine.recommend_careers(user_id)
    if not top3:
        st.warning("No career recommendations available. Complete quiz and skill input first.")
        conn.close()
        st.stop()
    st.subheader("Select Your Career Goal")
    career_options = [career for career, _ in top3]
    selected = st.radio("Career Options", career_options, key="career_select_confirm")
    if st.button("Confirm Career Goal"):
        c.execute('SELECT selected_career FROM users WHERE id=?', (user_id,))
        already = c.fetchone()[0]
        if already:
            st.info(f"Career goal already set to: {already}. To change, contact support or reset your profile.")
        else:
            c.execute('UPDATE users SET selected_career=? WHERE id=?', (selected, user_id))
            conn.commit()
            st.success(f"Career goal set to: {selected}. You can now generate your roadmap.")
            st.rerun()
    conn.close()
    st.stop()

def render_roadmap():
    require_auth()
    st.title("Personalized Roadmap")
    user_id = st.session_state['auth_user']['id']
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT selected_career FROM users WHERE id=?', (user_id,))
    selected_career = c.fetchone()[0]
    if not selected_career:
        st.warning("You must confirm your career goal before generating a roadmap.")
        conn.close()
        st.stop()
    c.execute('SELECT id, task, status FROM roadmap_tasks WHERE user_id=? ORDER BY id', (user_id,))
    tasks = c.fetchall()
    if not tasks:
        st.info("No roadmap generated yet. Please confirm your career goal to generate a roadmap.")
    else:
        st.subheader(f"Roadmap for {selected_career}")
        for tid, task, status in tasks:
            st.checkbox(task, value=(status == 'Completed'), key=f"roadmap_{tid}", disabled=True)
    conn.close()
    st.stop()

def render_progress_tracker():
    require_auth()
    st.title("Progress Tracker")
    user_id = st.session_state['auth_user']['id']
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT selected_career FROM users WHERE id=?', (user_id,))
    selected_career = c.fetchone()[0]
    if not selected_career:
        st.warning("No roadmap generated yet. Please complete Career Selection.")
        conn.close()
        st.stop()
    c.execute('SELECT id, task, status FROM roadmap_tasks WHERE user_id=? ORDER BY id', (user_id,))
    tasks = c.fetchall()
    if not tasks:
        st.info("No roadmap generated yet. Please complete Career Selection.")
        conn.close()
        st.stop()
    st.subheader(f"Progress for {selected_career}")
    for tid, task, status in tasks:
        checked = (status == 'Completed')
        if st.checkbox(task, value=checked, key=f"progress_{tid}"):
            if not checked:
                c.execute('UPDATE roadmap_tasks SET status=? WHERE id=?', ('Completed', tid))
                conn.commit()
        else:
            if checked:
                c.execute('UPDATE roadmap_tasks SET status=? WHERE id=?', ('Pending', tid))
                conn.commit()
    st.success("Progress updated.")
    conn.close()
    st.stop()

def render_profile():
    require_auth()
    st.title("Profile & Settings")
    user_id = st.session_state['auth_user']['id']
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT name, email, education, experience, goal, hours_per_week FROM users WHERE id=?', (user_id,))
    user_row = c.fetchone()
    conn.close()
    st.subheader("User Information")
    st.write(f"**Name:** {user_row[0]}")
    st.write(f"**Email:** {user_row[1]}")
    st.write(f"**Education:** {user_row[2]}")
    st.write(f"**Experience:** {user_row[3]}")
    st.write(f"**Goal:** {user_row[4]}")
    st.write(f"**Hours/Week:** {user_row[5]}")
    st.markdown("---")
    st.subheader("Update Quiz Responses")
    st.warning("Updating information will regenerate career recommendations and roadmap.")
    if st.button("Update Quiz"):
        set_page("Quiz")
        conn = sqlite3.connect('data/career_advisor.db')
        c = conn.cursor()
        c.execute('DELETE FROM quiz_scores WHERE user_id=?', (user_id,))
        conn.commit()
        conn.close()
        st.session_state['page'] = "Quiz"
        st.stop()
    st.subheader("Update Skill Levels")
    from data.career_skills import CAREER_SKILLS
    career_list = list(CAREER_SKILLS.keys())
    selected_career = st.selectbox("Select Career to Update Skills", career_list, key="profile_skill_career")
    if st.button("Update Skills"):
        st.title("Skill Input")
        st.info("These are your current skills.\nCareer goal selection happens later based on recommendations.")
        c.execute('''CREATE TABLE IF NOT EXISTS user_skills (
            user_id INTEGER,
            skill_name TEXT,
            user_level REAL,
            PRIMARY KEY (user_id, skill_name),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )''')
        conn.commit()
        c.execute('SELECT skill_name, user_level FROM user_skills WHERE user_id=?', (user_id,))
        existing_skills = c.fetchall()
        skill_levels = {"Not Known": 0.0, "Beginner": 0.3, "Intermediate": 0.6, "Advanced": 0.85}
        st.subheader("Your Skills")
        if not existing_skills:
            st.warning("No skills added yet. Please input your current skills.")
        else:
            for name, level in existing_skills:
                st.write(f"{name}: {level}")
        with st.form("skill_input_form"):
            new_skill = st.text_input("Skill Name")
            new_level = st.selectbox("Proficiency Level", list(skill_levels.keys()))
            submitted = st.form_submit_button("Add/Update Skill")
        if submitted and new_skill:
            c.execute('INSERT OR REPLACE INTO user_skills (user_id, skill_name, user_level) VALUES (?, ?, ?)',
                      (user_id, new_skill, skill_levels[new_level]))
            conn.commit()
            st.success(f"Skill '{new_skill}' updated!")
            st.rerun()
        conn.close()
        st.stop()
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('SELECT 1 FROM quiz_scores WHERE user_id=?', (user_id,))
    quiz_exists = c.fetchone() is not None
    conn.close()
    if quiz_exists:
        st.info("Quiz already completed. Update available in Profile section.")
        st.stop()
    st.write("Answer the following 12 questions to help us understand your interests and aptitude.")
    import numpy as np
    quiz_questions = [
        {"q": "Which activity do you enjoy most?", "options": [
            ("Solving puzzles", [1,0,0,0,0]),
            ("Drawing or writing", [0,1,0,0,0]),
            ("Building gadgets", [0,0,1,0,0]),
            ("Talking with people", [0,0,0,1,0])]},
        {"q": "What describes you best?", "options": [
            ("Logical thinker", [1,0,0,0,0]),
            ("Imaginative", [0,1,0,0,0]),
            ("Hands-on", [0,0,1,0,0]),
            ("Curious learner", [0,0,0,0,1])]},
        {"q": "Preferred project type?", "options": [
            ("Data analysis", [1,0,0,0,0]),
            ("Creative design", [0,1,0,0,0]),
            ("System building", [0,0,1,0,0]),
            ("Team leadership", [0,0,0,1,0])]},
        {"q": "You are praised for:", "options": [
            ("Problem solving", [1,0,0,0,0]),
            ("Original ideas", [0,1,0,0,0]),
            ("Technical skills", [0,0,1,0,0]),
            ("Communication", [0,0,0,1,0])]},
        {"q": "You prefer to:", "options": [
            ("Analyze data", [1,0,0,0,0]),
            ("Brainstorm", [0,1,0,0,0]),
            ("Assemble things", [0,0,1,0,0]),
            ("Teach others", [0,0,0,1,0])]},
        {"q": "Which is most appealing?", "options": [
            ("Finding patterns", [1,0,0,0,0]),
            ("Inventing", [0,1,0,0,0]),
            ("Engineering", [0,0,1,0,0]),
            ("Exploring new topics", [0,0,0,0,1])]},
        {"q": "You excel at:", "options": [
            ("Critical thinking", [1,0,0,0,0]),
            ("Artistic work", [0,1,0,0,0]),
            ("Technical tasks", [0,0,1,0,0]),
            ("Empathy", [0,0,0,1,0])]},
        {"q": "You value:", "options": [
            ("Accuracy", [1,0,0,0,0]),
            ("Innovation", [0,1,0,0,0]),
            ("Efficiency", [0,0,1,0,0]),
            ("Curiosity", [0,0,0,0,1])]},
        {"q": "Best describes your study style:", "options": [
            ("Structured", [1,0,0,0,0]),
            ("Experimental", [0,1,0,0,0]),
            ("Practical", [0,0,1,0,0]),
            ("Discussion-based", [0,0,0,1,0])]},
        {"q": "You are motivated by:", "options": [
            ("Solving challenges", [1,0,0,0,0]),
            ("Creating something new", [0,1,0,0,0]),
            ("Building systems", [0,0,1,0,0]),
            ("Learning new things", [0,0,0,0,1])]},
        {"q": "You prefer to work:", "options": [
            ("Independently", [1,0,0,0,0]),
            ("On creative tasks", [0,1,0,0,0]),
            ("With machines", [0,0,1,0,0]),
            ("With people", [0,0,0,1,0])]},
        {"q": "You are most interested in:", "options": [
            ("Data & logic", [1,0,0,0,0]),
            ("Design & arts", [0,1,0,0,0]),
            ("Technology", [0,0,1,0,0]),
            ("Exploring ideas", [0,0,0,0,1])]
        }
    ]
    quiz_answers = []
    with st.form("quiz_form"):
        for idx, q in enumerate(quiz_questions):
            options = [opt[0] for opt in q["options"]]
            answer = st.radio(q["q"], options, key=f"q{idx}")
            quiz_answers.append(answer)
        submitted = st.form_submit_button("Submit Quiz")
    if submitted:
        feature_vec = np.zeros(5)
        for idx, answer in enumerate(quiz_answers):
            for opt, vec in quiz_questions[idx]["options"]:
                if answer == opt:
                    feature_vec += np.array(vec)
        feature_vec = feature_vec / len(quiz_questions)
        conn = sqlite3.connect('data/career_advisor.db')
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO quiz_scores (user_id, analytical, creativity, engineering, communication, curiosity) VALUES (?, ?, ?, ?, ?, ?)''',
                  (user_id, float(feature_vec[0]), float(feature_vec[1]), float(feature_vec[2]), float(feature_vec[3]), float(feature_vec[4])))
        conn.commit()
        conn.close()
        st.success(f"Quiz submitted! Your feature vector: {np.round(feature_vec,2).tolist()}")
        st.stop()

def render_register():
    st.title("Register")
    with st.form("register_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        st.subheader("Skill Input")
        st.info("These are your current skills.\nCareer goal selection happens later based on recommendations.")
        experience = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Advanced"])
        goal = st.selectbox("Career Goal", ["First job", "Switch", "Promotion", "Higher studies"])
        hours_per_week = st.number_input("Time Availability (hours per week)", min_value=1, max_value=80, value=5)
        submitted = st.form_submit_button("Register")
    if submitted:
        if not (name and email and password):
            st.warning("Please fill all fields.")
        else:
            user_id = register_user(name, email, password, education, experience, goal, hours_per_week)
            if user_id:
                st.success("Registration successful! Please login.")
                set_page("Login")
                st.session_state['page'] = "Profile"
                st.stop()
            else:
                st.error("Email already registered.")
    st.stop()

def render_login():
    st.title("Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
    if submitted:
        user = check_login(email, password)
        if user:
            st.session_state['auth_user'] = user
            set_page("Profile")
            st.session_state['page'] = "Profile"
            st.stop()
        else:
            st.error("Invalid email or password.")
    if st.button("New user? Register here"):
        set_page("Register")
        st.session_state['page'] = "Register"
        st.rerun()
    st.stop()

def render_skill_input():
    require_auth()
    st.title("Skill Input")
    st.write("Input your current skills and proficiency levels. This section is about where you are now, not your career goal.")
    user_id = st.session_state['auth_user']['id']
    conn = sqlite3.connect('data/career_advisor.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_skills (
        user_id INTEGER,
        skill_name TEXT,
        user_level REAL,
        PRIMARY KEY (user_id, skill_name),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    c.execute('SELECT skill_name, user_level FROM user_skills WHERE user_id=?', (user_id,))
    existing_skills = c.fetchall()
    skill_levels = {"Not Known": 0.0, "Beginner": 0.3, "Intermediate": 0.6, "Advanced": 0.85}
    st.subheader("Your Skills")
    if existing_skills:
        for name, level in existing_skills:
            st.write(f"{name}: {level}")
    with st.form("skill_input_form"):
        new_skill = st.text_input("Skill Name")
        new_level = st.selectbox("Proficiency Level", list(skill_levels.keys()))
        submitted = st.form_submit_button("Add/Update Skill")
    if submitted and new_skill:
        c.execute('INSERT OR REPLACE INTO user_skills (user_id, skill_name, user_level) VALUES (?, ?, ?)',
                  (user_id, new_skill, skill_levels[new_level]))
        conn.commit()
        st.success(f"Skill '{new_skill}' updated!")
        st.rerun()
    conn.close()
    st.stop()

