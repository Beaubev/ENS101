const STORAGE_KEY = 'ens101-mentor-desk-appointment-1a-v3';
const ACTIVE_APPT_ID_KEY = 'ens101_active_appt_id';

const PREPARE_STEPS = [
  {
    id: 'prep-assessment',
    label: 'Assessment',
    short: 'Determine PathwayU completion',
    duration: '3–5 min',
    title: 'Determine PathwayU Assessment Completion',
    description: 'Enter the student’s @ensign.edu email to check completion across the four Career Explorer assessments, or upload their PDF report.',
    copilot: ['How do I explain PathwayU?', 'What if a student hasn’t taken the assessments?', 'Explain the 4 PathwayU assessments']
  },
  {
    id: 'prep-guidance',
    label: 'Guidance',
    short: 'Review tailored guidance',
    duration: '3–5 min',
    title: 'Review Personalized Career Guidance',
    description: 'Explore Holland Code insights, aligned Ensign College majors, top career paths, and tailored discussion strategies based on the assessment results.',
    copilot: ['Explain Holland Code SEC', 'Suggest questions for their major', 'Connect Holland traits to careers']
  },
  {
    id: 'prep-notes',
    label: 'Prep Notes',
    short: 'Type appointment notes',
    duration: '3–5 min',
    title: 'Appointment Preparation Notes',
    description: 'Capture your thoughts, talking points, and specific items to bring up during the appointment. These notes persist with the student record and will be available during Task 2.',
    copilot: ['Help me draft prep notes', 'Suggest key talking points', 'What should I prioritize for Appointment 1a?']
  }
];

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
      { id: 'internship-requirement', title: 'Explain the degree internship requirement', detail: 'The internship should relate to the student’s major; review the current internship information together.', action: { label: 'Open Internship Expert', url: '/internship/' } },
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
  { id: 'internship-expert', name: 'Ensign Internship Expert', initials: 'IE', category: 'Appointment 1a', url: '/internship/', description: 'Official source-grounded answers for Ensign College internships, course pairing, and CPT.' },
  { id: 'informational-interview', name: 'Informational Interview Handout', initials: 'II', category: 'Appointment 1a', url: '/resources/informational-interview-handout.pdf', description: 'Review the informational interview guidance and the questions on the back.' },
  { id: 'pathwayu', name: 'Career Explorer', initials: 'CE', category: 'Career Planning', url: 'https://ensign.pathwayu.com/login?next=%2Fresults', description: 'Open PathwayU career assessments and roadmap results.' },
  { id: 'international', name: 'International Students', initials: 'IS', category: 'Support', url: 'https://www.ensign.edu/international-students', description: 'Official help for work authorization and international-student questions.' },
  { id: 'office', name: 'Career Explorer AI', initials: 'AI', category: 'Career Planning', url: 'https://portal.office.com/', description: 'Open Microsoft 365 to access the Career Explorer AI assistant.' },
  { id: 'canvas', name: 'Canvas', initials: 'C', category: 'Academic', url: 'https://ensign.instructure.com/', description: 'ENS 101 course materials, assignments, announcements, and grades.' },
  { id: 'handshake', name: 'Handshake', initials: 'H', category: 'Career Planning', url: 'https://app.joinhandshake.com/edu', description: 'Primary student job board, on-campus interviews, and employer connections.' },
  { id: 'career', name: 'Career & Internship Services', initials: 'CS', category: 'Career Planning', url: 'https://www.ensign.edu/CIS', description: 'Career preparation, internships, résumés, interviews, and networking.' }
];

const defaultState = () => ({
  currentTask: 'prepare',
  currentStep: 0,
  appointmentId: '',
  student: {
    name: '',
    email: '',
    program: '',
    career: '',
    confidence: '5',
    roadmap: '',
    followup: ''
  },
  assessmentData: {
    completed_count: 0,
    total: 4,
    status: 'incomplete',
    missing: ['Interests', 'Values', 'Personality', 'Workplace Preferences'],
    holland_code: '',
    primary_interests: [],
    primary_values: [],
    primary_workplace_preferences: []
  },
  guidance: null,
  prepNotes: '',
  sessionNotes: '',
  studentNext: '',
  mentorFollow: '',
  checked: {},
  civitasRecorded: false,
  chatHistory: []
});

let state = defaultState();
let savedAppointmentsList = [];
let activeResourceFilter = 'All';
let saveTimer = null;
let toastTimer = null;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function totalTasks() {
  return WORKFLOW.reduce((sum, step) => sum + step.tasks.length, 0);
}

function completedTasks() {
  return Object.values(state.checked).filter(Boolean).length;
}

function stepComplete(step) {
  return step.tasks.every(task => state.checked[task.id]);
}

async function fetchAppointmentsList() {
  try {
    const res = await fetch('/api/appointments');
    const data = await res.json();
    if (data.status === 'ok') {
      savedAppointmentsList = data.appointments || [];
      renderStudentSwitcher();
    }
  } catch (err) {
    console.error('Failed to load appointments list:', err);
  }
}

function renderStudentSwitcher() {
  const switcher = $('#student-switcher');
  if (!switcher) return;

  switcher.innerHTML = '<option value="">+ New Student (Start Prep)</option>';
  savedAppointmentsList.forEach(appt => {
    const opt = document.createElement('option');
    opt.value = appt.id;
    const name = appt.student_name || 'Unnamed Student';
    const email = appt.student_email ? ` (${appt.student_email})` : '';
    const status = appt.civitas_recorded ? ' [Civitas ✓]' : '';
    opt.textContent = `${name}${email}${status}`;
    if (appt.id === state.appointmentId) {
      opt.selected = true;
    }
    switcher.appendChild(opt);
  });
}

