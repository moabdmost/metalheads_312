// ── Pull submission ID from the URL: /room-assigned/<id> ──────────────────
    //const submissionId = window.location.pathname.split('/').pop();
    const parts = window.location.pathname.split('/').filter(p => p.length > 0);
    const submissionId = parts[parts.length - 1];
    console.log('URL:', window.location.pathname, '→ ID:', submissionId);
    const POLL_INTERVAL = 3000; // check every 3 seconds

    async function poll() {
      try {
        const res  = await fetch(`/api/submissions/${submissionId}`);
        if (!res.ok) return;
        const sub  = await res.json();

        if (sub.room) {
          showAssigned(sub);
        }
      } catch {
        // silently retry
      }
    }

    function showAssigned(sub) {
      clearInterval(poller);

      // Extract just the room number from e.g. "Watson 109"
      const roomFull   = sub.room || '—';
      const roomNumber = roomFull.replace('Watson ', '').trim();

      document.getElementById('room-number').textContent    = roomFull.startsWith('Watson') ? roomNumber : roomFull;
      document.getElementById('detail-exam').textContent    = sub.examName    || '—';
      document.getElementById('detail-course').textContent  = `${sub.courseCode} — ${sub.courseName}`;
      document.getElementById('detail-prof').textContent    = sub.facultyName  || '—';
      document.getElementById('detail-accom').textContent   = sub.notes        || 'None';
      document.getElementById('detail-subid').textContent   = sub.id;

      // Swap views
      document.getElementById('waiting-view').style.display  = 'none';
      document.getElementById('assigned-view').style.display = '';
    }

    const poller = setInterval(poll, POLL_INTERVAL);
    poll(); // immediate first check