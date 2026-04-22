

const API_BASE = "/api";

let allSubmissions = [];
let filteredSubmissions = [];

// ── Init ──────────────────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
    loadSubmissions();
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    document.getElementById('exportPDF').addEventListener('click', exportPDF);
    document.getElementById('exportCSV').addEventListener('click', exportCSV);
});


// ── Data loading ──────────────────────────────────────────────────────────────

/**
 * Loads all submission records from the server and refreshes the analytics UI.
 * This includes populating the course filter, rendering the table, and updating summary counts.
 * @param {void}
 * @returns {void}
 */
async function loadSubmissions() {
    try {
        const response = await fetch(`${API_BASE}/submissions`);
        allSubmissions = await response.json();
        populateCourseFilter();
        filteredSubmissions = allSubmissions;
        renderTable();
        updateStats();
    } catch (error) {
        console.error('Failed to load submissions:', error);
        alert('Failed to load data. Make sure the Flask server is running.');
    }
}

/**
 * Builds the course dropdown filter options from loaded submissions.
 * @param {void}
 * @returns {void}
 */
function populateCourseFilter() {
    const courseFilter = document.getElementById('courseFilter');
    const courses = new Set();

    allSubmissions.forEach(sub => {
        if (sub.courseCode && sub.courseName) {
            courses.add(`${sub.courseCode} - ${sub.courseName}`);
        }
    });

    courses.forEach(course => {
        const option = document.createElement('option');
        option.value = course.split(' - ')[0];
        option.textContent = course;
        courseFilter.appendChild(option);
    });
}


// ── Filtering ─────────────────────────────────────────────────────────────────

/**
 * Applies the current course, status, and date filters to the submissions.
 * Updates the table and summary statistics after filtering.
 * @param: None. Reads filter values from the UI, applies them to the submissions,
 * @returns {Boolean}   Updates the table and summary statistics after filtering.
 */