async function loadAppointmentById(appId) {
  if (!appId) {
    resetAppointmentLocal();
    return;
  }
  try {
    const res = await fetch(`/api/appointments/get?id=${encodeURIComponent(appId)}`);
    const data = await res.json();
    if (data.status === 'ok' && data.appointment) {
      const a = data.appointment;
      state = {
        ...defaultState(),
        appointmentId: a.id,
        currentTask: a.current_task || 'prepare',
        currentStep: typeof a.current_step === 'number' ? a.current_step : 0,
        student: {
          name: a.student_name || '',
          email: a.student_email || '',
          program: a.program || '',
          career: a.career || '',
          confidence: a.confidence || '5',
          roadmap: a.roadmap_status || '',
          followup: a.followup_track || ''
        },
        assessmentData: a.assessment_data && typeof a.assessment_data === 'object' ? a.assessment_data : defaultState().assessmentData,
        prepNotes: a.prep_notes || '',
        sessionNotes: a.session_notes || '',
        studentNext: a.student_next || '',
        mentorFollow: a.mentor_follow || '',
        checked: a.checked_tasks && typeof a.checked_tasks === 'object' ? a.checked_tasks : {},
        civitasRecorded: Boolean(a.civitas_recorded),
        chatHistory: []
      };
      localStorage.setItem(ACTIVE_APPT_ID_KEY, a.id);
      syncInputsFromState();
      renderStep();
      renderChat();
      if (state.assessmentData.holland_code || state.assessmentData.completed_count > 0) {
        await fetchCareerGuidance();
      }
      showToast(`Loaded record for ${state.student.name || 'student'}`);
    }
  } catch (err) {
    console.error('Failed to load appointment:', err);
    showToast('Could not load appointment.');
  }
}

function persistState() {
  const statusEl = $('#save-status');
  if (statusEl) statusEl.textContent = 'Saving…';
  clearTimeout(saveTimer);
  saveTimer = setTimeout(async () => {
    try {
      const payload = {
        id: state.appointmentId || undefined,
        student_email: state.student.email,
        student_name: state.student.name,
        program: state.student.program,
        career: state.student.career,
        confidence: state.student.confidence,
        roadmap_status: state.student.roadmap,
        followup_track: state.student.followup,
        assessment_data: state.assessmentData,
        prep_notes: state.prepNotes,
        session_notes: state.sessionNotes,
        student_next: state.studentNext,
        mentor_follow: state.mentorFollow,
        checked_tasks: state.checked,
        current_task: state.currentTask,
        current_step: state.currentStep,
        civitas_recorded: state.civitasRecorded ? 1 : 0
      };

      const res = await fetch('/api/appointments/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok && data.status === 'ok') {
        if (data.appointment?.id && !state.appointmentId) {
          state.appointmentId = data.appointment.id;
          localStorage.setItem(ACTIVE_APPT_ID_KEY, data.appointment.id);
        }
        if (statusEl) statusEl.textContent = 'Saved to record';
        fetchAppointmentsList();
      } else {
        if (statusEl) statusEl.textContent = 'Saved locally';
      }
    } catch {
      if (statusEl) statusEl.textContent = 'Offline (local)';
    }
  }, 400);
}

async function fetchCareerGuidance() {
  try {
    const res = await fetch('/api/career-explorer/guidance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_name: state.student.name,
        program: state.student.program,
        career: state.student.career,
        assessment_data: state.assessmentData
      })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      state.guidance = data;
      renderGuidanceDisplay(data);
    }
  } catch (err) {
    console.error('Error fetching guidance:', err);
  }
}

function renderGuidanceDisplay(data) {
  const codeEl = $('#guidance-holland-code');
  if (codeEl) codeEl.textContent = data.holland_code ? `${data.holland_code} Profile` : 'Social-Enterprising-Conventional (SEC)';

  const traitsEl = $('#guidance-traits-list');
  if (traitsEl && Array.isArray(data.sections)) {
    const traitSection = data.sections.find(s => s.title.includes('Holland Code'));
    if (traitSection) {
      const items = traitSection.content.split('\n• ').map(s => s.replace(/^•\s*/, '').trim()).filter(Boolean);
      traitsEl.innerHTML = items.map(t => `<span class="trait-tag">${t}</span>`).join('');
    }
  }

  const majorsEl = $('#guidance-majors-list');
  if (majorsEl && Array.isArray(data.aligned_majors)) {
    majorsEl.innerHTML = data.aligned_majors.map(m => `<li><strong>${m}</strong></li>`).join('');
  }

  const careersEl = $('#guidance-careers-list');
  if (careersEl && Array.isArray(data.aligned_careers)) {
    careersEl.innerHTML = data.aligned_careers.map(c => `<li>${c}</li>`).join('');
  }

  const stratEl = $('#guidance-strategy-list');
  if (stratEl && Array.isArray(data.sections)) {
    const stratSection = data.sections.find(s => s.title.includes('Discussion Strategy'));
    if (stratSection) {
      const items = stratSection.content.split('\n• ').map(s => s.replace(/^•\s*/, '').trim()).filter(Boolean);
      stratEl.innerHTML = items.map(s => `<li>${s}</li>`).join('');
    }
  }
}

function renderAssessmentCards() {
  const data = state.assessmentData || {};
  const completed = Array.isArray(data.completed) ? data.completed : (data.completed_count === 4 ? ['Interests', 'Values', 'Personality', 'Workplace Preferences'] : []);
  const count = Number(data.completed_count || 0);

  const countBadge = $('#prep-completion-count');
  if (countBadge) countBadge.textContent = `${count} of 4 complete`;

  const map = {
    'card-interests': 'Interests',
    'card-values': 'Values',
    'card-personality': 'Personality',
    'card-workplace': 'Workplace Preferences'
  };

  Object.entries(map).forEach(([cardId, name]) => {
    const card = $(`#${cardId}`);
    if (!card) return;
    const badge = card.querySelector('.module-status-badge');
    const isDone = completed.includes(name) || (count === 4);

    if (isDone) {
      card.className = 'assessment-module-card complete';
      if (badge) {
        badge.className = 'module-status-badge complete';
        badge.textContent = '✓ Completed';
      }
    } else {
      card.className = 'assessment-module-card';
      if (badge) {
        badge.className = 'module-status-badge pending';
        badge.textContent = 'Not started';
      }
    }
  });

  const feedback = $('#prep-lookup-feedback');
  if (feedback) {
    if (count === 4 || data.status === 'complete') {
      feedback.className = 'lookup-feedback-banner success';
      feedback.textContent = '✓ All 4 Career Explorer assessments are complete! Student is ready for personalized guidance.';
      feedback.hidden = false;
    } else if (count > 0) {
      feedback.className = 'lookup-feedback-banner warning';
      const missing = Array.isArray(data.missing) && data.missing.length ? ` Still needed: ${data.missing.join(', ')}.` : '';
      feedback.textContent = `${count} of 4 assessments complete.${missing}`;
      feedback.hidden = false;
    } else {
      feedback.hidden = true;
    }
  }
}

