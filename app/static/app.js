document.addEventListener('DOMContentLoaded', () => {
    initApiKeyHandling();
    initNavigation();
    loadDropdownOptions();
    initOverviewChart();
    initForms();
    initResumeUploadDropzone();
});

// Manage API Key in LocalStorage & UI
function getApiKey() {
    return localStorage.getItem('gemini_api_key') || '';
}

function initApiKeyHandling() {
    const keyInput = document.getElementById('global-api-key');
    const badge = document.getElementById('engine-status-badge');
    if (!keyInput) return;

    keyInput.value = getApiKey();
    updateBadge();

    keyInput.addEventListener('input', () => {
        localStorage.setItem('gemini_api_key', keyInput.value.trim());
        updateBadge();
    });

    function updateBadge() {
        if (keyInput.value.trim()) {
            badge.innerText = 'Gemini AI Active';
            badge.style.color = '#6ee7b7';
        } else {
            badge.innerText = 'Hybrid ML / AI';
            badge.style.color = 'var(--accent)';
        }
    }
}

// Navigation Handling
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const headerText = document.getElementById('header-text');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(n => n.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            item.classList.add('active');
            const tabId = item.getAttribute('data-tab');
            document.getElementById(`tab-${tabId}`).classList.add('active');
            headerText.innerText = item.innerText.trim();
        });
    });
}

function getApiBaseUrl() {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (isLocal) return '';
    const stored = localStorage.getItem('render_backend_url');
    return stored ? stored.replace(/\/$/, '') : 'https://ai-career-mentor-3z0j.onrender.com';
}

// Fetch Dynamic Dropdowns from FastAPI
async function loadDropdownOptions() {
    try {
        const res = await fetch(`${getApiBaseUrl()}/api/options`);
        const data = await res.json();

        populateSelect('sal-industry', data.industries);
        populateSelect('sal-jobtitle', data.job_titles);
        populateSelect('sal-edu', data.education_levels);
        
        populateSelect('car-edu', data.education_levels);
        populateSelect('sg-target', data.target_roles);
        populateSelect('rm-target', data.target_roles);
        populateSelect('int-role', data.job_titles);

    } catch (err) {
        console.error('Failed to load options:', err);
    }
}

function populateSelect(elemId, items) {
    const select = document.getElementById(elemId);
    if (!select || !items) return;
    select.innerHTML = '';
    items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item;
        opt.innerText = item;
        select.appendChild(opt);
    });
}

// Resume Dropzone Setup
function initResumeUploadDropzone() {
    const dropzone = document.getElementById('resume-dropzone');
    const fileInput = document.getElementById('resume-file-input');
    const badge = document.getElementById('file-info-badge');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.background = 'rgba(99, 102, 241, 0.2)';
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.style.background = 'rgba(99, 102, 241, 0.05)';
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.background = 'rgba(99, 102, 241, 0.05)';
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            handleFileUpload(fileInput.files[0]);
        }
    });

    async function handleFileUpload(file) {
        badge.style.display = 'block';
        badge.innerText = `Extracting text from: ${file.name}...`;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('target_job_title', document.getElementById('res-target').value);
        if (getApiKey()) formData.append('api_key', getApiKey());

        try {
            const res = await fetch(`${getApiBaseUrl()}/api/resume-upload`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (res.ok) {
                document.getElementById('res-text').value = data.extracted_preview || '';
                badge.innerText = `Uploaded: ${file.name} (${data.word_count} words extracted)`;
                renderResumeResult(data);
            } else {
                badge.innerText = `Error: ${data.error || 'Failed to parse file.'}`;
            }
        } catch (err) {
            badge.innerText = `Upload failed: ${err.message}`;
        }
    }
}

