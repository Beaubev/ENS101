const STORAGE_KEY = 'ens101-mentor-desk-appointment-1a-v2';

const WORKFLOW = [
  {
    id: 'begin', label: 'Begin', short: 'Welcome and set direction', duration: '3–5 min',
    title: 'Begin the appointment',
    description: 'Open warmly, follow the prayer direction in the Appointment 1a guide, and learn the student’s major and career direction.',
    tasks: [
      { id: 'begin-prayer', title: 'Open with prayer', detail: 'Follow the appointment guideline and your department’s current practice.' },
      { id: 'begin-major', title: 'Confirm the student’s major', detail: 'Enter the major or program above so later guidance is specific.' },
      { id: 'begin-career', title: 'Ask about the student’s career direction', detail: 'Capture a short role or field—not sensitive personal information.' }
    ],
    prompts: ['What is your major?', 'What type of career do you see yourself doing when you graduate?'],
    copilot: ['Give me a warm opening', 'Explain Appointment 1a', 'Suggest a career question']
  },
  {
    id: 'ensign-connect', label: 'Ensign Connect', short: 'Join and explore the network', duration: '10–12 min',
    title: 'Set up Ensign Connect',
    description: 'Help the student join Ensign Connect, find the group for their major, set notification preferences, and see how to connect with alumni.',
    tasks: [
      { id: 'connect-join', title: 'Open Ensign Connect and complete “Join Now”', detail: 'Use Ensign Connect Web Access, then help the student sign up.', action: { label: 'Open Ensign Connect', url: 'https://ces.peoplegrove.com/hub/ces/organizations/ensign-connect' } },
      { id: 'connect-group', title: 'Join the group for the student’s major', detail: 'Choose Ensign College under Schools, open Groups, and select the matching major.', action: { label: 'Browse Ensign groups', url: 'https://ces.peoplegrove.com/hub/ces/groups?organization=19963' } },
      { id: 'connect-features', title: 'Point out Members, Discussion, and Join', detail: 'Show the blue Members and Discussion links and the green Join control.' },
      { id: 'connect-notifications', title: 'Review email and SMS preferences', detail: 'Open My Preferences and let the student choose which notifications to turn on or off.', action: { label: 'Open My Preferences', url: 'https://ces.peoplegrove.com/preferences/notifications' } },
      { id: 'connect-community', title: 'Explore alumni and community members', detail: 'Show how the student can view alumni profiles and send an appropriate message.', action: { label: 'Explore the community', url: 'https://ces.peoplegrove.com/hub/ces/person' } },
      { id: 'connect-interview', title: 'Review Informational Interview questions', detail: 'Go over Informational Interview handout and review questions on the back.', action: { label: 'Open Informational Interview handout', url: '/resources/informational-interview-handout.pdf' } },
      { id: 'connect-certificates', title: 'Connect certificates to opportunities', detail: 'Explain how certificate courses can strengthen preparation for internships and employment.' }
    ],
    prompts: ['Which major group should we join?', 'Who is one alumnus whose career path you would like to learn about?', 'What could you ask in an informational interview?'],
    copilot: ['Walk me through Ensign Connect', 'Draft an alumni message', 'Suggest interview questions']
  },
  {
    id: 'internship', label: 'Internship plan', short: 'Requirements and timing', duration: '8–10 min',
    title: 'Build an internship plan',
    description: 'Give the student a clear overview of the degree internship requirement, preparation timeline, course pairing, and where to verify special circumstances.',
    tasks: [
      { id: 'internship-requirement', title: 'Explain the degree internship requirement', detail: 'The internship should relate to the student’s major; review the current internship information together.' },
      { id: 'internship-course', title: 'Explain the accompanying internship course', detail: 'The student will enroll in the appropriate internship class at the same time. Verify the current course with the student’s program.' },
      { id: 'internship-international', title: 'Flag international-student planning', detail: 'Do not give immigration advice. Help international students verify current vacation-semester and work-authorization rules with the International Student Office.', action: { label: 'International Student Office', url: 'https://www.ensign.edu/international-students' } },
      { id: 'internship-pbwe', title: 'Explain the PBWE option carefully', detail: 'For on-campus students, CAR 398 PBWE provides real-world project experience and résumé value.' },
      { id: 'internship-timeline', title: 'Discuss application timing', detail: 'Large-company internships may recruit 6–9 months ahead; encourage early research.' },
      { id: 'internship-car201', title: 'Encourage early CAR 201 preparation', detail: 'The guide recommends taking CAR 201 as soon as appropriate so the student is ready when internships open.' }
    ],
    prompts: ['How could an internship connect to the career you want?', 'When would you need to begin applying?', 'What experience would help you feel ready?'],
    copilot: ['Explain the internship timeline', 'Compare CAR 398, 399, and 499', 'Give an international-student caution']
  },
  {
    id: 'career-direction', label: 'Career direction', short: 'Confidence and next appointment', duration: '6–8 min',
    title: 'Choose the right career next step',
    description: 'Use the 1–10 confidence question and Career Explorer roadmap status to decide whether the next appointment should focus on exploration or résumé creation.',
    tasks: [
      { id: 'career-confidence', title: 'Ask the 1–10 confidence question', detail: 'Update the confidence slider above: 1 means very unsure and 10 means very confident.' },
      { id: 'career-pathwayu', title: 'Check Career Explorer roadmap progress', detail: 'Ask whether the student completed the PathwayU roadmap assessments and update the status above.', action: { label: 'Open Career Explorer', url: 'https://ensign.pathwayu.com/login?next=%2Fresults' } },
      { id: 'career-followup', title: 'Choose the next appointment type', detail: 'If the student is still exploring, plan a Career Explorer appointment. If confident, plan a Create Resume appointment.' },
      { id: 'career-roadmap2', title: 'If scheduling Create Resume appointment, show Roadmap 2, Steps 1-5', detail: 'Make sure the student knows what to complete before the next appointment.' },
      { id: 'career-action', title: 'Record a specific student action', detail: 'Add the agreed action and time frame in the appointment record below.' }
    ],
    prompts: ['On a scale of 1–10, how sure are you about this career direction?', 'Have you completed the Career Explorer roadmap assessments?', 'What will you complete before our next appointment?'],
    copilot: ['Recommend the next appointment', 'Explain Career Explorer', 'Draft a student action step']
  },
  {
    id: 'complete', label: 'Complete', short: 'Next step and selfie', duration: '2–4 min',
    title: 'Complete the appointment',
    description: 'Confirm the agreed next actions and finish the page 1 appointment checklist.',
    tasks: [
      { id: 'close-nextsteps', title: 'Confirm both next steps', detail: 'Read back the student action and mentor follow-up recorded below.' },
      { id: 'close-selfie', title: 'Take the appointment selfie', detail: 'Follow the Appointment 1a practice and obtain the student’s consent before taking or using a photo.' }
    ],
    prompts: ['What is the first step you will take after today?', 'What support would you like from me?', 'When will you complete your next step?'],
    copilot: ['Summarize next steps', 'Draft a follow-up message', 'Give me a closing question']
  }
];

