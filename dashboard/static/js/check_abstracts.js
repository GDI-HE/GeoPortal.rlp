
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

  document.addEventListener("DOMContentLoaded", function () {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl)
    })
  });

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

$(function() {
        function enableColResizable() {
            $("#serviceTable").colResizable({liveDrag:true, disable: false});
        }
        enableColResizable();
        function updateDetailColspan() {
          let visibleCols = $('#serviceTable > thead > tr > th:visible').length;
          $('#serviceTable tr.collapse td[colspan]').attr('colspan', visibleCols);
        }
        // Update colspan after initial setup
        updateDetailColspan();



        // Set initial column visibility based on checkboxes
        $('.column-toggle-list input[type="checkbox"]').each(function() {
            var colIdx = parseInt($(this).data('column'));
            var checked = $(this).is(':checked');
            // Header
            $('#serviceTable thead th').eq(colIdx).toggle(checked);
            // Only main table body rows, not details
            $('#serviceTable > tbody > tr').not('.collapse').each(function() {
                $(this).find('td').eq(colIdx).toggle(checked);
            });
        });

        // Column toggle logic: only affect main table, not details
        $('.column-toggle-list input[type="checkbox"]').on('change', function() {
            // Update colspan after initial setup
            updateDetailColspan();

            var colIdx = parseInt($(this).data('column'));
            var checked = $(this).is(':checked');
            // Toggle header
            var $th = $('#serviceTable thead th').eq(colIdx);
            $th.toggle(checked);
            // Toggle only main table body rows, not details
            $('#serviceTable > tbody > tr').not('.collapse').each(function() {
                var $td = $(this).find('td').eq(colIdx);
                $td.toggle(checked);
            });
            // Proportionally resize all visible columns
            var $visibleThs = $('#serviceTable thead th:visible');
            var percent = 100 / $visibleThs.length;
            $visibleThs.each(function(i) {
                $(this).css({width: percent + '%', maxWidth: 'none'});
            });
            $('#serviceTable > tbody > tr').not('.collapse').each(function() {
                $(this).find('td:visible').each(function(i) {
                    $(this).css({width: percent + '%', maxWidth: 'none'});
                });
            });
            // Re-enable colResizable after DOM changes
            $("#serviceTable").colResizable({disable: true}); // Remove previous
            enableColResizable();
        });
    });

function isEllipsed(el) {
  // If element is not visible or not displayed, treat as not ellipsed
  if (!el.offsetParent || window.getComputedStyle(el).display === 'none') return false;
  return el.offsetWidth < el.scrollWidth;
}

// After column resize, update ellipsis and aria attributes for headers and cells
function updateEllipsisState() {
  // For headers
  document.querySelectorAll('.clickable-header').forEach(function(header) {
    if (isEllipsed(header)) {
      header.setAttribute('aria-label', header.textContent + ' (truncated)');
      header.setAttribute('tabindex', '0');
      header.classList.add('ellipsed');
    } else {
      header.setAttribute('aria-label', header.textContent);
      header.classList.remove('ellipsed');
    }
  });
  // For service title cells
  document.querySelectorAll('.service-title-cell').forEach(function(cell) {
    if (isEllipsed(cell)) {
      cell.setAttribute('aria-label', cell.textContent + ' (truncated)');
      cell.setAttribute('tabindex', '0');
      cell.classList.add('ellipsed');
    } else {
      cell.setAttribute('aria-label', cell.textContent);
      cell.classList.remove('ellipsed');
    }
  });
}

// Only run column resizing/ellipsis logic on desktop (not mobile)
function isMobileView() {
  return window.matchMedia && window.matchMedia('(max-width: 900px)').matches;
}

(function() {
  if (isMobileView()) return; // Don't run on mobile
  const table = document.getElementById('serviceTable');
  if (!table) return;
  const ths = table.querySelectorAll('thead th');
  let startX, startWidth, colIndex, resizing = false;

  ths.forEach((th, i) => {
    const handle = th.querySelector('.resize-handle');
    if (!handle) return;
    handle.addEventListener('mousedown', function(e) {
      e.preventDefault();
      resizing = true;
      startX = e.pageX;
      startWidth = th.offsetWidth;
      colIndex = i;
      document.body.style.cursor = 'col-resize';
      document.body.setAttribute('data-resizing-col', colIndex);
    });
  });

  document.addEventListener('mousemove', function(e) {
    if (!resizing) return;
    const dx = e.pageX - startX;
    const newWidth = Math.max(40, startWidth + dx);
    // Set width for header
    ths[colIndex].style.width = newWidth + 'px';
    ths[colIndex].style.maxWidth = 'none';
    // Set width for all cells in this column
    table.querySelectorAll('tbody tr').forEach(row => {
      const cell = row.querySelectorAll('td')[colIndex];
      if (cell) {
        cell.style.width = newWidth + 'px';
        cell.style.maxWidth = 'none';
        cell.style.whiteSpace = 'normal';
      }
    });
    updateEllipsisState();
  });
  document.addEventListener('mouseup', function() {
    if (resizing) {
      resizing = false;
      document.body.style.cursor = '';
      document.body.removeAttribute('data-resizing-col');
      updateEllipsisState();
    }
  });
  // Initial call
  updateEllipsisState();
})();

// Always update ellipsis state on resize (desktop only)
window.addEventListener('resize', function() {
  if (!isMobileView()) updateEllipsisState();
});

            

// Mobile details row toggle logic
(function() {
  function isMobile() {
    return window.matchMedia && window.matchMedia('(max-width: 700px)').matches;
  }
  function hideAllDetailsRows() {
    document.querySelectorAll('tr.collapse').forEach(function(row) {
      row.style.display = 'none';
      row.setAttribute('aria-hidden', 'true');
    });
  }
  function showDetailsRow(row) {
    row.style.display = 'table-row';
    row.setAttribute('aria-hidden', 'false');
  }
  document.addEventListener('DOMContentLoaded', function() {
    if (isMobile()) {
      hideAllDetailsRows();
      document.querySelectorAll('button[data-toggle="collapse"]').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
          var targetId = btn.getAttribute('data-target') || btn.getAttribute('data-bs-target');
          if (!targetId) return;
          var row = document.querySelector(targetId);
          if (!row) return;
          if (row.style.display === 'table-row') {
            row.style.display = 'none';
            row.setAttribute('aria-hidden', 'true');
          } else {
            hideAllDetailsRows();
            showDetailsRow(row);
          }
        });
      });
    }
  });
  // On resize, re-hide all details rows if switching to mobile
  window.addEventListener('resize', function() {
    if (isMobile()) hideAllDetailsRows();
  });
})();