function renderWorkflow() {
  const nav = $('#workflow-nav');
  if (!nav) return;
  nav.innerHTML = '';

  const task1Header = document.createElement('div');
  task1Header.className = 'sidebar-task-title';
  task1Header.innerHTML = `<span>Task 1: PREPARE</span><small>${state.currentTask === 'prepare' ? 'Active' : ''}</small>`;
  nav.appendChild(task1Header);

  PREPARE_STEPS.forEach((step, idx) => {
    const btn = document.createElement('button');
    const isActive = state.currentTask === 'prepare' && state.currentStep === idx;
    const isDone = (idx === 0 && (state.assessmentData?.completed_count > 0 || state.assessmentData?.status === 'complete'))
      || (idx === 1 && state.guidance !== null)
      || (idx === 2 && Boolean(state.prepNotes?.trim()));

    btn.type = 'button';
    btn.className = `workflow-button${isActive ? ' active' : ''}${isDone ? ' complete' : ''}`;
    btn.innerHTML = `<span class="workflow-num">${isDone ? '✓' : idx + 1}</span><span class="workflow-label"><strong>${step.label}</strong><small>${step.short}</small></span>${isDone ? '<span class="workflow-check">✓</span>' : ''}`;
    btn.addEventListener('click', () => {
      state.currentTask = 'prepare';
      state.currentStep = idx;
      persistState();
      renderStep();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    nav.appendChild(btn);
  });

  const task2Header = document.createElement('div');
  task2Header.className = 'sidebar-task-title';
  task2Header.innerHTML = `<span>Task 2: APPOINTMENT</span><small>${state.currentTask === 'appointment' ? 'Active' : ''}</small>`;
  nav.appendChild(task2Header);

  WORKFLOW.forEach((step, idx) => {
    const btn = document.createElement('button');
    const isActive = state.currentTask === 'appointment' && state.currentStep === idx;
    const isDone = stepComplete(step);
    const confidence = Number(state.student.confidence || 5);
    const confidenceTone = confidence <= 5 ? 'confidence-low' : confidence <= 7 ? 'confidence-medium' : 'confidence-high';

    btn.type = 'button';
    btn.className = `workflow-button${isActive ? ' active' : ''}${isDone ? ' complete' : ''}${idx === 0 ? ` ${confidenceTone}` : ''}`;
    btn.innerHTML = `<span class="workflow-num">${isDone ? '✓' : idx + 1}</span><span class="workflow-label"><strong>${step.label}</strong><small>${step.short}</small></span>${isDone ? '<span class="workflow-check">✓</span>' : ''}`;
    btn.addEventListener('click', () => {
      state.currentTask = 'appointment';
      state.currentStep = idx;
      persistState();
      renderStep();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    nav.appendChild(btn);
  });

  renderProgress();
}

function renderProgress() {
  const complete = completedTasks();
  const total = totalTasks();
  const percentage = Math.round((complete / total) * 100);
  const label = $('#progress-label');
  const count = $('#progress-count');
  const bar = $('#progress-bar');
  if (label) label.textContent = `${percentage}% complete`;
  if (count) count.textContent = `${complete} of ${total}`;
  if (bar) bar.style.width = `${percentage}%`;
}

function renderStep() {
  const isPrepare = state.currentTask === 'prepare';
  const prepWorkspace = $('#task1-prepare-workspace');
  const apptWorkspace = $('#task2-appointment-workspace');

  if (prepWorkspace) prepWorkspace.hidden = !isPrepare;
  if (apptWorkspace) apptWorkspace.hidden = isPrepare;

  if (isPrepare) {
    renderPrepareWorkspace();
  } else {
    renderAppointmentWorkspace();
  }

  renderCopilotSuggestions();
  renderWorkflow();
}

function renderPrepareWorkspace() {
  const stepIdx = state.currentStep;
  const currentStepDef = PREPARE_STEPS[stepIdx] || PREPARE_STEPS[0];

  const eyebrow = $('#step-eyebrow');
  if (eyebrow) eyebrow.textContent = `TASK 1: PREPARE · STEP ${stepIdx + 1} OF 3`;
  const title = $('#step-title');
  if (title) title.textContent = currentStepDef.title;
  const desc = $('#step-description');
  if (desc) desc.textContent = currentStepDef.description;
  const dur = $('#step-duration');
  if (dur) dur.textContent = `Suggested time · ${currentStepDef.duration}`;

  if ($('#prep-step-1')) $('#prep-step-1').hidden = stepIdx !== 0;
  if ($('#prep-step-2')) $('#prep-step-2').hidden = stepIdx !== 1;
  if ($('#prep-step-3')) $('#prep-step-3').hidden = stepIdx !== 2;

  if (stepIdx === 0) {
    renderAssessmentCards();
  } else if (stepIdx === 1) {
    if (state.guidance) {
      renderGuidanceDisplay(state.guidance);
    } else {
      fetchCareerGuidance();
    }
  } else if (stepIdx === 2) {
    if ($('#recap-name')) $('#recap-name').textContent = state.student.name || 'Unnamed';
    if ($('#recap-email')) $('#recap-email').textContent = state.student.email || 'No email';
    if ($('#recap-program')) $('#recap-program').textContent = state.student.program || 'Not selected';
    if ($('#recap-career')) $('#recap-career').textContent = state.student.career || 'Not selected';
    if ($('#recap-pathwayu')) $('#recap-pathwayu').textContent = state.assessmentData.status === 'complete' ? 'Completed' : `${state.assessmentData.completed_count || 0}/4 complete`;
    if ($('#prep-notes-textarea')) $('#prep-notes-textarea').value = state.prepNotes || '';
  }
}

function renderAppointmentWorkspace() {
  const stepIdx = state.currentStep;
  const step = WORKFLOW[stepIdx] || WORKFLOW[0];

  const showSessionDetails = stepIdx === 0 || stepIdx === WORKFLOW.length - 1;
  const sessionCard = $('#session-details-card');
  if (sessionCard) sessionCard.hidden = !showSessionDetails;

  const eyebrow = $('#step-eyebrow');
  if (eyebrow) eyebrow.textContent = `TASK 2: APPOINTMENT · STEP ${stepIdx + 1} OF ${WORKFLOW.length}`;
  const title = $('#step-title');
  if (title) title.textContent = step.title;
  const desc = $('#step-description');
  if (desc) desc.textContent = step.description;
  const dur = $('#step-duration');
  if (dur) dur.textContent = `Suggested time · ${step.duration}`;
  const kicker = $('#step-kicker');
  if (kicker) kicker.textContent = `Step ${stepIdx + 1} of ${WORKFLOW.length}`;

  const prevBtn = $('#previous-step');
  if (prevBtn) {
    prevBtn.disabled = stepIdx === 0;
    prevBtn.style.visibility = stepIdx === 0 ? 'hidden' : 'visible';
  }
  const nextBtn = $('#next-step');
  if (nextBtn) {
    nextBtn.textContent = stepIdx === WORKFLOW.length - 1 ? 'Finish appointment' : 'Continue';
  }

  const list = $('#task-list');
  if (list) {
    list.innerHTML = '';
    step.tasks.forEach(task => {
      const item = document.createElement('div');
      const checked = Boolean(state.checked[task.id]);
      item.className = `task-item${checked ? ' checked' : ''}`;
      const action = task.action ? `<a class="task-action" href="${resolveSuiteUrl(task.action.url)}" target="_blank" rel="noopener">${task.action.label}<svg viewBox="0 0 24 24"><path d="M14 5h5v5M10 14 19 5"/><path d="M19 13v6H5V5h6"/></svg></a>` : '';
      item.innerHTML = `<button class="task-check" type="button" aria-label="${checked ? 'Mark incomplete' : 'Mark complete'}: ${task.title}"><svg viewBox="0 0 24 24"><path d="m5 12 4 4L19 6"/></svg></button><div class="task-copy"><strong>${task.title}</strong><p>${task.detail}</p>${action}</div>`;
      item.querySelector('button').addEventListener('click', () => {
        state.checked[task.id] = !checked;
        persistState();
        renderStep();
      });
      list.appendChild(item);
    });
  }

  const done = step.tasks.filter(task => state.checked[task.id]).length;
  const countBadge = $('#step-task-count');
  if (countBadge) countBadge.textContent = `${done}/${step.tasks.length} complete`;

  const prompts = $('#conversation-prompts');
  if (prompts) {
    prompts.innerHTML = '';
    step.prompts.forEach(text => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'prompt-button';
      button.textContent = text;
      button.addEventListener('click', () => copyText(text, 'Question copied'));
      prompts.appendChild(button);
    });
  }

  const snippet = $('#prep-preview-snippet');
  const previewText = $('#prep-preview-text');
  if (state.prepNotes?.trim()) {
    if (snippet) snippet.textContent = state.prepNotes.slice(0, 60) + (state.prepNotes.length > 60 ? '…' : '');
    if (previewText) previewText.textContent = state.prepNotes;
  } else {
    if (snippet) snippet.textContent = 'No prep notes recorded';
    if (previewText) previewText.textContent = 'No prep notes recorded in Task 1 for this student.';
  }

  const civitasCard = $('#civitas-card');
  if (civitasCard) {
    civitasCard.hidden = stepIdx !== WORKFLOW.length - 1;
    const confirmCb = $('#civitas-confirm-checkbox');
    if (confirmCb) confirmCb.checked = Boolean(state.civitasRecorded);
    const delBtn = $('#btn-complete-delete-record');
    if (delBtn) delBtn.disabled = !state.civitasRecorded;
  }

  updateRecommendation();
}

function updateRecommendation() {
  const confidence = Number(state.student.confidence || 5);
  const recommendationElement = $('#followup-recommendation');
  if (!recommendationElement) return;

  const out = $('#confidence-output');
  if (out) out.textContent = confidence;
  const prepOut = $('#prep-confidence-output');
  if (prepOut) prepOut.textContent = confidence;

  const recommendationTone = confidence <= 5
    ? 'recommendation-low'
    : confidence <= 7 ? 'recommendation-medium' : 'recommendation-high';

  const recommendation = confidence <= 5
    ? 'The student may benefit from a Career Explorer follow-up after completing the PathwayU roadmap.'
    : confidence <= 7
      ? '<strong>Discuss both options:</strong> Clarify the student’s career direction, then choose Career Explorer or Create Resume together.'
      : 'If the student remains confident after discussion, consider a Create Resume appointment.';

  recommendationElement.className = `recommendation ${recommendationTone}`;
  recommendationElement.innerHTML = `<div class="recommendation-label">Suggested Action:</div><div class="recommendation-content"><div class="recommendation-guidance">${recommendation}</div><span class="recommendation-note">The mentor makes the final decision with the student.</span></div>`;
}

function syncInputsFromState() {
  if ($('#prep-student-name')) $('#prep-student-name').value = state.student.name;
  if ($('#prep-student-email')) $('#prep-student-email').value = state.student.email;
  if ($('#prep-student-program')) $('#prep-student-program').value = state.student.program;
  if ($('#prep-career-direction')) $('#prep-career-direction').value = state.student.career;
  if ($('#prep-career-confidence')) $('#prep-career-confidence').value = state.student.confidence;
  if ($('#prep-notes-textarea')) $('#prep-notes-textarea').value = state.prepNotes;

  if ($('#student-name')) $('#student-name').value = state.student.name;
  if ($('#career-student-email')) $('#career-student-email').value = state.student.email;
  if ($('#student-program')) $('#student-program').value = state.student.program;
  if ($('#career-direction')) $('#career-direction').value = state.student.career;
  if ($('#career-confidence')) $('#career-confidence').value = state.student.confidence;
  if ($('#roadmap-status')) $('#roadmap-status').value = state.student.roadmap;
  if ($('#followup-track')) $('#followup-track').value = state.student.followup;
  if ($('#session-notes')) $('#session-notes').value = state.sessionNotes;
  if ($('#student-next-step')) $('#student-next-step').value = state.studentNext;
  if ($('#mentor-follow-up')) $('#mentor-follow-up').value = state.mentorFollow;

  updateRecommendation();
  renderAssessmentCards();
}

function bindSessionFields() {
  const syncPairs = [
    [['#prep-student-name', '#student-name'], 'name'],
    [['#prep-student-email', '#career-student-email'], 'email'],
    [['#prep-student-program', '#student-program'], 'program'],
    [['#prep-career-direction', '#career-direction'], 'career'],
    [['#prep-career-confidence', '#career-confidence'], 'confidence']
  ];

  syncPairs.forEach(([selectors, key]) => {
    selectors.forEach(sel => {
      const el = $(sel);
      if (!el) return;
      el.addEventListener('input', () => {
        state.student[key] = el.value;
        selectors.forEach(otherSel => {
          const otherEl = $(otherSel);
          if (otherEl && otherEl !== el) otherEl.value = el.value;
        });
        if (key === 'confidence') {
          updateRecommendation();
          renderWorkflow();
        }
        persistState();
      });
    });
  });

  const roadmapSel = $('#roadmap-status');
  if (roadmapSel) {
    roadmapSel.addEventListener('change', () => {
      state.student.roadmap = roadmapSel.value;
      persistState();
    });
  }

  const followSel = $('#followup-track');
  if (followSel) {
    followSel.addEventListener('change', () => {
      state.student.followup = followSel.value;
      persistState();
    });
  }

  const prepNotesEl = $('#prep-notes-textarea');
  if (prepNotesEl) {
    prepNotesEl.addEventListener('input', () => {
      state.prepNotes = prepNotesEl.value;
      persistState();
    });
  }

  const notesPairs = [
    ['#session-notes', 'sessionNotes'],
    ['#student-next-step', 'studentNext'],
    ['#mentor-follow-up', 'mentorFollow']
  ];
  notesPairs.forEach(([sel, key]) => {
    const el = $(sel);
    if (!el) return;
    el.addEventListener('input', () => {
      state[key] = el.value;
      persistState();
    });
  });
}

async function checkCareerExplorerSession() {
  const statusEls = [$('#career-session-status'), $('#prep-career-session-status')].filter(Boolean);
  const authBtns = [$('#career-auth-button'), $('#prep-career-auth-btn')].filter(Boolean);
  try {
    const response = await fetch('/api/career-explorer/admin-status', { cache: 'no-store' });
    const data = await response.json();
    statusEls.forEach(status => {
      if (!data.available) {
        status.textContent = 'Optional setup needed';
        status.className = 'career-session-status warning';
      } else if (data.authenticated) {
        status.textContent = 'Admin session ready';
        status.className = 'career-session-status ready';
      } else {
        status.textContent = data.in_progress ? 'Sign in in open window' : 'SSO login needed';
        status.className = 'career-session-status warning';
      }
    });
    authBtns.forEach(btn => {
      btn.hidden = data.authenticated || !data.available;
      if (!btn.hidden) {
        btn.textContent = data.in_progress ? 'Check access' : 'Authenticate PathwayU';
      }
    });
    return data;
  } catch {
    statusEls.forEach(status => {
      status.textContent = 'Lookup unavailable';
      status.className = 'career-session-status warning';
    });
    authBtns.forEach(btn => { btn.hidden = true; });
    return null;
  }
}

async function launchCareerExplorerLogin() {
  try {
    const res = await fetch('/api/career-explorer/launch-login', { method: 'POST' });
    const data = await res.json();
    showToast(data.message || 'Authentication window opening...');
  } catch (err) {
    showToast('Failed to start authentication.');
  } finally {
    await checkCareerExplorerSession();
  }
}

async function performStudentLookup(email) {
  if (!email || !/^[^@\s]+@ensign\.edu$/i.test(email)) {
    showToast('Please enter a valid @ensign.edu address.');
    return;
  }

  showToast('Checking PathwayU assessments…');
  const feedback = $('#prep-lookup-feedback');
  if (feedback) {
    feedback.className = 'lookup-feedback-banner warning';
    feedback.textContent = 'Checking completion in PathwayU…';
    feedback.hidden = false;
  }

  try {
    const response = await fetch('/api/career-explorer/lookup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const data = await response.json();

    if (data.status === 'complete' || data.status === 'incomplete') {
      state.assessmentData = {
        ...state.assessmentData,
        ...data
      };
      state.student.roadmap = data.status === 'complete'
        ? 'Completed'
        : (Number(data.completed_count) > 0 ? 'In progress' : 'Not started');
      if ($('#roadmap-status')) $('#roadmap-status').value = state.student.roadmap;
      renderAssessmentCards();
      await fetchCareerGuidance();
      persistState();
      showToast('PathwayU completion updated!');
    } else if (data.status === 'auth_required') {
      showToast('Staff authentication required. Click Authenticate PathwayU.');
      await checkCareerExplorerSession();
    } else {
      showToast(data.message || 'Lookup unavailable.');
    }
  } catch (err) {
    showToast('Could not contact PathwayU lookup service.');
  }
}

async function handlePdfUpload(file) {
  if (!file || file.type !== 'application/pdf') {
    showToast('Please upload a PDF file.');
    return;
  }
  const statusEl = $('#prep-pdf-status');
  if (statusEl) {
    statusEl.textContent = `Analyzing ${file.name}…`;
    statusEl.hidden = false;
  }

  const reader = new FileReader();
  reader.onload = async (e) => {
    try {
      const base64 = e.target.result;
      const res = await fetch('/api/career-explorer/parse-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pdf_base64: base64 })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to parse PDF');

      const parsed = data.data || {};
      if (parsed.student_name && !state.student.name) {
        state.student.name = parsed.student_name;
        if ($('#prep-student-name')) $('#prep-student-name').value = parsed.student_name;
        if ($('#student-name')) $('#student-name').value = parsed.student_name;
      }
      state.assessmentData = {
        ...state.assessmentData,
        ...parsed
      };
      state.student.roadmap = parsed.status === 'complete' ? 'Completed' : (parsed.completed_count > 0 ? 'In progress' : 'Not started');
      if ($('#roadmap-status')) $('#roadmap-status').value = state.student.roadmap;

      if (statusEl) {
        statusEl.textContent = `✓ Report analyzed for ${parsed.student_name || 'student'}. Holland Code: ${parsed.holland_code || 'Detected'}.`;
      }
      renderAssessmentCards();
      await fetchCareerGuidance();
      persistState();
      showToast('Career Explorer report analyzed!');
    } catch (err) {
      if (statusEl) statusEl.textContent = `⚠️ ${err.message || 'Error processing PDF.'}`;
    }
  };
  reader.readAsDataURL(file);
}

function buildCivitasNote() {
  const dateStr = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  const tasksDone = WORKFLOW.flatMap(s => s.tasks).filter(t => state.checked[t.id]).map(t => `  ✓ ${t.title}`).join('\n');
  const code = state.assessmentData?.holland_code ? `\nHolland Code: ${state.assessmentData.holland_code}` : '';

  return `ENS 101 APPOINTMENT 1a — ADVISING RECORD
` +
    `Date: ${dateStr}
` +
    `Student: ${state.student.name || 'Not entered'} (${state.student.email || 'Not entered'})
` +
    `Major / Program: ${state.student.program || 'Undeclared / In Progress'}
` +
    `Career Direction: ${state.student.career || 'Exploring'}
` +
    `Career Confidence: ${state.student.confidence || 5}/10
` +
    `PathwayU Status: ${state.assessmentData?.status === 'complete' ? 'Completed (All 4 modules)' : (state.assessmentData?.completed_count > 0 ? `${state.assessmentData.completed_count}/4 completed` : 'Not completed')}${code}
` +
    `Next Planned Appointment: ${state.student.followup || 'Career Explorer / Create Resume'}

` +
    `PREPARATION NOTES:
${state.prepNotes || 'None recorded.'}

` +
    `SESSION CONVERSATION NOTES:
${state.sessionNotes || 'No notes entered.'}

` +
    `AGREED STUDENT NEXT STEPS:
${state.studentNext || 'None recorded.'}

` +
    `MENTOR FOLLOW-UP COMMITMENTS:
${state.mentorFollow || 'None recorded.'}

` +
    `COMPLETED WORKFLOW TASKS:
${tasksDone || 'None marked complete.'}
`;
}

function buildSummary() {
  const completedLabels = WORKFLOW.flatMap(step => step.tasks).filter(task => state.checked[task.id]).map(task => `- ${task.title}`).join('\n');
  return `ENS 101 APPOINTMENT 1a SUMMARY

Student preferred name: ${state.student.name || 'Not entered'}
Major or program: ${state.student.program || 'Not entered'}
Career direction: ${state.student.career || 'Not entered'}
Career confidence: ${state.student.confidence || '5'}/10
Career Explorer roadmap: ${state.student.roadmap || 'Not selected'}
Next appointment: ${state.student.followup || 'Not selected'}

CONVERSATION NOTES
${state.sessionNotes || 'No notes entered.'}

STUDENT NEXT STEP
${state.studentNext || 'Not entered.'}

MENTOR FOLLOW-UP
${state.mentorFollow || 'Not entered.'}

COMPLETED APPOINTMENT TASKS
${completedLabels || 'None marked complete.'}

Privacy reminder: Keep this summary only in an approved location and follow applicable student-record policies.`;
}

async function handleCivitasConfirmation(checked) {
  state.civitasRecorded = checked;
  const delBtn = $('#btn-complete-delete-record');
  if (delBtn) delBtn.disabled = !checked;

  if (state.appointmentId) {
    if (checked) {
      try {
        await fetch('/api/appointments/civitas-confirm', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: state.appointmentId })
        });
      } catch (e) {
        console.error('Error confirming Civitas:', e);
      }
    }
    persistState();
  }
}

async function handleDeleteRecordAfterCivitas() {
  if (!state.civitasRecorded) {
    showToast('Please confirm recording in Civitas first.');
    return;
  }

  const studentName = state.student.name || 'this student';
  if (!confirm(`Are you sure you want to complete this appointment and permanently delete the record for ${studentName} from this workstation?`)) {
    return;
  }

  if (state.appointmentId) {
    try {
      const res = await fetch('/api/appointments/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: state.appointmentId })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to delete record.');
      showToast('Appointment completed! Student record deleted.');
    } catch (err) {
      showToast(err.message || 'Error deleting appointment.');
      return;
    }
  }

  resetAppointmentLocal();
  await fetchAppointmentsList();
}

function resetAppointmentLocal() {
  state = defaultState();
  localStorage.removeItem(ACTIVE_APPT_ID_KEY);
  syncInputsFromState();
  renderStep();
  renderChat();
  showToast('New student appointment ready');
}

async function copyText(text, successMessage) {
  try {
    await navigator.clipboard.writeText(text);
    showToast(successMessage);
  } catch {
    showToast('Copy unavailable—select manually.');
  }
}

function showToast(message) {
  const toast = $('#toast');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2500);
}