const RESOURCES = [
  { id: 'connect', name: 'Ensign Connect', initials: 'EC', category: 'Appointment 1a', url: 'https://ces.peoplegrove.com/hub/ces/organizations/ensign-connect', description: 'Join Ensign Connect and access the student’s professional community.' },
  { id: 'groups', name: 'Ensign Major Groups', initials: 'G', category: 'Appointment 1a', url: 'https://ces.peoplegrove.com/hub/ces/groups?organization=19963', description: 'Find and join the Ensign College group for the student’s major.' },
  { id: 'preferences', name: 'Connect Preferences', initials: 'N', category: 'Appointment 1a', url: 'https://ces.peoplegrove.com/preferences/notifications', description: 'Review Ensign Connect email and SMS notification choices.' },
  { id: 'community', name: 'Explore the Community', initials: 'A', category: 'Appointment 1a', url: 'https://ces.peoplegrove.com/hub/ces/person', description: 'Browse alumni profiles and identify people for informational interviews.' },
  { id: 'informational-interview', name: 'Informational Interview Handout', initials: 'II', category: 'Appointment 1a', url: '/resources/informational-interview-handout.pdf', description: 'Review the informational interview guidance and the questions on the back.' },
  { id: 'pathwayu', name: 'Career Explorer', initials: 'CE', category: 'Career Planning', url: 'https://ensign.pathwayu.com/login?next=%2Fresults', description: 'Open PathwayU career assessments and roadmap results.' },
  { id: 'international', name: 'International Students', initials: 'IS', category: 'Support', url: 'https://www.ensign.edu/international-students', description: 'Official help for work authorization and international-student questions.' },
  { id: 'office', name: 'Career Explorer AI', initials: 'AI', category: 'Career Planning', url: 'https://portal.office.com/', description: 'Open Microsoft 365 to access the Career Explorer AI assistant.' },
  { id: 'canvas', name: 'Canvas', initials: 'C', category: 'Academic', url: 'https://ensign.instructure.com/', description: 'ENS 101 course materials, assignments, announcements, and grades.' },
  { id: 'career', name: 'Career & Internship Services', initials: 'CS', category: 'Career Planning', url: 'https://www.ensign.edu/CIS', description: 'Career preparation, internships, résumés, interviews, and networking.' }
];

