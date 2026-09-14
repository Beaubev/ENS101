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
      { id: 'internship-requirement', title: 'Explain the degree internship requirement', detail: 'Review Internship Process (blue bookmark) together. The internship should relate to the student’s major.', action: { label: 'Open Internship Expert', url: '/internship/' } },
      { id: 'internship-course', title: 'Explain the accompanying internship course', detail: 'The student will enroll in the appropriate internship class at the same time. Verify the current course with the student’s program.' },
      { id: 'internship-pbwe', title: 'Explain the PBWE option carefully', detail: 'For on-campus students, CAR 398 PBWE provides real-world project experience and résumé value.' },
      { id: 'internship-timeline', title: 'Discuss application timing', detail: 'Large-company internships may recruit 6–9 months ahead; encourage early research.' },
      { id: 'internship-international', title: 'Flag international-student planning', detail: 'Do not give immigration advice. Help international students verify current vacation-semester and work-authorization rules with the International Student Office.', action: { label: 'International Student Office', url: 'https://www.ensign.edu/international-students' } },
      { id: 'internship-car201', title: 'Encourage early CAR 201 preparation', detail: 'The Internship guide recommends taking CAR 201 as soon as appropriate so the student is ready when internships open.' }
    ],
    prompts: ['How could an internship connect to the career you want?', 'When would you need to begin applying?', 'What experience would help you feel ready?'],
    copilot: ['Explain the internship timeline', 'Compare CAR 398, 399, and 499', 'Give an international-student caution']
  },
  {
    id: 'career-direction', label: 'Career direction', short: 'Confidence and next appointment', duration: '6–8 min',
    title: 'Choose the right career next step',
    description: 'Use the 1–10 confidence question and Career & Major Explorer Roadmap status to decide whether the next appointment should focus on exploration or résumé creation.',
    tasks: [
      { id: 'career-confidence', title: 'Ask the 1–10 confidence question', detail: 'Update the confidence slider above: 1 means very unsure and 10 means very confident.' },
      { id: 'career-pathwayu', title: 'Check Career Explorer Assessment progress', detail: 'Ask whether the student completed the PathwayU assessments and update the status above.', action: { label: 'Open Career Explorer', url: 'https://ensign.pathwayu.com/login?next=%2Fresults' } },
      { id: 'career-followup', title: 'Choose the next appointment type', detail: 'If the student is still exploring, plan a Career Explorer appointment. If confident, plan a Create Resume appointment.' },
      { id: 'career-roadmap2', title: 'If scheduling Create Resume appointment, show Roadmap 2, Steps 1-5', detail: 'Make sure the student knows what to complete before the next appointment.' },
      { id: 'career-action', title: 'Record a specific student action', detail: 'Add the agreed action and time frame in the appointment record below.' }
    ],
    prompts: ['On a scale of 1–10, how sure are you about this career direction?', 'Have you completed the Career & Major Explorer Roadmap?', 'What will you complete before our next appointment?'],
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
  { id: 'internship-expert', name: 'Ensign Internship Expert', initials: 'IE', category: 'Appointment 1a', url: '/internship/', description: 'Official source-grounded answers for Ensign College internships, course pairing, and CPT.' },
  { id: 'informational-interview', name: 'Informational Interview Handout', initials: 'II', category: 'Appointment 1a', url: '/resources/informational-interview-handout.pdf', description: 'Review the informational interview guidance and the questions on the back.' },
  { id: 'pathwayu', name: 'Career & Major Explorer Roadmap', initials: 'CE', category: 'Career Planning', url: 'https://ensign.pathwayu.com/login?next=%2Fresults', description: 'Open the Career & Major Explorer Roadmap results.' },
  { id: 'international', name: 'International Students', initials: 'IS', category: 'Support', url: 'https://www.ensign.edu/international-students', description: 'Official help for work authorization and international-student questions.' },
  { id: 'office', name: 'Career Explorer AI', initials: 'AI', category: 'Career Planning', url: 'https://portal.office.com/', description: 'Open Microsoft 365 to access the Career Explorer AI assistant.' },
  { id: 'canvas', name: 'Canvas', initials: 'C', category: 'Academic', url: 'https://ensign.instructure.com/', description: 'ENS 101 course materials, assignments, announcements, and grades.' },
  { id: 'handshake', name: 'Handshake', initials: 'H', category: 'Career Planning', url: 'https://app.joinhandshake.com/edu', description: 'Primary student job board, on-campus interviews, and employer connections.' },
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
    const action = task.action ? `<a class="task-action" href="${resolveSuiteUrl(task.action.url)}" target="_blank" rel="noopener">${task.action.label}<svg viewBox="0 0 24 24"><path d="M14 5h5v5M10 14 19 5"/><path d="M19 13v6H5V5h6"/></svg></a>` : '';
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
  $('#quick-tool-list').innerHTML = tools.map(resource => `<a class="quick-tool" href="${resolveSuiteUrl(resource.url)}" target="_blank" rel="noopener"><span class="quick-tool-icon">${resource.initials}</span><strong>${resource.name}</strong></a>`).join('');
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
    <a class="resource-card card" href="${resolveSuiteUrl(resource.url)}" target="_blank" rel="noopener">
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
  const recommendationElement = $('#followup-recommendation');
  $('#confidence-output').textContent = confidence;
  const recommendationTone = confidence <= 5
    ? 'recommendation-low'
    : confidence <= 7 ? 'recommendation-medium' : 'recommendation-high';
  const recommendation = confidence <= 5
    ? '<strong>Suggested direction:</strong> The student may benefit from a Career Explorer follow-up after completing the Career & Major Explorer Roadmap.'
    : confidence <= 7
      ? '<strong>Discuss both options:</strong> Clarify the student’s career direction, then choose Career Explorer or Create Resume together.'
      : '<strong>Suggested direction:</strong> If the student remains confident after discussion, consider a Create Resume appointment.';
  recommendationElement.className = `recommendation ${recommendationTone}`;
  recommendationElement.innerHTML = `${recommendation}<span>The mentor makes the final decision with the student.</span>`;
}