function renderResumeResult(data) {
    const box = document.getElementById('resume-result');
    box.style.display = 'block';
    box.innerHTML = `
        <div style="font-size: 11px; color: var(--secondary); margin-bottom: 6px;">Evaluated via: ${data.source || 'AI Engine'}</div>
        <div style="display: flex; gap: 20px; align-items: center; margin-bottom: 15px;">
            <div>
                <div style="font-size: 12px; color: var(--text-muted);">ATS Compatibility</div>
                <div class="score-badge">${data.ats_score}/100</div>
            </div>
            <div>
                <div style="font-size: 12px; color: var(--text-muted);">Overall Rating</div>
                <div style="font-size: 20px; font-weight: 700; color: var(--accent);">${data.overall_rating}</div>
            </div>
        </div>
        <p style="font-size: 13px; color: #6ee7b7; margin-bottom: 8px;"><strong>Strengths:</strong> ${data.strengths}</p>
        <p style="font-size: 13px; color: #fca5a5; margin-bottom: 8px;"><strong>Areas to Improve:</strong> ${data.weaknesses}</p>
        <p style="font-size: 13px; color: var(--text-muted);"><strong>Action Plan:</strong> ${data.improvement_suggestions}</p>
    `;
}

// Overview Chart
let overviewChartInstance = null;
function initOverviewChart() {
    const ctx = document.getElementById('overviewChart');
    if (!ctx) return;
    overviewChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Data Science', 'IT & Dev', 'Engineering', 'Sales & Marketing', 'Management'],
            datasets: [{
                data: [30, 25, 20, 15, 10],
                backgroundColor: ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'right', labels: { color: '#9ca3af' } }
            }
        }
    });
}

let salaryChartInstance = null;