const defaultState = () => ({
  currentStep: 0, checked: {},
  student: { name: '', program: '', career: '', confidence: '5', roadmap: '', followup: '' },
  notes: '', studentNext: '', mentorFollow: '', chatHistory: []
});

let state = loadState();
let activeResourceFilter = 'All';
let saveTimer;
let toastTimer;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    return { ...defaultState(), ...saved, student: { ...defaultState().student, ...(saved?.student || {}) } };
  } catch { return defaultState(); }
}

function persistState() {
  $('#save-status').textContent = 'Saving…';
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    $('#save-status').textContent = 'Saved locally';
  }, 250);
}

function totalTasks() { return WORKFLOW.reduce((sum, step) => sum + step.tasks.length, 0); }
function completedTasks() { return Object.values(state.checked).filter(Boolean).length; }
function stepComplete(step) { return step.tasks.every(task => state.checked[task.id]); }

function renderWorkflow() {
  const nav = $('#workflow-nav');
  nav.innerHTML = '';
  WORKFLOW.forEach((step, index) => {
    const button = document.createElement('button');
    const complete = stepComplete(step);
    button.type = 'button';
    button.className = `workflow-button${index === state.currentStep ? ' active' : ''}${complete ? ' complete' : ''}`;
    button.setAttribute('aria-current', index === state.currentStep ? 'step' : 'false');
    button.innerHTML = `<span class="workflow-num">${complete ? '✓' : index + 1}</span><span class="workflow-label"><strong>${step.label}</strong><small>${step.short}</small></span>${complete ? '<span class="workflow-check">✓</span>' : ''}`;
    button.addEventListener('click', () => { state.currentStep = index; persistState(); renderStep(); window.scrollTo({ top: 0, behavior: 'smooth' }); });
    nav.appendChild(button);
  });
  renderProgress();
}

function renderProgress() {
  const complete = completedTasks();
  const total = totalTasks();
  const percentage = Math.round((complete / total) * 100);
  $('#progress-label').textContent = `${percentage}% complete`;
  $('#progress-count').textContent = `${complete} of ${total}`;
  $('#progress-bar').style.width = `${percentage}%`;
}

