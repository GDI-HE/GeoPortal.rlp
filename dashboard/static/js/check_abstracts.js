
function toggleDropdown(button) {
    const row = button.closest('tr');
    const dropdownContent = row.nextElementSibling;
    dropdownContent.classList.toggle('show');
    button.textContent = dropdownContent.classList.contains('show') ? 'Hide Details' : 'Show Details';
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
document.addEventListener('DOMContentLoaded', function() {
    let page = 1;
    serialNo = serialNo;
    const loadMoreButton = document.getElementById('load-more');
    const tableBody = document.querySelector('#serviceTable tbody');

    loadMoreButton.addEventListener('click', function() {
        page += 1;
        fetch(`/load-more-data?page=${page}`)
            .then(response => response.json())
            .then(data => {
                //Use this if you want to show only the elements from that page like only 1-10, 11-20 etc
                // const tableBody = document.querySelector('#serviceTable tbody');
                tableBody.innerHTML = ''; // Clear existing rows
                if (data.results) {
                    data.results.forEach(result => {
                        serialNo += 1; // Increment serial number for each new row
                        const mainRow = document.createElement('tr');
                        mainRow.classList.add('main-row');
                        const titleClass = result.layers_with_comma_keywords.length>0? 'highlight-red' : '';
                        mainRow.innerHTML = `
                            <td>${serialNo}</td>
                            <td>${result.wms_id}</td>
                            <td class="${titleClass}">${result.wms_title}</td>
                            <td>${result.total_layers}</td>
                            <td>${result.layers_without_abstract}</td>
                            <td>${result.layers_without_keywords}</td>
                            
                            // <td>${result.keywords_present.length}</td>
                            // <td>${result.abstracts_present.length}</td>
                            //                                   <td>
                                ${result.layers_abstract_match === 'Y' ? '<span>Y</span><br>' : '<span>N</span><br>'}
                            </td>
                            <td>${result.layers_with_short_abstract_count}</td>
                            <td>${result.connected_wms ? 'True': 'False'}</td>
                            <td>
                                <button class="dropdown-btn" onclick="toggleDropdown(this)">Show Details</button>
                            </td>
                        `;

                        const detailRow = document.createElement('tr');
                        detailRow.classList.add('details-section');
                        detailRow.innerHTML = `
                           <td colspan="12">
                    <div class="dropdown-container">
                        <div class="dropdown">
                            <div class="dropdown-title">Keywords Present <i class="fas fa-info-circle"></i></div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.keywords_present.map(keyword => `<li>${keyword}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">Abstracts Present <i class="fas fa-info-circle"></i></div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.abstracts_present.map(abstract => `<li>${abstract}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">Layers Without Abstracts <i class="fas fa-info-circle"></i></div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.layers_without_abstract_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">Layers Without Keywords <i class="fas fa-info-circle"></i></div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.layers_without_keyword_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">Layers Where Abstract Matches Title <i class="fas fa-info-circle"></i></div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.layers_abstract_matches_title_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">Layer Names <i class="fas fa-info-circle"></i></div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.layer_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">Layers With Short Abstracts <i class="fas fa-info-circle"></i></div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.layers_with_short_abstract_info.map(info => `<li class="short-abstract">${info[0]}: ${info[1]}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">Angaben zu Kosten/Gebühren/Lizenzen <i class="fas fa-info-circle"></i></div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.wms_fees}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">Beschränkungen des öffentlichen Zugangs <i class="fas fa-info-circle"></i></div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.wms_accessconstraints}
                                </ul>
                            </div>
                        </div>
                       </div> 
                    </td>
                `;
                        tableBody.appendChild(mainRow);
                        tableBody.appendChild(detailRow);
                    });
                    var dropdowns = document.querySelectorAll('.dropdown');
                    dropdowns.forEach(function(dropdown){
                        var title = dropdown.querySelector('.dropdown-title');
                        var content = dropdown.querySelector('.dropdown-content');
                        content.style.display = 'none';
                        title.addEventListener('click', function(){
                            var isVisible = content.style.display === 'block';
                            content.style.display = isVisible ? 'none' : 'block';
                            title.classList.toggle('active', !isVisible);
                        } )
                    } )

                    if (!data.has_next) {
                        loadMoreButton.style.display = 'none';
                    }
                }
            });
    });
});

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
    const tooltipTrigger = document.getElementById("tooltip-trigger");
    const tooltipContent = document.getElementById("tooltip-content");
  
    tooltipTrigger.addEventListener("click", function (event) {
      event.stopPropagation();
      tooltipContent.classList.toggle("show-tooltip");
  
      if (tooltipContent.classList.contains("show-tooltip")) {
        tooltipContent.focus();
      }
    });
  
    tooltipTrigger.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.stopPropagation();
        tooltipContent.classList.toggle("show-tooltip");
  
        if (tooltipContent.classList.contains("show-tooltip")) {
          tooltipContent.focus();
        }
      }
    });
  
    document.addEventListener("click", function () {
      if (tooltipContent.classList.contains("show-tooltip")) {
        tooltipContent.classList.remove("show-tooltip");
      }
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