// Form Logic
function initForms() {
    // 1. Salary Form
    document.getElementById('salary-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            industry: document.getElementById('sal-industry').value,
            job_title: document.getElementById('sal-jobtitle').value,
            years_experience: parseFloat(document.getElementById('sal-exp').value),
            education_level: document.getElementById('sal-edu').value
        };

        const res = await fetch(`${getApiBaseUrl()}/api/salary-prediction`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        document.getElementById('sal-out-val').innerText = data.formatted_salary_inr;
        document.getElementById('sal-out-usd').innerText = `Equivalent USD: ${data.formatted_salary_usd}`;
        document.getElementById('sal-out-range').innerText = data.range_inr;
        document.getElementById('salary-result').style.display = 'block';

        const minLakhs = (data.min_salary_inr / 100000).toFixed(2);
        const predLakhs = (data.predicted_salary_inr / 100000).toFixed(2);
        const maxLakhs = (data.max_salary_inr / 100000).toFixed(2);

        const sCtx = document.getElementById('salaryChart');
        if (salaryChartInstance) salaryChartInstance.destroy();
        salaryChartInstance = new Chart(sCtx, {
            type: 'bar',
            data: {
                labels: ['Min Est.', 'Predicted', 'Max Est.'],
                datasets: [{
                    label: 'Salary (₹ Lakhs)',
                    data: [minLakhs, predLakhs, maxLakhs],
                    backgroundColor: ['rgba(6, 182, 212, 0.5)', 'rgba(99, 102, 241, 0.8)', 'rgba(16, 185, 129, 0.5)'],
                    borderRadius: 6
                }]
            },
            options: {
                plugins: { legend: { display: true, labels: { color: '#9ca3af' } } },
                scales: {
                    y: { ticks: { color: '#9ca3af', callback: (val) => '₹' + val + ' L' } },
                    x: { ticks: { color: '#9ca3af' } }
                }
            }
        });
    });

    // 2. Career Recommendation Form
    document.getElementById('career-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            education_level: document.getElementById('car-edu').value,
            years_experience: parseFloat(document.getElementById('car-exp').value),
            work_style: document.getElementById('car-style').value,
            interests: document.getElementById('car-interests').value,
            current_skills: document.getElementById('car-skills').value
        };

        const res = await fetch(`${getApiBaseUrl()}/api/career-recommendation`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        const box = document.getElementById('career-result');
        box.style.display = 'block';
        box.innerHTML = '';

        data.all_matches.forEach((item, idx) => {
            box.innerHTML += `
                <div style="margin-bottom: 16px; padding: 14px; background: rgba(255,255,255,0.03); border-radius: 8px; border-left: 3px solid var(--primary);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="color: #fff;">#${idx+1} ${item.career_title}</h4>
                        <span class="tag" style="background: rgba(16, 185, 129, 0.2); color: #6ee7b7;">${item.match_score}% Match</span>
                    </div>
                    <p style="font-size: 13px; color: var(--text-muted); margin-top: 6px;">${item.reasoning}</p>
                    <div style="font-size: 12px; color: var(--secondary); margin-top: 6px;">Alternative: ${item.alternative_recommendation}</div>
                </div>
            `;
        });
    });

    // 3. Skill Gap Form
    document.getElementById('skillgap-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            current_role: document.getElementById('sg-current').value,
            target_role: document.getElementById('sg-target').value,
            current_skills: document.getElementById('sg-skills').value
        };

        const res = await fetch(`${getApiBaseUrl()}/api/skill-gap`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        const box = document.getElementById('skillgap-result');
        box.style.display = 'block';
        box.innerHTML = `
            <div style="display: flex; gap: 20px; align-items: center; margin-bottom: 15px;">
                <div>
                    <div style="font-size: 12px; color: var(--text-muted);">Readiness Score</div>
                    <div class="score-badge">${data.readiness_percentage}%</div>
                </div>
                <div>
                    <div style="font-size: 12px; color: var(--text-muted);">Est. Months to Bridge</div>
                    <div style="font-size: 24px; font-weight: 700; color: var(--secondary);">${data.estimated_months_to_close_gap} Months</div>
                </div>
            </div>
            <div style="margin-bottom: 12px;">
                <label style="font-size: 13px; color: var(--text-muted);">Missing Critical Skills:</label>
                <div class="tag-list">
                    ${data.missing_skills.map(s => `<span class="tag tag-danger">${s}</span>`).join('')}
                </div>
            </div>
            <div style="font-size: 13px; color: var(--text-main); background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px;">
                <strong>Recommended Learning Strategy:</strong><br>${data.recommended_resources}
            </div>
        `;
    });

    // 4. Roadmap Form
    document.getElementById('roadmap-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            current_role: document.getElementById('rm-current').value,
            target_role: document.getElementById('rm-target').value,
            weekly_hours: parseInt(document.getElementById('rm-hours').value),
            api_key: getApiKey()
        };

        const res = await fetch(`${getApiBaseUrl()}/api/roadmap`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        const box = document.getElementById('roadmap-result');
        box.style.display = 'block';

        const phasesHtml = (data.phases || []).map((p, idx) => `
            <div class="timeline-step" style="background: rgba(255,255,255,0.02); padding: 14px; border-radius: 8px; margin-bottom: 16px;">
                <div style="font-size: 15px; font-weight: 700; color: var(--secondary);">${p.phase_name || 'Phase ' + (idx+1)}</div>
                <div style="font-size: 13px; color: var(--text-muted); margin: 6px 0;">${p.description || ''}</div>
                
                ${p.key_skills ? `
                    <div style="margin: 8px 0;">
                        <span style="font-size: 11px; color: var(--text-muted);">Skills:</span>
                        <div class="tag-list" style="margin-top: 4px;">
                            ${(p.key_skills || []).map(sk => `<span class="tag">${sk}</span>`).join('')}
                        </div>
                    </div>
                ` : ''}

                ${p.recommended_resources ? `
                    <div style="font-size: 12px; color: var(--accent); margin-top: 6px;">
                        <i class="fa-solid fa-book-open"></i> <strong>Resources:</strong> ${p.recommended_resources}
                    </div>
                ` : ''}

                ${p.project_idea ? `
                    <div style="font-size: 12px; color: #a5b4fc; background: rgba(99,102,241,0.1); padding: 8px; border-radius: 6px; margin-top: 8px;">
                        <i class="fa-solid fa-laptop-code"></i> <strong>Portfolio Project:</strong> ${p.project_idea}
                    </div>
                ` : ''}
            </div>
        `).join('');

        const milestonesHtml = (data.milestones || []).map(m => `
            <li style="font-size: 12px; color: var(--text-bright); margin-bottom: 4px;"><i class="fa-solid fa-flag-checkered" style="color: var(--warning);"></i> ${m}</li>
        `).join('');

        box.innerHTML = `
            <div style="font-size: 11px; color: var(--accent); margin-bottom: 8px;">Generated via: ${data.source || 'AI Mentor'}</div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px;">
                <span class="tag" style="background: rgba(99, 102, 241, 0.2); color: #a5b4fc; font-size: 13px;"><i class="fa-solid fa-clock"></i> Duration: ${data.total_duration_months} Months</span>
                <span class="tag" style="background: rgba(6, 182, 212, 0.2); color: #67e8f9; font-size: 13px;"><i class="fa-solid fa-certificate"></i> Certification: ${data.target_certification}</span>
                <span class="tag" style="background: rgba(16, 185, 129, 0.2); color: #6ee7b7; font-size: 13px;"><i class="fa-solid fa-signal"></i> Level: ${data.difficulty_level}</span>
            </div>
            
            <h4 style="color: #fff; margin-bottom: 12px;"><i class="fa-solid fa-route"></i> Actionable Learning Phases</h4>
            ${phasesHtml}

            ${milestonesHtml ? `
                <div style="margin-top: 16px; padding: 12px; background: rgba(0,0,0,0.3); border-radius: 8px;">
                    <h5 style="color: var(--warning); font-size: 13px; margin-bottom: 8px;">Key Target Milestones:</h5>
                    <ul style="list-style: none;">${milestonesHtml}</ul>
                </div>
            ` : ''}

            ${data.career_tips ? `
                <div style="margin-top: 12px; font-size: 12px; color: var(--text-muted); border-left: 3px solid var(--secondary); padding-left: 10px;">
                    <strong>Mentor Career Advice:</strong> ${data.career_tips}
                </div>
            ` : ''}
        `;
    });

    // 5. Resume Text Form
    document.getElementById('resume-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            target_job_title: document.getElementById('res-target').value,
            resume_text: document.getElementById('res-text').value,
            api_key: getApiKey()
        };

        const res = await fetch(`${getApiBaseUrl()}/api/resume-analysis`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        renderResumeResult(data);
    });

    // 6. Interview Question Fetch & Answer Evaluation
    document.getElementById('interview-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            job_title: document.getElementById('int-role').value
        };

        const res = await fetch(`${getApiBaseUrl()}/api/interview-prep`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        const box = document.getElementById('interview-result');
        box.style.display = 'block';
        box.innerHTML = data.questions.map((q, idx) => `
            <div style="margin-bottom: 16px; padding: 12px; background: rgba(255,255,255,0.03); border-radius: 8px; border-left: 3px solid var(--secondary); cursor: pointer;" onclick="selectQuestionForPractice('${q.question_text.replace(/'/g, "\\'")}')">
                <div style="font-size: 12px; color: var(--text-muted); display:flex; justify-content:space-between;">
                    <span>Q${idx+1} [${q.question_type} - ${q.difficulty_level}]</span>
                    <span style="color: var(--accent);"><i class="fa-solid fa-hand-pointer"></i> Practice This</span>
                </div>
                <div style="font-size: 14px; font-weight: 600; color: #fff; margin: 6px 0;">${q.question_text}</div>
                <div style="font-size: 12px; color: var(--text-muted);">Key Evaluation: ${q.key_evaluation_points}</div>
            </div>
        `).join('');

        if (data.questions.length) {
            selectQuestionForPractice(data.questions[0].question_text);
        }
    });

    // Tagda AI Answer Evaluation Form
    document.getElementById('answer-eval-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const qText = document.getElementById('eval-q-text').value;
        const candAnswer = document.getElementById('eval-cand-answer').value;
        const jobTitle = document.getElementById('int-role').value;

        if (!candAnswer.strip && candAnswer.trim() === '') {
            alert('Please type your interview answer first!');
            return;
        }

        const payload = {
            job_title: jobTitle,
            question_text: qText,
            candidate_answer: candAnswer,
            api_key: getApiKey()
        };

        const res = await fetch(`${getApiBaseUrl()}/api/interview-evaluate`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        const box = document.getElementById('answer-eval-result');
        box.style.display = 'block';
        box.innerHTML = `
            <div style="font-size: 11px; color: var(--accent); margin-bottom: 6px;">Evaluated via: ${data.source || 'AI Engine'}</div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div>
                    <div style="font-size: 12px; color: var(--text-muted);">Answer Score</div>
                    <div class="score-badge" style="font-size: 32px;">${data.score_out_of_10} / 10</div>
                </div>
                <div class="tag" style="background: rgba(16,185,129,0.2); color:#6ee7b7; font-size:14px; padding:6px 14px;">${data.performance_tier}</div>
            </div>
            <p style="font-size: 13px; color: #6ee7b7; margin-bottom: 6px;"><strong>Strengths:</strong> ${data.strengths}</p>
            <p style="font-size: 13px; color: #fca5a5; margin-bottom: 6px;"><strong>Missing Key Points:</strong> ${data.missing_key_points}</p>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 10px;"><strong>Feedback:</strong> ${data.constructive_feedback}</p>
            <div style="font-size: 13px; background: rgba(0,0,0,0.4); padding: 12px; border-radius: 8px; border-left: 3px solid var(--secondary);">
                <strong style="color: var(--secondary);">Model Answer:</strong><br>${data.ideal_model_answer}
            </div>
        `;
    });

    // 7. LinkedIn Form
    document.getElementById('linkedin-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            linkedin_url: document.getElementById('li-url').value,
            headline: document.getElementById('li-headline').value,
            summary_text: document.getElementById('li-summary-text').value,
            api_key: getApiKey()
        };

        const res = await fetch(`${getApiBaseUrl()}/api/linkedin-review`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        const box = document.getElementById('linkedin-result');
        box.style.display = 'block';
        box.innerHTML = `
            <div style="display: flex; gap: 20px; align-items: center; margin-bottom: 15px;">
                <div>
                    <div style="font-size: 12px; color: var(--text-muted);">Completeness Score</div>
                    <div class="score-badge">${data.profile_completeness_score}%</div>
                </div>
                <div>
                    <div style="font-size: 12px; color: var(--text-muted);">Rating</div>
                    <div style="font-size: 20px; font-weight: 700; color: var(--secondary);">${data.review_rating}</div>
                </div>
            </div>
            <p style="font-size: 13px; margin-bottom: 8px;"><strong>Strengths:</strong> ${data.strengths}</p>
            <p style="font-size: 13px; color: #fca5a5; margin-bottom: 8px;"><strong>Weaknesses:</strong> ${data.weaknesses}</p>
            <p style="font-size: 13px; color: var(--text-muted);"><strong>Tips:</strong> ${data.improvement_suggestions}</p>
        `;
    });

    // 8. Live GitHub Form
    document.getElementById('github-live-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const userInput = document.getElementById('gh-input-username').value;
        if (!userInput.trim()) return;

        const payload = {
            username_or_url: userInput,
            api_key: getApiKey()
        };

        const res = await fetch(`${getApiBaseUrl()}/api/github-live-review`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        const box = document.getElementById('github-result');
        box.style.display = 'block';

        if (!res.ok) {
            box.innerHTML = `<div style="color: var(--danger); font-size: 14px;">Error: ${data.error}</div>`;
            return;
        }

        const metrics = data.raw_metrics || {};
        const devScore = data.developer_score || data.profile_score || 75;
        const devTier = data.developer_tier || data.review_rating || 'Active Contributor';
        const codeGrade = data.code_quality_grade || 'A';
        const topTechs = data.top_technologies || metrics.top_languages || [];

        box.innerHTML = `
            <div style="font-size: 11px; color: var(--accent); margin-bottom: 8px;">Evaluated via: ${data.source || 'Live GitHub API'}</div>
            <div style="display: flex; gap: 16px; align-items: center; margin-bottom: 15px; background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px;">
                ${metrics.avatar_url ? `<img src="${metrics.avatar_url}" style="width: 54px; height: 54px; border-radius: 50%; border: 2px solid var(--accent);">` : ''}
                <div>
                    <h3 style="color: #fff; margin-bottom: 2px;">${metrics.full_name || metrics.github_username}</h3>
                    <div style="font-size: 13px; color: var(--text-muted);"><i class="fa-brands fa-github"></i> @${metrics.github_username}</div>
                    ${metrics.bio ? `<div style="font-size: 12px; color: var(--text-bright); margin-top: 4px;">"${metrics.bio}"</div>` : ''}
                </div>
            </div>

            <div style="display: flex; flex-wrap: wrap; gap: 16px; align-items: center; margin-bottom: 16px;">
                <div>
                    <div style="font-size: 11px; color: var(--text-muted);">Developer Score</div>
                    <div class="score-badge" style="font-size: 28px;">${devScore} <span style="font-size:14px; color:var(--text-muted);">/ 100</span></div>
                </div>
                <div>
                    <div style="font-size: 11px; color: var(--text-muted);">Code Grade</div>
                    <div style="font-size: 24px; font-weight: 800; color: #6ee7b7;">${codeGrade}</div>
                </div>
                <div>
                    <div style="font-size: 11px; color: var(--text-muted);">Developer Tier</div>
                    <div style="font-size: 15px; font-weight: 700; color: var(--secondary);">${devTier}</div>
                </div>
            </div>

            <div class="tag-list" style="margin-bottom: 14px;">
                <span class="tag" style="background: rgba(46,164,79,0.2); color:#6ee7b7;"><i class="fa-solid fa-code-fork"></i> Repos: ${metrics.public_repos}</span>
                <span class="tag" style="background: rgba(245,158,11,0.2); color:#fcd34d;"><i class="fa-solid fa-star"></i> Stars: ${metrics.total_stars}</span>
                <span class="tag" style="background: rgba(99,102,241,0.2); color:#a5b4fc;"><i class="fa-solid fa-users"></i> Followers: ${metrics.followers}</span>
                <span class="tag" style="background: rgba(6,182,212,0.2); color:#67e8f9;"><i class="fa-solid fa-fire"></i> Top Repo: ${metrics.top_repository}</span>
            </div>

            ${topTechs.length ? `
                <div style="margin-bottom: 12px;">
                    <span style="font-size: 12px; color: var(--text-muted);">Detected Technologies:</span>
                    <div class="tag-list" style="margin-top: 4px;">
                        ${topTechs.map(t => `<span class="tag" style="background: rgba(255,255,255,0.06); color:#fff;">${t}</span>`).join('')}
                    </div>
                </div>
            ` : ''}

            <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; font-size: 13px; line-height: 1.6;">
                <p style="margin-bottom: 8px; color: #6ee7b7;"><strong><i class="fa-solid fa-circle-check"></i> Strengths:</strong> ${data.strengths}</p>
                <p style="margin-bottom: 8px; color: #fca5a5;"><strong><i class="fa-solid fa-circle-exclamation"></i> Gaps & Weaknesses:</strong> ${data.weaknesses}</p>
                <p style="color: var(--text-bright);"><strong><i class="fa-solid fa-lightbulb" style="color:var(--warning);"></i> Actionable Growth Roadmap:</strong> ${data.improvement_suggestions}</p>
            </div>
        `;
    });
}

function selectQuestionForPractice(qText) {
    const input = document.getElementById('eval-q-text');
    if (input) {
        input.value = qText;
        document.getElementById('eval-cand-answer').focus();
    }
}