function renderStep() {
  const step = WORKFLOW[state.currentStep];
  $('#step-title').textContent = step.title;
  $('#step-description').textContent = step.description;
  $('#step-duration').textContent = `Suggested time · ${step.duration}`;
  $('#step-kicker').textContent = `Step ${state.currentStep + 1} of ${WORKFLOW.length}`;
  $('#previous-step').disabled = state.currentStep === 0;
  $('#previous-step').style.visibility = state.currentStep === 0 ? 'hidden' : 'visible';
  $('#next-step').textContent = state.currentStep === WORKFLOW.length - 1 ? 'Finish appointment' : 'Continue';

  const list = $('#task-list');
  list.innerHTML = '';
  step.tasks.forEach(task => {
    const item = document.createElement('div');
    const checked = Boolean(state.checked[task.id]);
    item.className = `task-item${checked ? ' checked' : ''}`;
    const action = task.action ? `<a class="task-action" href="${task.action.url}" target="_blank" rel="noopener">${task.action.label}<svg viewBox="0 0 24 24"><path d="M14 5h5v5M10 14 19 5"/><path d="M19 13v6H5V5h6"/></svg></a>` : '';
    item.innerHTML = `<button class="task-check" type="button" aria-label="${checked ? 'Mark incomplete' : 'Mark complete'}: ${task.title}"><svg viewBox="0 0 24 24"><path d="m5 12 4 4L19 6"/></svg></button><div class="task-copy"><strong>${task.title}</strong><p>${task.detail}</p>${action}</div>`;
    item.querySelector('button').addEventListener('click', () => {
      state.checked[task.id] = !checked;
      persistState(); renderStep();
    });
    list.appendChild(item);
  });
  const done = step.tasks.filter(task => state.checked[task.id]).length;
  $('#step-task-count').textContent = `${done}/${step.tasks.length} complete`;

  const prompts = $('#conversation-prompts');
  prompts.innerHTML = '';
  step.prompts.forEach(text => {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'prompt-button'; button.textContent = text;
    button.addEventListener('click', () => copyText(text, 'Question copied'));
    prompts.appendChild(button);
  });
  renderCopilotSuggestions();
  renderWorkflow();
}

function renderQuickTools() {
  const tools = RESOURCES.filter(resource => ['connect', 'pathwayu', 'office', 'community'].includes(resource.id));
  $('#quick-tool-list').innerHTML = tools.map(resource => `<a class="quick-tool" href="${resource.url}" target="_blank" rel="noopener"><span class="quick-tool-icon">${resource.initials}</span><strong>${resource.name}</strong></a>`).join('');
}

function renderResources() {
  const categories = ['All', ...new Set(RESOURCES.map(resource => resource.category))];
  $('#resource-filters').innerHTML = '';
  categories.forEach(category => {
    const button = document.createElement('button');
    button.type = 'button'; button.className = `filter-button${category === activeResourceFilter ? ' active' : ''}`; button.textContent = category;
    button.addEventListener('click', () => { activeResourceFilter = category; renderResources(); });
    $('#resource-filters').appendChild(button);
  });
  const query = $('#resource-search').value.trim().toLowerCase();
  const filtered = RESOURCES.filter(resource => {
    const matchesFilter = activeResourceFilter === 'All' || resource.category === activeResourceFilter;
    const haystack = `${resource.name} ${resource.description} ${resource.category}`.toLowerCase();
    return matchesFilter && haystack.includes(query);
  });
  $('#resource-grid').innerHTML = filtered.length ? filtered.map(resource => `
    <a class="resource-card card" href="${resource.url}" target="_blank" rel="noopener">
      <div class="resource-top"><span class="resource-icon">${resource.initials}</span><svg class="resource-external" viewBox="0 0 24 24"><path d="M14 5h5v5M10 14 19 5"/><path d="M19 13v6H5V5h6"/></svg></div>
      <h2>${resource.name}</h2><p>${resource.description}</p><span class="resource-category${resource.category === 'Appointment 1a' ? ' appointment-label' : ''}">${resource.category}</span>
    </a>`).join('') : '<div class="resource-empty card"><strong>No matching resources</strong><p>Try a different search or category.</p></div>';
}

