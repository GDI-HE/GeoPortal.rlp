$(document).ready(function() {
    // Existing code for updating the graph
    $('#update_graph_btn').click(function() {
        var start_date = $('#start_date').val();
        var end_date = $('#end_date').val();
        var url = $(this).data('url');

        $.ajax({
            url: url,
            type: 'GET',
            data: {
                'start_date': start_date,
                'end_date': end_date
            },
            success: function(response) {
                $('#graph_container').html(response.fig_html);
            },
            error: function(xhr, status, error) {
                console.error('Error updating graph:', error);
            }
        });
    });

    // New code for handling form submission but not working right now
    // TODO
    $('#reportForm').on('submit', function(event) {
        event.preventDefault(); // Prevent the default form submission

        const formData = new FormData(this);
        const url = $(this).attr('action'); // Get the form action URL

        $.ajax({
            url: url,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                // Update the modal content with the response
                $('#modalGraphContent').attr('srcdoc', response['fig_html_report']);
            },
            error: function(xhr, status, error) {
                console.error('Failed to submit the form: ' + error);
            }
        });
    });
});

$(document).ready(function() {
    $(".modal-header, .modal-footer").addClass("draggable-handle");
    $("#graphModal").draggable({
        handle: ".draggable-handle",
        containment: "window",
        cursor: "move",
        start: function(event, ui) {
            $(".draggable-handle").addClass("dragging");
        },
        stop: function(event, ui) {
            $(".draggable-handle").removeClass("dragging");
        }
    })

});
//need to check its security issue
function getBaseUrl() {
const { protocol, hostname, port } = window.location;
return `${protocol}//${hostname}${port ? `:${port}` : ''}`;
}

    function showGraphInModal(contentType) {
        currentKeyword = contentType;
        const baseUrl = getBaseUrl();
        const filterUrl = `${baseUrl}/filter/`;
        const spinnerContainer = document.getElementById('spinnerContainer');

        // Show the spinner
        spinnerContainer.style.display = 'block';

        $.get(filterUrl, function(data) {
            let htmlContent = '';

            if (contentType === 'fig_html_report') {
                let modifiedFormHtml = formHtml.replace(
                    /<input type="file" name="file"[^>]*>/,
                '<input type="file" name="file" required id="id_file" accept=".csv">'
                );
                htmlContent = `
                    <h1>Generate Reporting Date</h1>
                    <form id="reportForm" method="post" enctype="multipart/form-data" data-url="${filterUrl}">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                        ${modifiedFormHtml}
                        <input type="hidden" name="contenttype" value="user_report">
                        <button type="submit">Upload</button>
                    </form>
                `;
            } else {
                htmlContent = `
                    <label for="start_date">Start Date:</label>
                    <input type="date" id="start_date" name="start_date" value="${startDate}">
                    <label for="end_date">End Date:</label>
                    <input type="date" id="end_date" name="end_date" value="${endDate}">
                    <button id="update_graph_btn" data-url="${filterUrl}" data-keyword="${contentType}">Filter</button>
                `;
                if (contentType === 'fig_html' || contentType === 'session_data' || contentType === 'fig_wms' || contentType === 'fig_wfs'|| contentType === 'fig_wmc') {
                    htmlContent += `
                        <label for="dropdown">Select Option:</label>
                        <select id="dropdown" name="dropdown">
                            <option value="monthly" data-url="monthly_url">Monthly</option>
                            <option value="daily" data-url="daily_url">Daily</option>
                            <option value="weekly" data-url="weekly_url">Weekly</option>
                            <option value="6months" data-url="6months_url">6 Months</option>
                            <option value="yearly" data-url="yearly_url">Yearly</option>
                        </select>
                    `;
                }
            }

            $('#dynamicContent').html(htmlContent);
            $('#modalGraphContent').attr('srcdoc', data[contentType]);

            $('#graphModal').modal({
                backdrop: false
            });
            spinnerContainer.style.display = 'none';

            // hide download button for 3 modal
            const downloadLink = document.getElementById('downloadWmsCsvLink');
            if (contentType === 'session_data') {
                downloadLink.style.display = 'none';
            } else {
                downloadLink.style.display = 'block';
            }
    
            let dropdownValue = "";
            if (contentType !== 'fig_html_report') {
                document.getElementById('update_graph_btn').addEventListener('click', function() {
                    const startDate = document.getElementById('start_date').value;
                    const endDate = document.getElementById('end_date').value;
                    if (contentType === 'fig_html'|| contentType === 'fig_wms' || contentType === 'fig_wfs'|| contentType === 'fig_wmc') {
                    dropdownValue = document.getElementById('dropdown').value;
                    } 
                    const url = this.getAttribute('data-url');
                    const keyword = this.getAttribute('data-keyword');

                    // Show the spinner before making the AJAX request
                    $('#modalGraphContent').hide();
                    spinnerContainer.style.display = 'flex';

                    $.ajax({
                        url: url,
                        type: 'GET',
                        data: {
                            start_date: startDate,
                            end_date: endDate,
                            keyword: keyword,
                            //if dropdownValue is empty, do nothing
                            dropdown: dropdownValue ? dropdownValue : null
                        },
                        success: function(data) {
                            $('#modalGraphContent').attr('srcdoc', data[contentType]);
                            // hide the spinner after the content is loaded
                            $('#modalGraphContent').show();
                            spinnerContainer.style.display = 'none';
                        },
                        error: function(xhr, status, error) {
                            console.error('Failed to fetch the content from ' + url);
                            // Hide the spinner if there is an error
                            spinnerContainer.style.display = 'none';
                        }
                    });
                });
            } else {
                                
                    document.getElementById('reportForm').addEventListener('submit', function(event) {
                        event.preventDefault(); // Prevent the default form submission
                
                        const formData = new FormData(this);
                        //const url = '/dashboard/';
                        const url = this.getAttribute('data-url');
                                                    
                            if (!url) {
                                console.error('Form action URL is not set.');
                                return;
                            }

                            function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');
spinnerContainer.style.display = 'block';

                        
                        $.ajax({
                            url: url,
                            type: 'POST',
                            data: formData,
                            processData: false,
                            contentType: false,
                            headers: {
                                'X-CSRFToken': '{{ csrftoken }}' // Include CSRF token in the headers
                            },
                            success: function(data) {
                                try {
                                    
                                    $('#modalGraphContent').attr('srcdoc', data[contentType]);
                                } catch (e) {
                                    
                                    console.error('Response data:', data);
                                }
                                spinnerContainer.style.display = 'none';
                            },
                            error: function(xhr, status, error) {
                            }
                        });
                    });
                }
        });
    }

 document.addEventListener('DOMContentLoaded', function() {
    const userCreationReportButton = document.getElementById('userCreationReportButton');
    if (userCreationReportButton) {
        userCreationReportButton.addEventListener('click', function() {
            // Change the modal content
            const baseUrl = getBaseUrl();
            const filterUrl = `${baseUrl}/filter/`;
            const spinnerContainer = document.getElementById('spinnerContainer');

            // Show the spinner
            spinnerContainer.style.display = 'block';

            $.ajax({
                url: filterUrl,
                type: 'GET',
                data: {
                    contentType: 'fig_html_report'
                },
                success: function(data) {
                    // Assuming csrfToken and modifiedFormHtml are defined elsewhere in your script
                    const csrfToken = getCookie('csrftoken'); // Function to get CSRF token
                    const modifiedFormHtml = '<input type="file" name="file" required id="id_file" accept=".csv">'; // Example form HTML

                    let htmlContent = `
                        <h1>Generate Reporting Date</h1>
                        <form id="reportForm" method="post" enctype="multipart/form-data" data-url="${filterUrl}">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            ${modifiedFormHtml}
                            <input type="hidden" name="contenttype" value="user_report">
                            <button type="submit">Upload</button>
                        </form>
                    `;

                    $('#dynamicContent').html(htmlContent);
                    $('#modalGraphContent').attr('srcdoc', data['fig_html_report']);

                    // Hide the spinner after the content is loaded
                    spinnerContainer.style.display = 'none';

                    // Add event listener for form submission
                    document.getElementById('reportForm').addEventListener('submit', function(event) {
                        event.preventDefault(); // Prevent the default form submission

                        const formData = new FormData(this);
                        const url = this.getAttribute('data-url');

                        if (!url) {
                            console.error('Form action URL is not set.');
                            return;
                        }

                        spinnerContainer.style.display = 'block';

                        $.ajax({
                            url: url,
                            type: 'POST',
                            data: formData,
                            processData: false,
                            contentType: false,
                            headers: {
                                'X-CSRFToken': csrfToken // Include CSRF token in the headers
                            },
                            success: function(data) {
                                try {
                                    $('#modalGraphContent').attr('srcdoc', data['fig_html_report']);
                                } catch (e) {
                                    console.error('Response data:', data);
                                }
                                spinnerContainer.style.display = 'none';
                            },
                            error: function(xhr, status, error) {
                                console.error('Failed to fetch the content from ' + url);
                                console.error('Status:', status);
                                console.error('Error:', error);
                                console.error('Response:', xhr.responseText);
                                spinnerContainer.style.display = 'none';
                            }
                        });
                    });
                },
                error: function(xhr, status, error) {
                    console.error('Failed to fetch the content from ' + filterUrl);
                    console.error('Status:', status);
                    console.error('Error:', error);
                    console.error('Response:', xhr.responseText);
                    // Hide the spinner if there is an error
                    spinnerContainer.style.display = 'none';
                }
            });
        });
    } else {
        console.error('Element with ID userCreationReportButton not found.');
    }
});
        
        // Function to get the CSRF token
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

    document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('downloadWmsCsvLink').addEventListener('click', function() {
            const startDate = document.getElementById('start_date').value;
            const endDate = document.getElementById('end_date').value;
    
            $.ajax({
                url: downloadCsvUrl,
                type: 'GET',
                data: {
                    start_date: startDate,
                    end_date: endDate,
                    keyword: currentKeyword,
                    dropdown: document.getElementById('dropdown') ? document.getElementById('dropdown').value : null
                },
                success: function(data) {
                    const blob = new Blob([data], { type: 'text/csv' });
                    const link = document.createElement('a');
                    link.href = window.URL.createObjectURL(blob);
                    link.download = `${currentKeyword}_data.csv`;
                    link.click();
                },
                error: function(xhr, status, error) {
                    console.error('Error downloading CSV:', error);
                }
            });
        });
    });