function setCareerLookupResult(kind, title, details = []) {
  const result = $('#career-lookup-result');
  result.innerHTML = '';
  result.className = `career-lookup-result ${kind}`;
  const heading = document.createElement('strong');
  heading.textContent = title;
  result.appendChild(heading);
  details.filter(Boolean).forEach(detail => {
    const line = document.createElement('div');
    line.textContent = detail;
    result.appendChild(line);
  });
  result.hidden = false;
}

function setCareerLookupAvailability(available) {
  $('#career-student-email').disabled = !available;
  $('#career-lookup-button').disabled = !available;
}

async function checkCareerExplorerSession() {
  const status = $('#career-session-status');
  const authButton = $('#career-auth-button');
  try {
    const response = await fetch('/api/career-explorer/admin-status', { cache: 'no-store' });
    const data = await response.json();
    if (!data.available) {
      status.textContent = 'Optional setup needed';
      status.className = 'career-session-status warning';
      authButton.hidden = true;
      setCareerLookupAvailability(false);
    } else if (data.authenticated) {
      status.textContent = 'Admin session ready';
      status.className = 'career-session-status ready';
      authButton.hidden = true;
      setCareerLookupAvailability(true);
    } else {
      status.textContent = data.in_progress ? 'Finish sign-in in the open window' : 'Staff authentication required';
      status.className = 'career-session-status warning';
      authButton.textContent = data.in_progress ? 'Check access' : 'Authenticate PathwayU';
      authButton.hidden = false;
      setCareerLookupAvailability(true);
    }
    return data;
  } catch {
    status.textContent = 'Lookup service unavailable';
    status.className = 'career-session-status warning';
    authButton.hidden = true;
    setCareerLookupAvailability(false);
    return null;
  }
}