function showView(viewName) {
  $$('.view').forEach(view => view.classList.toggle('active', view.id === `${viewName}-view`));
  $$('.top-nav-button').forEach(button => button.classList.toggle('active', button.dataset.view === viewName));
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function bindSessionFields() {
  const fields = [
    ['#student-name', 'name'], ['#student-program', 'program'], ['#career-direction', 'career'],
    ['#career-confidence', 'confidence'], ['#roadmap-status', 'roadmap'], ['#followup-track', 'followup']
  ];
  fields.forEach(([selector, key]) => {
    const element = $(selector); element.value = state.student[key];
    element.addEventListener('input', () => { state.student[key] = element.value; updateRecommendation(); persistState(); });
  });
  [['#session-notes', 'notes'], ['#student-next-step', 'studentNext'], ['#mentor-follow-up', 'mentorFollow']].forEach(([selector, key]) => {
    const element = $(selector); element.value = state[key];
    element.addEventListener('input', () => { state[key] = element.value; persistState(); });
  });
  updateRecommendation();
}

function updateRecommendation() {
  const confidence = Number(state.student.confidence || 5);
  $('#confidence-output').textContent = confidence;
  const recommendation = confidence <= 5
    ? '<strong>Suggested direction:</strong> The student may benefit from a Career Explorer follow-up after completing the PathwayU roadmap.'
    : confidence <= 7
      ? '<strong>Discuss both options:</strong> Clarify the student’s career direction, then choose Career Explorer or Create Resume together.'
      : '<strong>Suggested direction:</strong> If the student remains confident after discussion, consider a Create Resume appointment.';
  $('#followup-recommendation').innerHTML = `${recommendation}<span>The mentor makes the final decision with the student.</span>`;
}

function buildSummary() {
  const completedLabels = WORKFLOW.flatMap(step => step.tasks).filter(task => state.checked[task.id]).map(task => `- ${task.title}`).join('\n');
  return `ENS 101 APPOINTMENT 1a SUMMARY\n\nStudent preferred name: ${state.student.name || 'Not entered'}\nMajor or program: ${state.student.program || 'Not entered'}\nCareer direction: ${state.student.career || 'Not entered'}\nCareer confidence: ${state.student.confidence || '5'}/10\nCareer Explorer roadmap: ${state.student.roadmap || 'Not selected'}\nNext appointment: ${state.student.followup || 'Not selected'}\n\nCONVERSATION NOTES\n${state.notes || 'No notes entered.'}\n\nSTUDENT NEXT STEP\n${state.studentNext || 'Not entered.'}\n\nMENTOR FOLLOW-UP\n${state.mentorFollow || 'Not entered.'}\n\nCOMPLETED APPOINTMENT TASKS\n${completedLabels || 'None marked complete.'}\n\nPrivacy reminder: Keep this summary only in an approved location and follow applicable student-record policies.`;
}

async function copyText(text, successMessage) {
  try { await navigator.clipboard.writeText(text); showToast(successMessage); }
  catch { showToast('Copy was unavailable—select the text manually.'); }
}

function showToast(message) {
  const toast = $('#toast'); toast.textContent = message; toast.classList.add('show');
  clearTimeout(toastTimer); toastTimer = setTimeout(() => toast.classList.remove('show'), 2300);
}

function openCopilot(prefill = '') {
  $('#copilot-panel').classList.add('open');
  $('#open-copilot').hidden = true;
  if (prefill) { $('#message-input').value = prefill; }
  $('#message-input').focus();
}

function closeCopilot() { $('#copilot-panel').classList.remove('open'); $('#open-copilot').hidden = false; }

function addMessage(role, text, responseId = '') {
  const article = document.createElement('article'); article.className = `message ${role}`;
  const label = document.createElement('small'); label.textContent = role === 'assistant' ? 'Mentor Copilot' : 'You';
  const body = document.createElement('div'); body.textContent = text;
  article.append(label, body); $('#messages').appendChild(article);
  if (role === 'assistant' && responseId) {
    article.title = 'AI-generated guidance—use your judgment and college policy.';
  }
  $('#messages').scrollTop = $('#messages').scrollHeight;
}

function renderChat() {
  $('#messages').innerHTML = '';
  if (!state.chatHistory.length) {
    addMessage('assistant', 'I’m here to support your conversation—not replace your judgment. Ask me for a thoughtful question, a resource match, a concise summary, or a follow-up message.');
  } else state.chatHistory.forEach(item => addMessage(item.role, item.content));
}

function renderCopilotSuggestions() {
  const suggestions = $('#suggestions'); suggestions.innerHTML = '';
  WORKFLOW[state.currentStep].copilot.forEach(prompt => {
    const button = document.createElement('button'); button.type = 'button'; button.textContent = prompt;
    button.addEventListener('click', () => { openCopilot(prompt); }); suggestions.appendChild(button);
  });
}

async function submitCopilot(message) {
  openCopilot();
  addMessage('user', message); state.chatHistory.push({ role: 'user', content: message }); persistState();
  $('#service-status').textContent = 'Thinking…'; $('#send-button').disabled = true;
  const context = [state.student.program && `Major or program: ${state.student.program}.`, state.student.career && `Career direction: ${state.student.career}.`, `Career confidence: ${state.student.confidence}/10.`, state.student.roadmap && `Career Explorer roadmap: ${state.student.roadmap}.`, state.student.followup && `Planned next appointment: ${state.student.followup}.`, state.notes && `General mentor notes: ${state.notes}`, state.studentNext && `Possible student next step: ${state.studentNext}`].filter(Boolean).join(' ');
  try {
    const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: context ? `${message}\n\nNon-sensitive appointment context: ${context}` : message, mode: WORKFLOW[state.currentStep].id, history: state.chatHistory.slice(0, -1).slice(-8) }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Copilot could not respond.');
    addMessage('assistant', data.reply, data.response_id); state.chatHistory.push({ role: 'assistant', content: data.reply });
    $('#service-status').textContent = data.live ? 'AI guidance' : 'Offline guidance'; persistState();
  } catch (error) { addMessage('assistant', error.message || 'Please try again.'); $('#service-status').textContent = 'Try again'; }
  finally { $('#send-button').disabled = false; }
}

