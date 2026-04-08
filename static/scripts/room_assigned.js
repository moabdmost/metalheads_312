document.addEventListener('DOMContentLoaded', () => {

  // Read from data attribute — works regardless of URL structure
  const submissionId = document.querySelector('[data-submission-id]')
                         ?.dataset.submissionId;

  if (!submissionId) {
    console.error('No submission ID found on page');
    return;
  }

  const POLL_INTERVAL = 3000;
  let poller;

async function poll() {
    try {
      const res = await fetch(`/api/submissions/${submissionId}`);
      if (!res.ok) return;
      const sub = await res.json();
      console.log('full sub:', JSON.stringify(sub));  // ADD THIS
      console.log('sub.room =', sub.room);
      if (sub.room) showAssigned(sub);
    } catch (err) {
      console.error('poll error:', err);
    }
  }

  function showAssigned(sub) {
    clearInterval(poller);
    const roomFull   = sub.room || '—';
    const roomNumber = roomFull.replace('Watson ', '').trim();
    document.getElementById('room-number').textContent   = roomFull.startsWith('Watson') ? roomNumber : roomFull;
    document.getElementById('detail-course').textContent = `${sub.courseCode} — ${sub.courseName}`;
    document.getElementById('detail-prof').textContent   = sub.facultyName || '—';
    document.getElementById('detail-accom').textContent  = sub.notes       || 'None';
    document.getElementById('detail-subid').textContent  = sub.id;
    document.getElementById('waiting-view').style.display  = 'none';
    document.getElementById('assigned-view').style.display = 'block';
  }

  poller = setInterval(poll, POLL_INTERVAL);
  poll();

});