async function launchCareerExplorerLogin() {
  const button = $('#career-auth-button');
  button.disabled = true;
  try {
    const response = await fetch('/api/career-explorer/launch-login', { method: 'POST' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Authentication could not be started.');
    setCareerLookupResult('warning', 'Complete Ensign staff sign-in', ['Finish SSO/MFA in the PathwayU window, close that window, then check access.']);
  } catch (error) {
    setCareerLookupResult('error', 'Authentication unavailable', [error.message || 'Please try again.']);
  } finally {
    button.disabled = false;
    await checkCareerExplorerSession();
  }
}

function updateRoadmapFromLookup(data) {
  state.student.roadmap = data.status === 'complete'
    ? 'Completed'
    : Number(data.completed_count) > 0 ? 'In progress' : 'Not started';
  $('#roadmap-status').value = state.student.roadmap;
  updateRecommendation();
  persistState();
}

async function lookupCareerExplorer(event) {
  event.preventDefault();
  const emailInput = $('#career-student-email');
  const button = $('#career-lookup-button');
  const email = emailInput.value.trim();
  if (!/^[^@\s]+@ensign\.edu$/i.test(email)) {
    setCareerLookupResult('error', 'Enter a valid Ensign email', ['Use the student’s @ensign.edu address.']);
    emailInput.focus();
    return;
  }

  button.disabled = true;
  button.textContent = 'Checking…';
  setCareerLookupResult('warning', 'Checking Career Explorer', ['This can take a few seconds.']);
  try {
    const response = await fetch('/api/career-explorer/lookup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const data = await response.json();

    if (data.status === 'complete') {
      updateRoadmapFromLookup(data);
      setCareerLookupResult('success', 'Career Explorer complete', ['All four assessments are complete.']);
    } else if (data.status === 'incomplete') {
      updateRoadmapFromLookup(data);
      const missing = Array.isArray(data.missing) && data.missing.length ? `Still needed: ${data.missing.join(', ')}.` : '';
      setCareerLookupResult('warning', 'Career Explorer not yet complete', [`${data.completed_count || 0} of ${data.total || 4} assessments complete.`, missing]);
    } else if (data.status === 'not_found') {
      setCareerLookupResult('error', 'Student not found', ['Verify the @ensign.edu address and try again.']);
    } else if (data.status === 'auth_required') {
      setCareerLookupResult('warning', 'Staff authentication required', [data.message]);
      await checkCareerExplorerSession();
    } else {
      setCareerLookupResult('error', 'Lookup unavailable', [data.message || 'Please try again.']);
    }
  } catch {
    setCareerLookupResult('error', 'Lookup unavailable', ['The app could not contact the Career Explorer lookup service.']);
  } finally {
    // The email intentionally remains only in this input and is never persisted.
    button.disabled = false;
    button.textContent = 'Check completion';
  }
}

function buildSummary() {
  const completedLabels = WORKFLOW.flatMap(step => step.tasks).filter(task => state.checked[task.id]).map(task => `- ${task.title}`).join('\n');
  return `ENS 101 APPOINTMENT 1a SUMMARY\n\nStudent preferred name: ${state.student.name || 'Not entered'}\nMajor or program: ${state.student.program || 'Not entered'}\nCareer direction: ${state.student.career || 'Not entered'}\nCareer confidence: ${state.student.confidence || '5'}/10\nCareer & Major Explorer Roadmap: ${state.student.roadmap || 'Not selected'}\nNext appointment: ${state.student.followup || 'Not selected'}\n\nCONVERSATION NOTES\n${state.notes || 'No notes entered.'}\n\nSTUDENT NEXT STEP\n${state.studentNext || 'Not entered.'}\n\nMENTOR FOLLOW-UP\n${state.mentorFollow || 'Not entered.'}\n\nCOMPLETED APPOINTMENT TASKS\n${completedLabels || 'None marked complete.'}\n\nPrivacy reminder: Keep this summary only in an approved location and follow applicable student-record policies.`;
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

function resolveSuiteUrl(url) {
  if (!url) return '#';
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  const isProxied = window.location.hostname.endsWith('.tail299fc7.ts.net') || 
                    window.location.pathname.startsWith('/ens101') ||
                    window.location.pathname.startsWith('/mentor-desk');
  const host = window.location.hostname || '127.0.0.1';

  if (url === '/' || url === '/dashboard' || url === '/dashboard/') {
    return isProxied ? '/' : `http://${host}:5020/`;
  }
  if (url === '/internship' || url === '/internship/') {
    return isProxied ? '/internship/' : `http://${host}:5035/`;
  }
  return url;
}

function configureTopLinks() {
  const dashBtn = $('#btn-suite-dashboard');
  if (dashBtn) {
    dashBtn.href = resolveSuiteUrl('/');
  }

  const internBtn = $('#btn-internship-expert');
  if (internBtn) {
    internBtn.href = resolveSuiteUrl('/internship/');
  }
}

function formatAssistantMessage(text) {
  const escaped = String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

  let formatted = escaped.replace(
    /\[([^\]]+)\]\(((?:https?:\/\/|\/)[^\s\)\"\']+)\)/g,
    (_match, label, rawUrl) => {
      const resolved = resolveSuiteUrl(rawUrl);
      return `<a href="${resolved}" target="_blank" rel="noopener noreferrer" class="chat-link">${label} &#8599;</a>`;
    }
  );

  formatted = formatted.replace(
    /(^|[\s(])(https?:\/\/[^\s\)\"\']+)/g,
    (_match, prefix, rawUrl) => `${prefix}<a href="${rawUrl}" target="_blank" rel="noopener noreferrer" class="chat-link">${rawUrl} &#8599;</a>`
  );

  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/\n/g, '<br>');
  return formatted;
}

function addMessage(role, text, responseId = '') {
  const article = document.createElement('article'); article.className = `message ${role}`;
  const label = document.createElement('small'); label.textContent = role === 'assistant' ? 'Mentor Copilot' : 'You';
  const body = document.createElement('div'); body.className = 'message-body';
  if (role === 'assistant') {
    body.innerHTML = formatAssistantMessage(text);
  } else {
    body.textContent = text;
  }
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
  const context = [state.student.program && `Major or program: ${state.student.program}.`, state.student.career && `Career direction: ${state.student.career}.`, `Career confidence: ${state.student.confidence}/10.`, state.student.roadmap && `Career & Major Explorer Roadmap: ${state.student.roadmap}.`, state.student.followup && `Planned next appointment: ${state.student.followup}.`, state.notes && `General mentor notes: ${state.notes}`, state.studentNext && `Possible student next step: ${state.studentNext}`].filter(Boolean).join(' ');
  try {
    const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: context ? `${message}\n\nNon-sensitive appointment context: ${context}` : message, mode: WORKFLOW[state.currentStep].id, history: state.chatHistory.slice(0, -1).slice(-8) }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Copilot could not respond.');
    addMessage('assistant', data.reply, data.response_id); state.chatHistory.push({ role: 'assistant', content: data.reply });
    const replyEngine = data.engine === 'local' ? 'Qwen Local' : (data.engine === 'gemini' ? 'Google Gemini' : (data.engine === 'internship_redirect' ? 'Internship Referral' : 'Offline Guidance'));
    updateEngineIndicator(replyEngine); persistState();
  } catch (error) { addMessage('assistant', error.message || 'Please try again.'); $('#service-status').textContent = 'Try again'; }
  finally { $('#send-button').disabled = false; }
}

function resetAppointment() {
  state = defaultState(); localStorage.removeItem(STORAGE_KEY);
  $('#career-student-email').value = '';
  $('#career-lookup-result').hidden = true;
  bindStateToInputs(); renderStep(); renderChat(); $('#confirm-dialog').hidden = true; showView('appointment'); showToast('New appointment ready');
}

function bindStateToInputs() {
  $('#student-name').value = state.student.name; $('#student-program').value = state.student.program; $('#career-direction').value = state.student.career; $('#career-confidence').value = state.student.confidence; $('#roadmap-status').value = state.student.roadmap; $('#followup-track').value = state.student.followup;
  $('#session-notes').value = state.notes; $('#student-next-step').value = state.studentNext; $('#mentor-follow-up').value = state.mentorFollow;
  updateRecommendation();
}

function openSuggestionModal() {
  const dialog = $('#suggestion-dialog');
  if (!dialog) return;
  dialog.hidden = false;
  $('#suggestion-text').focus();
}

function closeSuggestionModal() {
  const dialog = $('#suggestion-dialog');
  if (!dialog) return;
  dialog.hidden = true;
}

async function handleSuggestionSubmit(event) {
  event.preventDefault();
  const submitBtn = $('#submit-suggestion-btn');
  const category = $('#suggestion-category').value;
  const suggestion = $('#suggestion-text').value.trim();
  const submitter = $('#suggestion-submitter').value.trim();

  if (!suggestion) {
    showToast('Please enter a suggestion.');
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Submitting…';

  try {
    const resp = await fetch('/api/suggestions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, suggestion, submitter }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.error || 'Failed to submit suggestion.');
    }
    showToast(data.message || 'Thank you! Suggestion submitted.');
    $('#suggestion-text').value = '';
    $('#suggestion-submitter').value = '';
    $('#suggestion-char-count').textContent = '0 / 2000';
    closeSuggestionModal();
  } catch (err) {
    showToast(err.message || 'Error submitting suggestion.');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Submit Suggestion';
  }
}

function bindEvents() {
  $$('.top-nav-button').forEach(button => button.addEventListener('click', () => showView(button.dataset.view)));
  $$('[data-view-jump]').forEach(button => button.addEventListener('click', () => showView(button.dataset.viewJump)));
  $('#resource-search').addEventListener('input', renderResources);
  $('#career-lookup-form').addEventListener('submit', lookupCareerExplorer);
  $('#career-auth-button').addEventListener('click', launchCareerExplorerLogin);
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

  // Suggestion Modal handlers
  const openSuggestBtn = $('#open-suggestion-modal');
  if (openSuggestBtn) openSuggestBtn.addEventListener('click', openSuggestionModal);
  const closeSuggestBtn = $('#close-suggestion-dialog');
  if (closeSuggestBtn) closeSuggestBtn.addEventListener('click', closeSuggestionModal);
  const cancelSuggestBtn = $('#cancel-suggestion');
  if (cancelSuggestBtn) cancelSuggestBtn.addEventListener('click', closeSuggestionModal);
  const suggestDialog = $('#suggestion-dialog');
  if (suggestDialog) suggestDialog.addEventListener('click', event => { if (event.target === suggestDialog) closeSuggestionModal(); });
  const suggestForm = $('#suggestion-form');
  if (suggestForm) suggestForm.addEventListener('submit', handleSuggestionSubmit);
  const suggestText = $('#suggestion-text');
  if (suggestText) {
    suggestText.addEventListener('input', () => {
      const charCount = $('#suggestion-char-count');
      if (charCount) charCount.textContent = `${suggestText.value.length} / 2000`;
    });
  }

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      $('#confirm-dialog').hidden = true;
      closeSuggestionModal();
      closeCopilot();
    }
  });
}

function updateEngineIndicator(engineName) {
  const badge = $('#ai-engine-badge');
  const nameEl = $('#ai-engine-name');
  const serviceStatus = $('#service-status');
  const isGemini = engineName.toLowerCase().includes('gemini');
  const isOffline = engineName.toLowerCase().includes('offline') || engineName.toLowerCase().includes('unavailable');

  if (nameEl) nameEl.textContent = engineName;
  if (badge) {
    badge.className = `engine-indicator-pill ${isOffline ? 'engine-offline' : (isGemini ? 'engine-gemini' : 'engine-qwen')}`;
  }
  if (serviceStatus) {
    serviceStatus.textContent = engineName;
  }
}

async function loadServiceStatus() {
  try {
    const response = await fetch('/api/status');
    const data = await response.json();
    const active = data.active_engine || (data.ai_configured ? 'Qwen Local' : 'Offline Guidance');
    updateEngineIndicator(active);
  } catch {
    updateEngineIndicator('Offline Guidance');
  }
}

bindSessionFields(); bindEvents(); configureTopLinks(); renderQuickTools(); renderResources(); renderStep(); renderChat(); loadServiceStatus(); checkCareerExplorerSession();
