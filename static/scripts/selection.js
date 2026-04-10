    const COURSES = {
      "Dr. Ramanujan": [
        "CSC371 - Machine Learning",
        "CSC324 - Theory of Computation",
        "CSC250 - Computer Organization",
      ],
      "Dr. Lim": [
        "CSC221 - Data Structures",
        "CSC312 - Software Design",
        "CSC355 - Compiler Design",
        "CSC356 - Computer Security",
      ],
      "Dr. Duhon": [
        "MATH150 - Calculus I",
        "MATH250 - Linear Algebra",
        "MATH310 - Probability",
      ],
    };

    /**
     * Updates the course dropdown based on the selected professor.
     * The available course list is defined by the COURSES map above.
     */
    function updateCourses() {
      const prof   = document.getElementById('professor').value;
      const sel    = document.getElementById('course');
      sel.innerHTML = '';
      sel.disabled  = !prof;

      if (!prof) {
        sel.innerHTML = '<option value="">Select professor first</option>';
        return;
      }

      sel.innerHTML = '<option value="">Select course…</option>';
      (COURSES[prof] || []).forEach(c => {
        const opt = document.createElement('option');
        opt.value = opt.textContent = c;
        sel.appendChild(opt);
      });
    }