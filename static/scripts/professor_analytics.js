const API_BASE = "http://127.0.0.1:5000/api";

let allSubmissions = [];
let filteredSubmissions = [];

// Load data on page load
window.addEventListener('DOMContentLoaded', () => {
    loadSubmissions();
    
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    document.getElementById('exportPDF').addEventListener('click', exportPDF);
    document.getElementById('exportCSV').addEventListener('click', exportCSV);
});

async function loadSubmissions() {
    try {
        const response = await fetch(`${API_BASE}/submissions`);
        allSubmissions = await response.json();
        
        // Populate course filter
        populateCourseFilter();
        
        // Show all data initially
        filteredSubmissions = allSubmissions;
        renderTable();
        updateStats();
        
    } catch (error) {
        console.error('Failed to load submissions:', error);
        alert('Failed to load data');
    }
}

function populateCourseFilter() {
    const courseFilter = document.getElementById('courseFilter');
    const courses = new Set();
    
    allSubmissions.forEach(sub => {
        courses.add(`${sub.courseCode} - ${sub.courseName}`);
    });
    
    courses.forEach(course => {
        const option = document.createElement('option');
        option.value = course.split(' - ')[0]; // Just the code
        option.textContent = course;
        courseFilter.appendChild(option);
    });
}

function applyFilters() {
    const courseFilter = document.getElementById('courseFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    filteredSubmissions = allSubmissions.filter(sub => {
        // Course filter
        if (courseFilter && sub.courseCode !== courseFilter) {
            return false;
        }
        
        // Status filter
        if (statusFilter && sub.status !== statusFilter) {
            return false;
        }
        
        // Date filters
        if (startDate) {
            const checkInDate = new Date(sub.checkInTime).toISOString().split('T')[0];
            if (checkInDate < startDate) {
                return false;
            }
        }
        
        if (endDate) {
            const checkInDate = new Date(sub.checkInTime).toISOString().split('T')[0];
            if (checkInDate > endDate) {
                return false;
            }
        }
        
        return true;
    });
    
    renderTable();
    updateStats();
}

function renderTable() {
    const tbody = document.getElementById('analyticsRows');
    tbody.innerHTML = '';
    
    filteredSubmissions.forEach(sub => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${sub.id}</td>
            <td><b>${sub.studentName}</b><br><span class="muted">${sub.studentId}</span></td>
            <td><b>${sub.courseCode}</b> — ${sub.courseName}<br>${sub.examName}</td>
            <td>${formatTime(sub.checkInTime)}</td>
            <td>${formatTime(sub.checkOutTime)}</td>
            <td>${pill(sub.status)}</td>
            <td>${sub.facultyName}</td>
        `;
        tbody.appendChild(row);
    });
}

function updateStats() {
    const total = filteredSubmissions.length;
    const completed = filteredSubmissions.filter(s => s.status === 'COMPLETED').length;
    const inProgress = filteredSubmissions.filter(s => s.status === 'IN_PROGRESS').length;
    const pending = filteredSubmissions.filter(s => s.status === 'PENDING').length;
    
    document.getElementById('totalCount').textContent = total;
    document.getElementById('completedCount').textContent = completed;
    document.getElementById('inProgressCount').textContent = inProgress;
    document.getElementById('pendingCount').textContent = pending;
}

function formatTime(t) {
    if (!t) return "—";
    return t.replace("T", " ");
}

function pill(status) {
    const label = status.replace(/_/g, ' ');
    return `<span class="pill" data-status="${status}">${label}</span>`;
}

async function exportPDF() {
    try {
        // Build query params from current filters
        const params = new URLSearchParams();
        
        const courseFilter = document.getElementById('courseFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (courseFilter) params.append('course', courseFilter);
        if (statusFilter) params.append('status', statusFilter);
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        // Trigger download
        window.location.href = `${API_BASE}/export-pdf?${params.toString()}`;
        
    } catch (error) {
        console.error('PDF export failed:', error);
        alert('Failed to export PDF');
    }
}

async function exportCSV() {
    try {
        // Build query params from current filters
        const params = new URLSearchParams();
        
        const courseFilter = document.getElementById('courseFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (courseFilter) params.append('course', courseFilter);
        if (statusFilter) params.append('status', statusFilter);
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        // Trigger download
        window.location.href = `${API_BASE}/export-csv?${params.toString()}`;
        
    } catch (error) {
        console.error('CSV export failed:', error);
        alert('Failed to export CSV');
    }
}
