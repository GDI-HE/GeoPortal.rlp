
function toggleDropdown(button) {
    const row = button.closest('tr');
    const dropdownContent = row.nextElementSibling;
    dropdownContent.classList.toggle('show');
    button.textContent = dropdownContent.classList.contains('show') ? 'Hide Details' : 'Show Details';
}

        function searchTable() {
    const input = document.getElementById('searchInput');
    const filter = input.value.toLowerCase();
    if (filter.length == 0) {
        location.reload();
        return;
    } 
    if (filter.length < 5) {
        return; // Do not search until at least 5 characters are entered
    }
   
    const spinner = document.getElementById('spinner');
    spinner.style.display = 'block'; // Show the spinner
    const loadMoreButton = document.getElementById('load-more');
    loadMoreButton.style.display = 'none'; // Hide the load more button
    fetch(`/search-data?query=${filter}`)
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector('#serviceTable tbody');
            tableBody.innerHTML = ''; // Clear existing rows
            let serialNo = 0;
            data.results.forEach(result => {
                serialNo += 1; // Increment serial number for each new row
                const mainRow = document.createElement('tr');
                mainRow.classList.add('main-row');
                const titleClass = result.layers_with_comma_keywords.length;
                const layersWithoutAbstractHtml = result.layers_without_abstract
                ? '<i class="fas fa-circle red-dot"></i>'
                : '<i class="fas fa-circle green-dot"></i>';

                const layersWithoutKeywordsHtml = result.layers_without_keywords
                ? '<i class="fas fa-circle red-dot"></i>'
                : '<i class="fas fa-circle green-dot"></i>';

                let layersAbstractMatchHtml = '';
                if (Array.isArray(result.layers_abstract_match)) {
                    layersAbstractMatchHtml = result.layers_abstract_match.map(match => {
                        if (match === 'Y') {
                            return '<i class="fas fa-circle red-dot"></i>';
                        } else if (match === 'N') {
                            return '<i class="fas fa-circle green-dot"></i>';
                        }
                        return '';
                    }).join('');
                } else if (typeof result.layers_abstract_match === 'string') {
                    layersAbstractMatchHtml = result.layers_abstract_match.split('').map(match => {
                        if (match === 'Y') {
                            return '<i class="fas fa-circle red-dot"></i>';
                        } else if (match === 'N') {
                            return '<i class="fas fa-circle green-dot"></i>';
                        }
                        return '';
                    }).join('');
                } else {
                    console.warn('layers_abstract_match is not an array or string:', result.layers_abstract_match);
                }

                const layersWithShortAbstractCountHtml = result.layers_with_short_abstract_count > 0
                ? '<i class="fas fa-circle red-dot"></i>'
                : '<i class="fas fa-circle green-dot"></i>';

                const connectedWmsHtml = result.connected_wms
                    ? '<i class="fas fa-circle green-dot"></i>'
                    : '<i class="fas fa-circle red-dot"></i>';

                mainRow.innerHTML = `
                    <td>${serialNo}</td>
                    <td>${result.wms_id}</td>
                    <td class="${titleClass}">${result.wms_title}</td>
                    <td>${result.total_layers}</td>
                    <td>${layersWithoutAbstractHtml}</td>
                    <td>${layersWithoutKeywordsHtml}</td>
                    <td>${layersAbstractMatchHtml}</td>
                    <td>${layersWithShortAbstractCountHtml}</td>
                    <td>${connectedWmsHtml}</td>
                   
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
                            <div class="dropdown-title">
                                Keywords Present
                                ${result.keywords_present.length > 0 
                                    ? '<i class="fas fa-info-circle"></i>' 
                                    : '<i class="fas fa-info-circle red-icon"></i>'}
                            </div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.keywords_present.map(keyword => `<li>${keyword}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">
                            Abstracts Present
                            ${result.abstracts_present.length > 0 
                                ? '<i class="fas fa-info-circle"></i>' 
                                : '<i class="fas fa-info-circle red-icon"></i>'}
                            </div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.abstracts_present.map(abstract => `<li>${abstract}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">
                                Layers Without Abstracts
                                ${result.layers_without_abstract_names.length > 0 
                                    ? '<i class="fas fa-info-circle red-icon"></i>' 
                                    : '<i class="fas fa-info-circle"></i>'}
                            </div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.layers_without_abstract_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                </ul>
                            </div>
                        </div>

                        <div class="dropdown">
                            <div class="dropdown-title">
                            Layers Without Keywords
                            ${result.layers_without_keyword_names.length > 0 
                                ? '<i class="fas fa-info-circle red-icon"></i>' 
                                : '<i class="fas fa-info-circle"></i>'}
                            </div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.layers_without_keyword_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                </ul>
                            </div>
                        </div>

                        <div class="dropdown">
                            <div class="dropdown-title">
                            Layers Where Abstract Matches Title
                            ${result.layers_abstract_matches_title_names.length > 0 
                                ? '<i class="fas fa-info-circle red-icon"></i>' 
                                : '<i class="fas fa-info-circle"></i>'}
                            </div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.layers_abstract_matches_title_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">
                            Layer Names
                            ${result.layer_names.length > 0 
                                ? '<i class="fas fa-info-circle"></i>' 
                                : '<i class="fas fa-info-circle red-icon"></i>'}
                            </div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.layer_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">
                            Layers With Short Abstracts
                            ${result.layers_with_short_abstract_info.length > 0 
                                ? '<i class="fas fa-info-circle red-icon"></i>' 
                                : '<i class="fas fa-info-circle"></i>'}
                            </div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.layers_with_short_abstract_info.map(info => `<li class="short-abstract">${info[0]}: ${info[1]}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">
                            Angaben zu Kosten/Gebühren/Lizenzen
                             ${result.wms_fees && result.wms_fees.length > 5
                                ? '<i class="fas fa-info-circle"></i>' 
                                : '<i class="fas fa-info-circle red-icon"></i>'}
                            </div>
                            <div class="dropdown-content">
                                <ul>
                                    ${result.wms_fees}
                                </ul>
                            </div>
                        </div>
                        <div class="dropdown">
                            <div class="dropdown-title">
                            Beschränkungen des öffentlichen Zugangs
                                ${result.wms_accessconstraints && result.wms_accessconstraints.length > 5
                                    ? '<i class="fas fa-info-circle"></i>' 
                                    : '<i class="fas fa-info-circle red-icon"></i>'}
                            </div>
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
        })
        .finally(() => {
            spinner.style.display = 'none'; // Hide the spinner
        }
        );
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