function resetAppointment() {
  state = defaultState(); localStorage.removeItem(STORAGE_KEY);
  bindStateToInputs(); renderStep(); renderChat(); $('#confirm-dialog').hidden = true; showView('appointment'); showToast('New appointment ready');
}

function bindStateToInputs() {
  $('#student-name').value = state.student.name; $('#student-program').value = state.student.program; $('#career-direction').value = state.student.career; $('#career-confidence').value = state.student.confidence; $('#roadmap-status').value = state.student.roadmap; $('#followup-track').value = state.student.followup;
  $('#session-notes').value = state.notes; $('#student-next-step').value = state.studentNext; $('#mentor-follow-up').value = state.mentorFollow;
  updateRecommendation();
}

function bindEvents() {
  $$('.top-nav-button').forEach(button => button.addEventListener('click', () => showView(button.dataset.view)));
  $$('[data-view-jump]').forEach(button => button.addEventListener('click', () => showView(button.dataset.viewJump)));
  $('#resource-search').addEventListener('input', renderResources);
  $('#previous-step').addEventListener('click', () => { if (state.currentStep > 0) { state.currentStep--; persistState(); renderStep(); window.scrollTo({ top: 0, behavior: 'smooth' }); } });
  $('#next-step').addEventListener('click', () => {
    if (state.currentStep < WORKFLOW.length - 1) { state.currentStep++; persistState(); renderStep(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
    else { showToast(completedTasks() === totalTasks() ? 'Appointment workflow complete' : 'Review any unfinished tasks before closing'); }
  });
  $('#copy-summary').addEventListener('click', () => copyText(buildSummary(), 'Appointment summary copied'));
  $('#open-copilot').addEventListener('click', () => openCopilot()); $('#close-copilot').addEventListener('click', closeCopilot);
  $('#chat-form').addEventListener('submit', async event => { event.preventDefault(); const input = $('#message-input'); const message = input.value.trim(); if (!message) return; input.value = ''; await submitCopilot(message); });
  $('#message-input').addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); $('#chat-form').requestSubmit(); } });
  $('#new-appointment').addEventListener('click', () => { $('#confirm-dialog').hidden = false; $('#cancel-reset').focus(); });
  $('#cancel-reset').addEventListener('click', () => { $('#confirm-dialog').hidden = true; });
  $('#confirm-reset').addEventListener('click', resetAppointment);
  $('#confirm-dialog').addEventListener('click', event => { if (event.target === $('#confirm-dialog')) $('#confirm-dialog').hidden = true; });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') { $('#confirm-dialog').hidden = true; closeCopilot(); } });
}

async function loadServiceStatus() {
  try {
    const response = await fetch('/api/status'); const data = await response.json();
    $('#service-status').textContent = data.ai_configured ? 'AI ready' : 'Offline guidance ready';
  } catch { $('#service-status').textContent = 'Offline guidance ready'; }
}

bindSessionFields(); bindEvents(); renderQuickTools(); renderResources(); renderStep(); renderChat(); loadServiceStatus();
