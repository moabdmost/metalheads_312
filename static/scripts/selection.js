    const COURSES = {
      "R.Ramanujan": [
        "CSC371 - Machine Learning",
        "CSC324 - Theory of Computation",
        "CSC250 - Computer Organization",
      ],
      "T.Lim": [
        "CSC221 - Data Structures",
        "CSC312 - Software Design",
        "CSC355 - Compiler Design",
        "CSC356 - Computer Security",
      ],
      "A.Duhon": [
        "MATH150 - Calculus I",
        "MATH250 - Linear Algebra",
        "MATH310 - Probability",
      ],
    };

    /**
     * Updates the course dropdown based on the selected professor.
     * The available course list is defined by the COURSES map above.
     * @param {void}
     * @returns {void}
     */
    function updateCourses() {
      /** 
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
      */

      var input, filter, ul, li, a, i, txtValue, matches;
      input = document.getElementById('professor_input');
      filter = input.value.toUpperCase();
      ul = document.getElementById("professor-list");
      li = ul.getElementsByTagName('li');

      // First, hide all items
      for (i = 0; i < li.length; i++) {
        li[i].style.display = "none";
      }

      // Find matching items and show only top 3
      matches = [];
      for (i = 0; i < li.length; i++) {
        a = li[i].getElementsByTagName("a")[0];
        txtValue = a.textContent || a.innerText;
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
          matches.push(li[i]);
        }
      }

      // Show only the first 2 matches
      for (i = 0; i < Math.min(matches.length, 2); i++) {
        matches[i].style.display = "";
      }

      // Show or hide the list
      ul.style.display = matches.length > 0 ? "block" : "none";

      // Add click handlers to select suggestion
      matches.slice(0, 2).forEach(item => {
        item.onclick = function() {
          const selectedProfessor = this.getElementsByTagName("a")[0].textContent;
          setProfessor(selectedProfessor);
        };
      });
    }

    /**
     * fills the courses dropdown box based on the selected professor. 
     * If no professor is selected, the dropdown is disabled and shows a 
     * prompt to select a professor first.
     * @param {*} prof 
     * @returns 
     */
    /**
     * Fills the course dropdown with courses for the selected professor.
     * @param {string} prof - The professor name to filter courses by.
     * @returns {void}
     */
    function fillCourses(prof) {
      const sel = document.getElementById('course');
      sel.innerHTML = '';
      sel.disabled = !prof;

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

    /**
     * set's the professor input field to the selected professor, 
     * hides the dropdown list, and updates the course options 
     * based on the selected professor.
     * @param {*} prof 
     * @returns (void) Sets the professor input field to the selected professor, 
     * hides the dropdown list, and updates the course options 
     * based on the selected professor.
     */
    /**
     * Sets the professor input value and updates the course dropdown.
     * @param {string} prof - The professor name to set.
     * @returns {void}
     */
    function setProfessor(prof) {
      const input = document.getElementById('professor_input');
      const ul = document.getElementById('professor-list');
      input.value = prof;
      ul.style.display = 'none';
      fillCourses(prof);
    }

    /**
     * Submits the selected professor from the dropdown, sets the input field,
     * and updates the course options accordingly.
     * @param {*} item 
     * @returns (void) Sets the professor input field to the selected professor,
     */
    /**
     * Handles selection of a professor from the dropdown list.
     * @param {HTMLElement} item - The list item element that was clicked.
     * @returns {void}
     */
    function submitSelection(item) {
      const selectedProfessor = item.querySelector('a').textContent;
      setProfessor(selectedProfessor);
    }
      
      