function applyFilters() {
    const courseFilter = document.getElementById('courseFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    const startDate    = document.getElementById('startDate').value;
    const endDate      = document.getElementById('endDate').value;

    filteredSubmissions = allSubmissions.filter(sub => {
        if (courseFilter && sub.courseCode !== courseFilter) return false;
        if (statusFilter && sub.status !== statusFilter)     return false;

        if (startDate && sub.checkInTime) {
            const d = sub.checkInTime.split('T')[0];
            if (d < startDate) return false;
        }
        if (endDate && sub.checkInTime) {
            const d = sub.checkInTime.split('T')[0];
            if (d > endDate) return false;
        }
        return true;
    });

    renderTable();
    updateStats();
}


// ── Rendering ─────────────────────────────────────────────────────────────────

/**
 * Renders the analytics table rows for the currently filtered submissions.
 * @param: None. Renders the analytics table rows for the currently filtered submissions.
 * @returns: None. Renders the analytics table rows for the currently filtered submissions.
 */
function renderTable() {
    const tbody = document.getElementById('analyticsRows');
    tbody.innerHTML = '';

    if (filteredSubmissions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted); padding:32px;">No submissions match the current filters.</td></tr>`;
        return;
    }

    filteredSubmissions.forEach(sub => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${sub.id}</td>
            <td><b>${sub.studentName || '—'}</b><br><span class="muted">${sub.studentId || '—'}</span></td>
            <td><b>${sub.courseCode || '—'}</b> — ${sub.courseName || '—'}<br><span class="muted">${sub.examName || '—'}</span></td>
            <td>${formatTime(sub.checkInTime)}</td>
            <td>${formatTime(sub.checkOutTime)}</td>
            <td>${calculateTotalTime(sub.checkInTime, sub.checkOutTime)}</td>
            <td>${pill(sub.status)}</td>
            <td>${sub.facultyName || '—'}</td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Updates the summary statistics shown in the analytics dashboard.
 * @param: None. Updates the summary statistics shown in the analytics dashboard.
 * @returns: None. Updates the summary statistics shown in the analytics dashboard.
 */
function updateStats() {
    const total      = filteredSubmissions.length;
    const completed  = filteredSubmissions.filter(s => s.status === 'COMPLETED').length;
    const inProgress = filteredSubmissions.filter(s => s.status === 'IN_PROGRESS').length;
    const pending    = filteredSubmissions.filter(s => s.status === 'PENDING').length;

    document.getElementById('totalCount').textContent      = total;
    document.getElementById('completedCount').textContent  = completed;
    document.getElementById('inProgressCount').textContent = inProgress;
    document.getElementById('pendingCount').textContent    = pending;
}


// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Formats an ISO timestamp for display in the analytics table.
 * @param {string} t - The timestamp string to format.
 * @returns {string} A more human-readable timestamp or a placeholder.
 */
function formatTime(t) {
    if (!t) return "—";
    return t.replace("T", " ");
}

/**
 * Calculates the total time spent based on check-in and check-out timestamps.
 * @param {string} checkIn - The check-in timestamp.
 * @param {string} checkOut - The check-out timestamp.
 * @return {string} The total time in "HH:mm:ss" format or a placeholder if not calculable.
 */
function calculateTotalTime(checkIn, checkOut) {
    const clockIn= new Date(checkIn);
    const clockOut= new Date(checkOut);
    if (isNaN(clockIn) || isNaN(clockOut)) return "—";
    const diffMs = clockOut - clockIn;
    if (diffMs < 0) return "—";
    const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);

    const string= hours.toString().padStart(2,0) + ":" + minutes.toString().padStart(2,0) + ":" + seconds.toString().padStart(2,0)+ "";
    return string;


}   


/**
 * Converts a submission status into a styled pill label.
 * @param {string} status - The status value to render.
 * @returns {string} HTML markup for a styled status pill.
 */
function pill(status) {
    const label = (status || 'UNKNOWN').replace(/_/g, ' ');
    return `<span class="pill" data-status="${status}">${label}</span>`;
}


// ── PDF Export (client-side via jsPDF) ────────────────────────────────────────
// Requires in your HTML <head>:
//   <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
//   <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.2/jspdf.plugin.autotable.min.js"></script>

/**
 * Exports the currently filtered analytics data to a PDF document.
 * This client-side function requires jsPDF and autotable to be loaded.
 * @param {void}
 * @returns {void}
 */
function exportPDF() {
    if (typeof window.jspdf === 'undefined') {
        alert('PDF library not loaded. Make sure jsPDF script tags are in your HTML.');
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: "landscape", unit: "pt", format: "letter" });

    // Header
    doc.setFontSize(18);
    doc.setTextColor(79, 142, 247);
    doc.text("Davidson College Quiz Center", 40, 40);

    doc.setFontSize(11);
    doc.setTextColor(180, 180, 200);
    doc.text("Professor Analytics Report", 40, 58);

    // Timestamp
    const now = new Date().toLocaleString();
    doc.setFontSize(9);
    doc.setTextColor(120, 120, 150);
    doc.text(`Generated: ${now}`, 40, 72);

    // Filter summary
    const courseVal = document.getElementById('courseFilter').value || 'All';
    const statusVal = document.getElementById('statusFilter').value || 'All';
    const startVal  = document.getElementById('startDate').value   || 'Any';
    const endVal    = document.getElementById('endDate').value     || 'Any';
    doc.text(`Filters — Course: ${courseVal}  |  Status: ${statusVal}  |  Date: ${startVal} → ${endVal}  |  Showing: ${filteredSubmissions.length} records`, 40, 84);

    // Table
    doc.autoTable({
        startY: 96,
        head: [["ID", "Student", "Student ID", "Course", "Check-In", "Check-Out", "Total Time", "Status", "Faculty"]],
        body: filteredSubmissions.map(s => [
            s.id || "—",
            s.studentName || "—",
            s.studentId || "—",
            `${s.courseCode || ""} ${s.courseName || ""}`.trim() || "—",
            formatTime(s.checkInTime),
            formatTime(s.checkOutTime),
            calculateTotalTime(s.checkInTime, s.checkOutTime),
            (s.status || "—").replace(/_/g, " "),
            s.facultyName || "—"
        ]),
        styles: {
            fontSize: 8,
            cellPadding: 5,
            textColor: [232, 234, 246],
            fillColor: [34, 38, 58]
        },
        headStyles: {
            fillColor: [79, 142, 247],
            textColor: [255, 255, 255],
            fontStyle: "bold",
            fontSize: 8
        },
        alternateRowStyles: {
            fillColor: [26, 29, 39]
        },
        tableLineColor: [46, 51, 80],
        tableLineWidth: 0.5,
    });

    // Footer on each page
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(100, 100, 130);
        doc.text(
            `Davidson College Quiz Center  —  Page ${i} of ${pageCount}`,
            doc.internal.pageSize.getWidth() / 2,
            doc.internal.pageSize.getHeight() - 16,
            { align: "center" }
        );
    }

    doc.save(`quiz-center-report-${new Date().toISOString().split('T')[0]}.pdf`);
}


// ── CSV Export (client-side, no server needed) ────────────────────────────────

/**
 * Exports the currently filtered analytics data to a CSV file.
 * The CSV is generated client-side and downloaded without server interaction.
 * @param {void}
 * @returns {void}
 */
function exportCSV() {
    const headers = ["ID", "Student Name", "Student ID", "Course Code", "Course Name",
                     "Check-In", "Check-Out", "Total Time", "Status", "Faculty", "Notes"];

    const rows = filteredSubmissions.map(s => [
        s.id            || "",
        s.studentName   || "",
        s.studentId     || "",
        s.courseCode    || "",
        s.courseName    || "",
        formatTime(s.checkInTime),
        formatTime(s.checkOutTime),
        calculateTotalTime(s.checkInTime, s.checkOutTime),
        s.status        || "",
        s.facultyName   || "",
    ]);

    const csv = [headers, ...rows]
        .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(","))
        .join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `quiz-center-report-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}