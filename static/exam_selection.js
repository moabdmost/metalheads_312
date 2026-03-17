// JavaScript for exam_selection.html
// Populates course and exam dropdowns ONLY for the logged-in student

window.addEventListener('DOMContentLoaded', () => {
    // Check if student is logged in
    const loggedInStudent = JSON.parse(localStorage.getItem('loggedInStudent'));
    
    if (!loggedInStudent) {
        alert('Please log in first');
        window.location.href = '/student';
        return;
    }
    
    loadCoursesForStudent(loggedInStudent.studentId);
    
    const form = document.getElementById('examForm');
    const courseSelect = document.getElementById('courseSelect');
    const examSelect = document.getElementById('examSelect');
    
    // When course is selected, populate exams
    courseSelect.addEventListener('change', () => {
        loadExamsForStudent(courseSelect.value, loggedInStudent.studentId);
    });
    
    // Handle form submission
    form.addEventListener('submit', handleSubmit);
});

let studentSubmissions = [];

async function loadCoursesForStudent(studentId) {
    try {
        const response = await fetch('/api/submissions');
        const allSubmissions = await response.json();
        
        // Filter to only this student's submissions
        studentSubmissions = allSubmissions.filter(sub => sub.studentId === studentId);
        
        if (studentSubmissions.length === 0) {
            alert('No exams found for your account.');
            return;
        }
        
        // Get unique courses for this student
        const courses = {};
        studentSubmissions.forEach(sub => {
            const key = sub.courseCode;
            if (!courses[key]) {
                courses[key] = {
                    code: sub.courseCode,
                    name: sub.courseName
                };
            }
        });
        
        // Populate course dropdown
        const courseSelect = document.getElementById('courseSelect');
        courseSelect.innerHTML = '<option value="">-- Choose a course --</option>';
        
        Object.values(courses).forEach(course => {
            const option = document.createElement('option');
            option.value = course.code;
            option.textContent = `${course.code} - ${course.name}`;
            courseSelect.appendChild(option);
        });
        
    } catch (err) {
        console.error('Failed to load courses:', err);
        alert('Unable to load courses. Please refresh the page.');
    }
}

function loadExamsForStudent(courseCode, studentId) {
    const examSelect = document.getElementById('examSelect');
    
    if (!courseCode) {
        examSelect.innerHTML = '<option value="">-- First select a course --</option>';
        examSelect.disabled = true;
        return;
    }
    
    // Filter exams by selected course AND this student
    const exams = studentSubmissions
        .filter(sub => sub.courseCode === courseCode)
        .map(sub => ({
            id: sub.id,
            name: sub.examName
        }));
    
    // Populate exam dropdown
    examSelect.innerHTML = '<option value="">-- Choose an exam --</option>';
    exams.forEach(exam => {
        const option = document.createElement('option');
        option.value = exam.id;
        option.textContent = exam.name;
        examSelect.appendChild(option);
    });
    
    examSelect.disabled = false;
}

function handleSubmit(event) {
    event.preventDefault();
    
    const courseSelect = document.getElementById('courseSelect');
    const examSelect = document.getElementById('examSelect');
    
    if (!courseSelect.value) {
        alert('Please select a course.');
        return;
    }
    
    if (!examSelect.value) {
        alert('Please select an exam.');
        return;
    }
    
    // Save the selected exam to localStorage for the thank you page
    const selectedSubmission = studentSubmissions.find(sub => sub.id === examSelect.value);
    localStorage.setItem('selectedExam', JSON.stringify(selectedSubmission));
    
    // Redirect to thank you page
    window.location.href = '/thankyou';
}
