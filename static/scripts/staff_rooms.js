let allRooms = [];

    // ── Load rooms from API ───────────────────────────────────────────────────
    async function loadRooms() {
      try {
        const res   = await fetch('/api/rooms');
        if (!res.ok) throw new Error('Failed');
        allRooms    = await res.json();
        renderRooms(allRooms);
        updateStats(allRooms);
        document.getElementById('last-updated').textContent =
          'Updated ' + new Date().toLocaleTimeString();
      } catch (e) {
        ['general','reduced','individual'].forEach(g => {
          document.getElementById(`grid-${g}`).innerHTML =
            `<div class="state-msg">Could not load rooms.</div>`;
        });
      }
    }

    // ── Render into section grids ─────────────────────────────────────────────
    function renderRooms(rooms) {
      const sections = { general: [], reduced: [], individual: [] };

      for (const r of rooms) {
        const t = (r.type || '').toLowerCase();
        if (t === 'general')    sections.general.push(r);
        else if (t === 'reduced') sections.reduced.push(r);
        else                    sections.individual.push(r); // individual + aadr
      }

      for (const [key, list] of Object.entries(sections)) {
        const grid = document.getElementById(`grid-${key}`);
        if (!list.length) {
          grid.innerHTML = `<div class="state-msg">No rooms in this category.</div>`;
          continue;
        }
        grid.innerHTML = list.map(r => roomCardHTML(r)).join('');
      }

      // Attach toggle listeners
      document.querySelectorAll('.toggle-switch input').forEach(cb => {
        cb.addEventListener('change', () => handleToggle(cb));
      });

      // Clicking card body also toggles
      document.querySelectorAll('.room-card').forEach(card => {
        card.addEventListener('click', (e) => {
          // Don't double-fire if clicking directly on checkbox
          if (e.target.tagName === 'INPUT') return;
          const cb = card.querySelector('.toggle-switch input');
          if (cb) { cb.checked = !cb.checked; handleToggle(cb); }
        });
      });
    }

    function roomCardHTML(r) {
      const staffed    = r.staffed;
      const occupants  = r.occupants || 0;
      const capacity   = r.capacity  || '—';
      const typeName   = (r.type || 'general').toLowerCase();

      const typeLabel  = {
        general:    'General',
        reduced:    'Reduced Distraction',
        individual: 'Individual',
        aadr:       'AADR',
      }[typeName] || typeName;

      return `
        <div class="room-card ${staffed ? 'is-staffed' : ''}" data-room-id="${r.id}">
          <div class="room-card-top">
            <span class="room-name">${r.id}</span>
            <span class="room-type-badge ${typeName}">${typeLabel}</span>
          </div>

          <div class="room-meta">
            <div class="room-meta-item">
              <span class="room-meta-label">Capacity</span>
              <span class="room-meta-value">${capacity}</span>
            </div>
            <div class="room-meta-item">
              <span class="room-meta-label">Occupied</span>
              <span class="room-meta-value">${occupants}</span>
            </div>
            <div class="room-meta-item">
              <span class="room-meta-label">Available</span>
              <span class="room-meta-value">${capacity === '—' ? '—' : capacity - occupants}</span>
            </div>
          </div>

          <div class="room-toggle-row">
            <span class="toggle-label">${staffed ? '✓ Staffed' : 'Unstaffed'}</span>
            <label class="toggle-switch" onclick="event.stopPropagation()">
              <input type="checkbox" data-room-id="${r.id}" ${staffed ? 'checked' : ''}/>
              <span class="toggle-track"></span>
            </label>
          </div>
        </div>
      `;
    }

    // ── Handle staffed toggle ─────────────────────────────────────────────────
    async function handleToggle(checkbox) {
      const roomId  = checkbox.dataset.roomId;
      const staffed = checkbox.checked;

      // Optimistic UI update
      const card = document.querySelector(`.room-card[data-room-id="${roomId}"]`);
      if (card) {
        card.classList.toggle('is-staffed', staffed);
        const label = card.querySelector('.toggle-label');
        if (label) label.textContent = staffed ? '✓ Staffed' : 'Unstaffed';
      }

      try {
        const res = await fetch(`/api/rooms/${encodeURIComponent(roomId)}`, {
          method:  'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ staffed }),
        });
        if (!res.ok) throw new Error('Save failed');
        showToast(staffed ? `${roomId} marked as staffed` : `${roomId} marked as unstaffed`);

        // Update local state
        const room = allRooms.find(r => r.id === roomId);
        if (room) room.staffed = staffed;
        updateStats(allRooms);

      } catch (e) {
        // Revert on failure
        checkbox.checked = !staffed;
        if (card) {
          card.classList.toggle('is-staffed', !staffed);
          const label = card.querySelector('.toggle-label');
          if (label) label.textContent = !staffed ? '✓ Staffed' : 'Unstaffed';
        }
        showToast('Failed to save — please try again', true);
      }
    }

    // ── Stats ─────────────────────────────────────────────────────────────────
    function updateStats(rooms) {
      const staffed   = rooms.filter(r => r.staffed).length;
      const unstaffed = rooms.length - staffed;
      const occupied  = rooms.filter(r => (r.occupants || 0) > 0).length;
      document.getElementById('stat-staffed').textContent   = staffed;
      document.getElementById('stat-unstaffed').textContent = unstaffed;
      document.getElementById('stat-occupied').textContent  = occupied;
    }

    // ── Toast ─────────────────────────────────────────────────────────────────
    let toastTimer;
    function showToast(msg, isError = false) {
      const el = document.getElementById('toast');
      el.textContent = msg;
      el.style.color = isError ? 'var(--danger)' : 'var(--success)';
      el.classList.add('show');
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => el.classList.remove('show'), 2500);
    }

    // ── Init ──────────────────────────────────────────────────────────────────
    loadRooms();
    setInterval(loadRooms, 15000); // auto-refresh every 15s