function resolveSuiteUrl(url) {
  if (!url) return '#';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
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
  if (dashBtn) dashBtn.href = resolveSuiteUrl('/');
  const internBtn = $('#btn-internship-expert');
  if (internBtn) internBtn.href = resolveSuiteUrl('/internship/');
}

function showView(viewName) {
  $$('.view').forEach(view => view.classList.toggle('active', view.id === `${viewName}-view`));
  $$('.top-nav-button').forEach(button => button.classList.toggle('active', button.dataset.view === viewName));
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderQuickTools() {
  const tools = RESOURCES.filter(r => ['connect', 'pathwayu', 'office', 'community'].includes(r.id));
  const el = $('#quick-tool-list');
  if (el) {
    el.innerHTML = tools.map(r => `<a class="quick-tool" href="${resolveSuiteUrl(r.url)}" target="_blank" rel="noopener"><span class="quick-tool-icon">${r.initials}</span><strong>${r.name}</strong></a>`).join('');
  }
}

function renderResources() {
  const filterRow = $('#resource-filters');
  if (!filterRow) return;
  const categories = ['All', ...new Set(RESOURCES.map(r => r.category))];
  filterRow.innerHTML = '';
  categories.forEach(cat => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `filter-button${cat === activeResourceFilter ? ' active' : ''}`;
    btn.textContent = cat;
    btn.addEventListener('click', () => { activeResourceFilter = cat; renderResources(); });
    filterRow.appendChild(btn);
  });

  const query = $('#resource-search')?.value.trim().toLowerCase() || '';
  const filtered = RESOURCES.filter(r => {
    const matchCat = activeResourceFilter === 'All' || r.category === activeResourceFilter;
    const haystack = `${r.name} ${r.description} ${r.category}`.toLowerCase();
    return matchCat && haystack.includes(query);
  });

  const grid = $('#resource-grid');
  if (grid) {
    grid.innerHTML = filtered.length ? filtered.map(r => `
      <a class="resource-card card" href="${resolveSuiteUrl(r.url)}" target="_blank" rel="noopener">
        <div class="resource-top"><span class="resource-icon">${r.initials}</span><svg class="resource-external" viewBox="0 0 24 24"><path d="M14 5h5v5M10 14 19 5"/><path d="M19 13v6H5V5h6"/></svg></div>
        <h2>${r.name}</h2><p>${r.description}</p><span class="resource-category${r.category === 'Appointment 1a' ? ' appointment-label' : ''}">${r.category}</span>
      </a>`).join('') : '<div class="resource-empty card"><strong>No matching resources</strong><p>Try a different search or category.</p></div>';
  }
}

