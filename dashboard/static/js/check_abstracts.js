
function toggleDropdown(button) {
    const row = button.closest('tr');
    const dropdownContent = row.nextElementSibling;
    dropdownContent.classList.toggle('show');
    button.textContent = dropdownContent.classList.contains('show') ? TRANSLATIONS.hide_details : TRANSLATIONS.show_details;
}

function toggleClearButton(){
    const input = document.getElementById('searchInput');
    const clearButton = document.getElementById('clear-input1');
    if (input.value.length > 0) {
        clearButton.style.display = 'block';
    } else {
        clearButton.style.display = 'none';
    }
} 
function clearSearchInput() {
    const input = document.getElementById('searchInput');
    input.value = '';
    toggleClearButton();
    location.reload();
}

function toggleColumnList() {
    const columnList = document.getElementById('columnToggleList');
    if (columnList.style.display === 'none') {
        columnList.style.display = 'block';
    } else {
        // Check the number of selected columns
        const selectedColumns = document.querySelectorAll('#columnToggleList input[type="checkbox"]:checked');
        columnList.style.display = 'none';
    } 
}

document.addEventListener("DOMContentLoaded", function () {
  // Select all buttons with IDs starting with "tooltip-trigger"
  const tooltipTriggers = document.querySelectorAll("button[id^='tooltip-trigger']");

  // Loop over each tooltip trigger button
  tooltipTriggers.forEach(function (trigger) {
    // Get the aria-describedby attribute to find the corresponding tooltip content by ID
    const tooltipId = trigger.getAttribute("aria-describedby");
    const tooltipContent = document.getElementById(tooltipId);

    // Handle click event to toggle tooltip visibility
    trigger.addEventListener("click", function (event) {
      event.stopPropagation();

      // Hide any other open tooltips
      document.querySelectorAll(".custom-tooltip.show-tooltip").forEach(function (tooltip) {
        if (tooltip !== tooltipContent) {
          tooltip.classList.remove("show-tooltip");
        }
      });

      // Toggle the tooltip visibility for the clicked button
      tooltipContent.classList.toggle("show-tooltip");

      // Focus the tooltip content if shown for accessibility
      if (tooltipContent.classList.contains("show-tooltip")) {
        tooltipContent.focus();
      }
    });

    // Handle keyboard events (Enter or Space)
    trigger.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        event.stopPropagation();

        // Hide other tooltips before toggling current one
        document.querySelectorAll(".custom-tooltip.show-tooltip").forEach(function (tooltip) {
          if (tooltip !== tooltipContent) {
            tooltip.classList.remove("show-tooltip");
          }
        });

        tooltipContent.classList.toggle("show-tooltip");

        if (tooltipContent.classList.contains("show-tooltip")) {
          tooltipContent.focus();
        }
      }
    });
  });

  // Clicking outside closes any open tooltip
  document.addEventListener("click", function () {
    document.querySelectorAll(".custom-tooltip.show-tooltip").forEach(function (tooltip) {
      tooltip.classList.remove("show-tooltip");
    });
  });
});

  
  // Add this function at the beginning of your script
function resetColumnToggles() {
    document.querySelectorAll('#columnToggleList input[type="checkbox"]').forEach(checkbox => {
        const column = parseInt(checkbox.getAttribute('data-column'));
        const table = document.getElementById('serviceTable');
        const th = table.querySelector(`thead th:nth-child(${column + 1})`);
        const tds = table.querySelectorAll(`tbody td:nth-child(${column + 1})`);

        // Check if the checkbox was initially checked in the HTML
        const initiallyChecked = checkbox.hasAttribute('checked');

        if (initiallyChecked) {
            // Keep initially checked columns visible and checked
            checkbox.checked = true;
            th.style.display = '';
            tds.forEach(td => td.style.display = '');
        } else {
            // Reset only the manually checked checkboxes
            checkbox.checked = false;
            th.style.display = 'none';
            tds.forEach(td => td.style.display = 'none');
        }
    });
}

// Call this function when the page loads
document.addEventListener('DOMContentLoaded', resetColumnToggles);

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('#columnToggleList input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            const column = this.getAttribute('data-column');
            const table = document.getElementById('serviceTable');
            const th = table.querySelector(`thead th:nth-child(${parseInt(column) + 1})`);
            const tds = table.querySelectorAll(`tbody td:nth-child(${parseInt(column) + 1})`);
            if (this.checked) {
                th.style.display = '';
                tds.forEach(td => td.style.display = '');
            } else {
                th.style.display = 'none';
                tds.forEach(td => td.style.display = 'none');
            }
        });
    });
});
document.addEventListener("DOMContentLoaded", function () {
document.querySelectorAll('.dropdown-btn').forEach(button => {
    button.addEventListener('click', () => {
      const detailsSection = button.closest('tr').nextElementSibling;
      if (detailsSection.classList.contains('details-section')) {
        // Toggle between showing and hiding the details section
        detailsSection.style.display = 
          detailsSection.style.display === 'none' || detailsSection.style.display === '' 
          ? 'table-row' 
          : 'none';
      }
    });
  });
}); 

document.addEventListener('DOMContentLoaded', function() {
    var dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(function(dropdown) {
        var title = dropdown.querySelector('.dropdown-title');
        var content = dropdown.querySelector('.dropdown-content');
        content.style.display = 'none';
        title.addEventListener('click', function() {
            var isVisible = content.style.display === 'block';
            content.style.display = isVisible ? 'none' : 'block';
            title.classList.toggle('active', !isVisible);
        });
    });
});

