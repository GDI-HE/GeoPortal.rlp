
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
                        mainRow.innerHTML = `
                            <td>${serialNo}</td>
                            <td>${result.wms_id}</td>
                            <td>${result.wms_title}</td>
                            <td>${result.total_layers}</td>
                            <td>${result.layers_without_abstract}</td>
                            <td>${result.layers_without_keywords}</td>
                            <td class="status ${result.all_layers_have_abstract ? 'status-yes' : 'status-no'}">
                                ${result.all_layers_have_abstract ? 'Yes' : 'No'}
                            </td>
                            <td class="status ${result.all_layers_have_keywords ? 'status-yes' : 'status-no'}">
                                ${result.all_layers_have_keywords ? 'Yes' : 'No'}
                            </td>
                            <td>${result.keywords_present.length} keywords</td>
                            <td>${result.abstracts_present.length} abstracts</td>
                            <td>
                                ${result.layers_abstract_match.map(match => `<span>${match}</span><br>`).join('')}
                            </td>
                            <td>${result.layers_with_short_abstract_count}</td>
                           
                            <td>
                                <button class="dropdown-btn" onclick="toggleDropdown(this)">Show Details</button>
                            </td>
                        `;
        
                        const detailRow = document.createElement('tr');
                        detailRow.classList.add('dropdown-content');
                        detailRow.innerHTML = `
                            <td colspan="12">
                                <h3>Keywords Present:</h3>
                                <ul>
                                    ${result.keywords_present.map(keyword => `<li>${keyword}</li>`).join('')}
                                </ul>
                                <h3>Abstracts Present:</h3>
                                <ul>
                                    ${result.abstracts_present.map(abstract => `<li>${abstract}</li>`).join('')}
                                </ul>
                                <h3>Layers Without Abstracts:</h3>
                                <ul>
                                    ${result.layers_without_abstract_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                </ul>
                                <h3>Layers Without Keywords:</h3>
                                <ul>
                                    ${result.layers_without_keyword_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                </ul>
                                <h3>Layers Where Abstract Matches Title:</h3>
                                <ul>
                                    ${result.layers_abstract_matches_title_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                </ul>
                                <h3>Layer Names:</h3>
                                <ul>
                                    ${result.layer_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                </ul>
                                <h3>Layers With Short Abstracts:</h3>
                                <ul>
                                    ${result.layers_with_short_abstract_info.map(info => `<li class="short-abstract">${info[0]}: ${info[1]}</li>`).join('')}
                                </ul>
                                <h3> Angaben zu Kosten/Gebühren/Lizenzen </h3>
                                <ul>
                                    ${result.wms_fees}
                                </ul>
                                <h3> Beschränkungen des öffentlichen Zugangs </h3>
                                <ul>
                                    ${result.wms_accessconstraints}
                                </ul>

                            </td>
                        `;
        
                        tableBody.appendChild(mainRow);
                        tableBody.appendChild(detailRow);
                    });
                });
        }
        function toggleClearButton(){
            const input = document.getElementById('searchInput');
            const clearButton = document.getElementById('clear-input');
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
                        if (data.results) {
                            data.results.forEach(result => {
                                serialNo += 1; // Increment serial number for each new row
                                const mainRow = document.createElement('tr');
                                mainRow.classList.add('main-row');
                                mainRow.innerHTML = `
                                    <td>${serialNo}</td>
                                    <td>${result.wms_id}</td>
                                    <td>${result.wms_title}</td>
                                    <td>${result.total_layers}</td>
                                    <td>${result.layers_without_abstract}</td>
                                    <td>${result.layers_without_keywords}</td>
                                    <td class="status ${result.all_layers_have_abstract ? 'status-yes' : 'status-no'}">
                                        ${result.all_layers_have_abstract ? 'Yes' : 'No'}
                                    </td>
                                    <td class="status ${result.all_layers_have_keywords ? 'status-yes' : 'status-no'}">
                                        ${result.all_layers_have_keywords ? 'Yes' : 'No'}
                                    </td>
                                    <td>${result.keywords_present.length} keywords</td>
                                    <td>${result.abstracts_present.length} abstracts</td>
                                    <td>
                                        ${result.layers_abstract_match.map(match => `<span>${match}</span><br>`).join('')}
                                    </td>
                                    <td>${result.layers_with_short_abstract_count}</td>
                                    <td>
                                        <button class="dropdown-btn" onclick="toggleDropdown(this)">Show Details</button>
                                    </td>
                                `;

                                const detailRow = document.createElement('tr');
                                detailRow.classList.add('dropdown-content');
                                detailRow.innerHTML = `
                                    <td colspan="12">
                                        <h3>Keywords Present:</h3>
                                        <ul>
                                            ${result.keywords_present.map(keyword => `<li>${keyword}</li>`).join('')}
                                        </ul>
                                        <h3>Abstracts Present:</h3>
                                        <ul>
                                            ${result.abstracts_present.map(abstract => `<li>${abstract}</li>`).join('')}
                                        </ul>
                                        <h3>Layers Without Abstracts:</h3>
                                        <ul>
                                            ${result.layers_without_abstract_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                        </ul>
                                        <h3>Layers Without Keywords:</h3>
                                        <ul>
                                            ${result.layers_without_keyword_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                        </ul>
                                        <h3>Layers Where Abstract Matches Title:</h3>
                                        <ul>
                                            ${result.layers_abstract_matches_title_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                        </ul>
                                        <h3>Layer Names:</h3>
                                        <ul>
                                            ${result.layer_names.map(layer_name => `<li>${layer_name}</li>`).join('')}
                                        </ul>
                                        <h3>Layers With Short Abstracts:</h3>
                                        <ul>
                                            ${result.layers_with_short_abstract_info.map(info => `<li class="short-abstract">${info[0]}: ${info[1]}</li>`).join('')}
                                        </ul>
                                        <h3> Angaben zu Kosten/Gebühren/Lizenzen </h3>
                                        <ul>
                                            ${result.wms_fees}
                                        </ul>
                                        <h3> Beschränkungen des öffentlichen Zugangs </h3>
                                        <ul>
                                            ${result.wms_accessconstraints}
                                        </ul>

                                    </td>
                                `;

                                tableBody.appendChild(mainRow);
                                tableBody.appendChild(detailRow);
                            });

                            if (!data.has_next) {
                                loadMoreButton.style.display = 'none';
                            }
                        }
                    });
            });
        });
 