function openCopilot(prefill = '') {
  $('#copilot-panel').classList.add('open');
  $('#open-copilot').hidden = true;
  if (prefill) $('#message-input').value = prefill;
  $('#message-input').focus();
}

function closeCopilot() {
  $('#copilot-panel').classList.remove('open');
  $('#open-copilot').hidden = false;
}

function formatAssistantMessage(text) {
  const escaped = String(text)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  let formatted = escaped.replace(
    /\[([^\]]+)\]\(((?:https?:\/\/|\/)[^\s\)"']+)\)/g,
    (_match, label, rawUrl) => `<a href="${resolveSuiteUrl(rawUrl)}" target="_blank" rel="noopener noreferrer" class="chat-link">${label} &#8599;</a>`
  );
  formatted = formatted.replace(
    /(^|[\s(])(https?:\/\/[^\s\)"']+)/g,
    (_match, prefix, rawUrl) => `${prefix}<a href="${rawUrl}" target="_blank" rel="noopener noreferrer" class="chat-link">${rawUrl} &#8599;</a>`
  );
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  return formatted.replace(/\n/g, '<br>');
}

function addMessage(role, text, responseId = '') {
  const article = document.createElement('article');
  article.className = `message ${role}`;
  const label = document.createElement('small');
  label.textContent = role === 'assistant' ? 'Mentor Copilot' : 'You';
  const body = document.createElement('div');
  body.className = 'message-body';
  if (role === 'assistant') {
    body.innerHTML = formatAssistantMessage(text);
  } else {
    body.textContent = text;
  }
  article.append(label, body);
  $('#messages').appendChild(article);
  $('#messages').scrollTop = $('#messages').scrollHeight;
}

function renderChat() {
  $('#messages').innerHTML = '';
  if (!state.chatHistory.length) {
    addMessage('assistant', 'I’m here to support your preparation and appointment—not replace your judgment. Ask me for a thoughtful question, a resource match, or guidance.');
  } else {
    state.chatHistory.forEach(item => addMessage(item.role, item.content));
  }
}

function renderCopilotSuggestions() {
  const suggestions = $('#suggestions');
  if (!suggestions) return;
  suggestions.innerHTML = '';
  const prompts = state.currentTask === 'prepare'
    ? (PREPARE_STEPS[state.currentStep]?.copilot || ['Help me prepare for this appointment', 'Explain PathwayU'])
    : (WORKFLOW[state.currentStep]?.copilot || ['Suggest a question', 'Recommend next steps']);

  prompts.forEach(p => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = p;
    btn.addEventListener('click', () => openCopilot(p));
    suggestions.appendChild(btn);
  });
}

async function submitCopilot(message) {
  openCopilot();
  addMessage('user', message);
  state.chatHistory.push({ role: 'user', content: message });
  $('#service-status').textContent = 'Thinking…';
  $('#send-button').disabled = true;

  const context = [
    state.student.name && `Student: ${state.student.name}.`,
    state.student.program && `Major: ${state.student.program}.`,
    state.student.career && `Career: ${state.student.career}.`,
    `Confidence: ${state.student.confidence}/10.`,
    state.assessmentData?.holland_code && `Holland Code: ${state.assessmentData.holland_code}.`,
    state.prepNotes && `Prep notes: ${state.prepNotes}`
  ].filter(Boolean).join(' ');

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: context ? `${message}

Appointment context: ${context}` : message,
        mode: state.currentTask === 'prepare' ? 'step1' : WORKFLOW[state.currentStep].id,
        history: state.chatHistory.slice(0, -1).slice(-8)
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Copilot could not respond.');
    addMessage('assistant', data.reply, data.response_id);
    state.chatHistory.push({ role: 'assistant', content: data.reply });
  } catch (err) {
    addMessage('assistant', err.message || 'Please try again.');
  } finally {
    $('#service-status').textContent = 'Ready';
    $('#send-button').disabled = false;
  }
}

function openSuggestionModal() {
  const dialog = $('#suggestion-dialog');
  if (dialog) { dialog.hidden = false; $('#suggestion-text')?.focus(); }
}
function closeSuggestionModal() {
  const dialog = $('#suggestion-dialog');
  if (dialog) dialog.hidden = true;
}

async function handleSuggestionSubmit(e) {
  e.preventDefault();
  const submitBtn = $('#submit-suggestion-btn');
  const category = $('#suggestion-category').value;
  const suggestion = $('#suggestion-text').value.trim();
  const submitter = $('#suggestion-submitter').value.trim();

  if (!suggestion) return;
  submitBtn.disabled = true;
  try {
    const res = await fetch('/api/suggestions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, suggestion, submitter })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed to submit.');
    showToast(data.message || 'Thank you! Suggestion submitted.');
    $('#suggestion-text').value = '';
    closeSuggestionModal();
  } catch (err) {
    showToast(err.message || 'Error submitting suggestion.');
  } finally {
    submitBtn.disabled = false;
  }
}

function bindEvents() {
  $$('.top-nav-button').forEach(btn => btn.addEventListener('click', () => showView(btn.dataset.view)));
  $$('[data-view-jump]').forEach(btn => btn.addEventListener('click', () => showView(btn.dataset.viewJump)));
  $('#resource-search')?.addEventListener('input', renderResources);

  const switcher = $('#student-switcher');
  if (switcher) {
    switcher.addEventListener('change', async (e) => {
      await loadAppointmentById(e.target.value);
    });
  }

  $('#new-appointment')?.addEventListener('click', () => {
    $('#confirm-dialog').hidden = false;
  });
  $('#cancel-reset')?.addEventListener('click', () => {
    $('#confirm-dialog').hidden = true;
  });
  $('#confirm-reset')?.addEventListener('click', () => {
    $('#confirm-dialog').hidden = true;
    resetAppointmentLocal();
  });
  $('#confirm-dialog')?.addEventListener('click', (e) => {
    if (e.target === $('#confirm-dialog')) $('#confirm-dialog').hidden = true;
  });

  $('#prep-career-lookup-btn')?.addEventListener('click', () => {
    const email = $('#prep-student-email')?.value.trim();
    performStudentLookup(email);
  });

  $('#career-lookup-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = $('#career-student-email')?.value.trim();
    performStudentLookup(email);
  });

  $('#career-auth-button')?.addEventListener('click', launchCareerExplorerLogin);
  $('#prep-career-auth-btn')?.addEventListener('click', launchCareerExplorerLogin);

  const dropzone = $('#prep-pdf-dropzone');
  const fileInput = $('#prep-pdf-input');
  if (dropzone && fileInput) {
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files?.length) {
        handlePdfUpload(e.dataTransfer.files[0]);
      }
    });
    fileInput.addEventListener('change', (e) => {
      if (e.target.files?.length) {
        handlePdfUpload(e.target.files[0]);
      }
    });
  }

  $('#btn-prep-to-step2')?.addEventListener('click', async () => {
    state.currentStep = 1;
    persistState();
    renderStep();
    await fetchCareerGuidance();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  $('#btn-guidance-back')?.addEventListener('click', () => {
    state.currentStep = 0;
    persistState();
    renderStep();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  $('#btn-guidance-to-step3')?.addEventListener('click', () => {
    state.currentStep = 2;
    persistState();
    renderStep();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  $('#btn-notes-back')?.addEventListener('click', () => {
    state.currentStep = 1;
    persistState();
    renderStep();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  $('#btn-copy-guidance-notes')?.addEventListener('click', () => {
    if (!state.guidance) return;
    const g = state.guidance;
    const summaryText = `
--- CAREER EXPLORER INSIGHTS ---
` +
      `Holland Code: ${g.holland_code || 'SEC'}
` +
      `Aligned Majors: ${(g.aligned_majors || []).join(', ')}
` +
      `Top Careers: ${(g.aligned_careers || []).join(', ')}
` +
      `Discussion Strategy:
${(g.sections?.find(s => s.title.includes('Discussion Strategy'))?.content || '')}
`;

    state.prepNotes = (state.prepNotes ? state.prepNotes.trim() + '\n' : '') + summaryText;
    if ($('#prep-notes-textarea')) $('#prep-notes-textarea').value = state.prepNotes;
    persistState();
    showToast('Guidance summary appended to Prep Notes!');
  });

  $$('.prompt-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const prompt = btn.dataset.prompt;
      if (!prompt) return;
      state.prepNotes = (state.prepNotes ? state.prepNotes.trim() + '\n• ' : '• ') + prompt;
      if ($('#prep-notes-textarea')) $('#prep-notes-textarea').value = state.prepNotes;
      persistState();
      showToast('Prompt added to notes');
    });
  });

  $('#btn-start-task2')?.addEventListener('click', () => {
    state.currentTask = 'appointment';
    state.currentStep = 0;
    persistState();
    renderStep();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    showToast('Task 2: Begin Appointment started!');
  });

  $('#previous-step')?.addEventListener('click', () => {
    if (state.currentStep > 0) {
      state.currentStep--;
      persistState();
      renderStep();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });

  $('#next-step')?.addEventListener('click', () => {
    if (state.currentStep < WORKFLOW.length - 1) {
      state.currentStep++;
      persistState();
      renderStep();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      showToast(completedTasks() === totalTasks() ? 'Appointment workflow complete' : 'Review unfinished tasks before logging Civitas');
    }
  });

  $('#btn-toggle-prep-preview')?.addEventListener('click', () => {
    const body = $('#prep-preview-content');
    const chevron = $('#prep-preview-chevron');
    if (body) {
      body.hidden = !body.hidden;
      if (chevron) chevron.textContent = body.hidden ? '▼' : '▲';
    }
  });

  $('#btn-copy-civitas')?.addEventListener('click', () => {
    copyText(buildCivitasNote(), 'Civitas Advising Note copied to clipboard!');
  });

  $('#civitas-confirm-checkbox')?.addEventListener('change', (e) => {
    handleCivitasConfirmation(e.target.checked);
  });

  $('#btn-complete-delete-record')?.addEventListener('click', handleDeleteRecordAfterCivitas);

  $('#copy-summary')?.addEventListener('click', () => {
    copyText(buildSummary(), 'Appointment summary copied to clipboard');
  });

  $('#open-copilot')?.addEventListener('click', () => openCopilot());
  $('#close-copilot')?.addEventListener('click', closeCopilot);
  $('#chat-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const msg = $('#message-input').value.trim();
    if (msg) {
      $('#message-input').value = '';
      submitCopilot(msg);
    }
  });
  $('#message-input')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      $('#chat-form').requestSubmit();
    }
  });

  $('#open-suggestion-modal')?.addEventListener('click', openSuggestionModal);
  $('#close-suggestion-dialog')?.addEventListener('click', closeSuggestionModal);
  $('#cancel-suggestion')?.addEventListener('click', closeSuggestionModal);
  $('#suggestion-dialog')?.addEventListener('click', (e) => {
    if (e.target === $('#suggestion-dialog')) closeSuggestionModal();
  });
  $('#suggestion-form')?.addEventListener('submit', handleSuggestionSubmit);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      $('#confirm-dialog').hidden = true;
      closeSuggestionModal();
      closeCopilot();
    }
  });
}

async function loadServiceStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    const active = data.active_engine || (data.ai_configured ? 'Qwen Local' : 'Offline Guidance');
    const badge = $('#ai-engine-badge');
    const nameEl = $('#ai-engine-name');
    if (nameEl) nameEl.textContent = active;
    if (badge) {
      const isGemini = active.toLowerCase().includes('gemini');
      const isOffline = active.toLowerCase().includes('offline') || active.toLowerCase().includes('not configured');
      badge.className = `engine-indicator-pill ${isOffline ? 'engine-offline' : (isGemini ? 'engine-gemini' : 'engine-qwen')}`;
    }
  } catch {
  }
}

async function init() {
  bindSessionFields();
  bindEvents();
  configureTopLinks();
  renderQuickTools();
  renderResources();

  await fetchAppointmentsList();

  const activeApptId = localStorage.getItem(ACTIVE_APPT_ID_KEY);
  if (activeApptId) {
    await loadAppointmentById(activeApptId);
  } else {
    renderStep();
    renderChat();
  }

  loadServiceStatus();
  checkCareerExplorerSession();
}

init();
