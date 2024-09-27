$(document).ready(function() {
    // Existing code for updating the graph
    //Is this really needed?
    // $('#update_graph_btn').click(function() {
    //     var start_date = $('#start_date').val();
    //     var end_date = $('#end_date').val();
    //     var url = $(this).data('url');

    //     $.ajax({
    //         url: url,
    //         type: 'GET',
    //         data: {
    //             'start_date': start_date,
    //             'end_date': end_date
    //         },
    //         success: function(response) {
    //             $('#graph_container').html(response.fig_html);
    //         },
    //         error: function(xhr, status, error) {
    //             console.error('Error updating graph:', error);
    //         }
    //     });
    // });

    // New code for handling form submission but not working right now
    // // TODO
    // $('#reportForm').on('submit', function(event) {
    //     event.preventDefault(); // Prevent the default form submission

    //     const formData = new FormData(this);
    //     const url = $(this).attr('action'); // Get the form action URL

    //     $.ajax({
    //         url: url,
    //         type: 'POST',
    //         data: formData,
    //         processData: false,
    //         contentType: false,
    //         success: function(response) {
    //             // Update the modal content with the response
    //             $('#modalGraphContent').attr('srcdoc', response['fig_html_report']);
    //         },
    //         error: function(xhr, status, error) {
    //             console.error('Failed to submit the form: ' + error);
    //         }
    //     });
    // });
    // const titleElement = document.querySelector('.plot-container .svg-container .main-svg .infolayer .g-gtitle .gtitle');
    //     if (titleElement) {
    //         titleElement.classList.remove('gtitle'); // Remove the 'gtitle' class
    //         titleElement.innerText = ''; // Set the text content to an empty string
    //         console.log('Class "gtitle" removed and text content set to an empty string.');
    //     } else {
    //         console.log('Title element not found.');
    //     }
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
    console.log('showGraphInModal called with contentType:', contentType);
    currentKeyword = contentType;
    const baseUrl = getBaseUrl();
    const filterUrl = `${baseUrl}/filter/`;
    const spinnerContainer = document.getElementById('spinnerContainer');
        
      // Define a mapping of content types to titles
    const contentTypeToTitle = {
        'fig_html': 'User Statistics',
        'fig_wms': 'WMS Statistics',
        'fig_wfs': 'WFS Statistics',
        'fig_wmc': 'WMC Statistics',
        'session_data': 'Session Data',
        'fig_html_report': 'Userdefined Report'
    };
    
    // Function to update the modal title
       function updateModalTitle(contentType) {
        // Get the title from the mapping, default to 'User Statistics' if not found
        const title = contentTypeToTitle[contentType] || 'User Statistics';
        document.getElementById('graphModalLabel').innerText = title;
    
        // Select the element and update its text content
    }
    
    
    // Example usage
    updateModalTitle(contentType);
    

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
                <p>Upload a CSV file to generate a report. 
                    <i class="fa fa-info-circle" id="infoIcon" data-html="true" style="cursor: pointer;"></i>
                </p>
                <form id="reportForm" method="post" enctype="multipart/form-data" data-url="${filterUrl}">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                    ${modifiedFormHtml}
                       <input type="hidden" name="contentType" id="contentType" value="${contentType}"> <!-- Dynamically set contentType -->
                    <button type="submit" class="btn btn-primary">Upload</button>
                </form>
            `;
        } else {
                                        htmlContent = `
                    <div class="row">
                        <div class="col-12 d-flex flex-wrap flex-md-nowrap py-1">
                            <div class="col-sm-12 col-md-4 py-1">
                                <small class="text-black">Start Date</small>
                                <div class="card shadow-sm">
                                    <div class="input-group">
                                        <span class="input-group-text" style="height: 30px;" id="addon-wrapping_start">
                                            <i class="fa fa-calendar-day"></i>
                                        </span>
                                        <input type="date" id="start_date" name="start_date" value="${startDate}" class="form-control" style="height: 30px; font-size: small; color: rgb(87, 115, 158); width: calc(100% - 40px);" placeholder="Start Date" aria-label="Start Date" aria-describedby="addon-wrapping_start">
                                    </div>
                                </div>
                            </div>
                            <div class="col-sm-12 col-md-4 py-1">
                                <small class="text-black">End Date</small>
                                <div class="card shadow-sm">
                                    <div class="input-group">
                                        <span class="input-group-text" style="height: 30px;" id="addon-wrapping_end">
                                            <i class="fa fa-calendar-day"></i>
                                        </span>
                                        <input type="date" id="end_date" name="end_date" value="${endDate}" class="form-control" style="height: 30px; font-size: small; color: rgb(87, 115, 158); width: calc(100% - 40px);" placeholder="End Date" aria-label="End Date" aria-describedby="addon-wrapping_end">
                                    </div>
                                </div>
                            </div>
                            <div class="col-sm-12 col-md-3 py-1">
                                <small class="text-black">Select Option</small>
                                <div class="card shadow-sm">
                                    <div class="input-group">
                                        <span class="input-group-text" style="height: 30px;" id="addon-wrapping_select">
                                            <i class="fa fa-list"></i>
                                        </span>
                                        <select id="dropdown" name="dropdown" class="form-control" style="height: 30px; font-size: small; color: rgb(87, 115, 158);" aria-label="Select Option" aria-describedby="addon-wrapping_select">
                                            <option value="monthly" data-url="monthly_url">Monthly</option>
                                            <option value="daily" data-url="daily_url">Daily</option>
                                            <option value="weekly" data-url="weekly_url">Weekly</option>
                                            <option value="6months" data-url="6months_url">6 Months</option>
                                            <option value="yearly" data-url="yearly_url">Yearly</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            <div class="col-sm-12 col-md-2 py-1 d-flex align-items-center justify-content-center">
                                <button id="update_graph_btn" data-url="${filterUrl}" data-keyword="${contentType}" class="btn btn-primary" style="height: 38px; padding: 0.375rem 0.75rem; margin-right: 60px; margin-top:20px;">Filter</button>
                            </div>
                        </div>
                    </div>
                `;
                    // if (contentType === 'fig_html' || contentType === 'session_data' || contentType === 'fig_wms' || contentType === 'fig_wfs' || contentType === 'fig_wmc') {
                    //     htmlContent += `
                    //         <div class="col-sm-12 py-1">
                    //             <small class="text-primary">Select Option</small>
                    //             <div class="card shadow-sm">
                    //                 <div class="input-group">
                    //                     <span class="input-group-text" style="height: 30px;" id="addon-wrapping_select">
                    //                         <i class="fa fa-list"></i>
                    //                     </span>
                    //                     <select id="dropdown" name="dropdown" class="form-control" style="height: 30px; font-size: small; color: rgb(87, 115, 158);" aria-label="Select Option" aria-describedby="addon-wrapping_select">
                    //                         <option value="monthly" data-url="monthly_url">Monthly</option>
                    //                         <option value="daily" data-url="daily_url">Daily</option>
                    //                         <option value="weekly" data-url="weekly_url">Weekly</option>
                    //                         <option value="6months" data-url="6months_url">6 Months</option>
                    //                         <option value="yearly" data-url="yearly_url">Yearly</option>
                    //                     </select>
                    //                 </div>
                    //             </div>
                    //         </div>
                    //     `;
                    // }
                }


        $('#dynamicContent').html(htmlContent);

        if (contentType === 'fig_html_report') {
            document.getElementById('reportForm').addEventListener('submit', function(event) {
                event.preventDefault(); // Prevent the default form submission

                const formData = new FormData(this);
                const url = this.getAttribute('data-url');
                formData.set('contentType', contentType); // Set the contentType value dynamically
                if (!url) {
                    console.error('Form action URL is not set.');
                    return;
                }

                // Show the spinner before making the AJAX request
                spinnerContainer.style.display = 'flex';

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
                        //console.log('Server response for form submission:', data); // Debugging: Log the server response
                        try {
                            // Update the graph container with the returned HTML
                            const reportContainer = document.getElementById('modalGraphContent');
                            reportContainer.srcdoc = '';
                            reportContainer.srcdoc = data.fig_upload_report;
                        } catch (e) {
                            console.error('Error updating report container:', e);
                        }
                        spinnerContainer.style.display = 'none';
                    },
                    error: function(xhr, status, error) {
                        console.error('Failed to fetch the content from ' + url);
                        console.error('Status:', status);
                        console.error('Error:', error);
                        spinnerContainer.style.display = 'none';
                    }
                });
            });
        } else {
            document.getElementById('update_graph_btn').addEventListener('click', function() {
                const startDate = document.getElementById('start_date').value;
                const endDate = document.getElementById('end_date').value;
                let dropdownValue = "";
                if (contentType === 'fig_html' || contentType === 'fig_wms' || contentType === 'fig_wfs' || contentType === 'fig_wmc') {
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
                        dropdown: dropdownValue ? dropdownValue : null
                    },
                    success: function(data) {
                        console.log('AJAX success response:', data); // Log AJAX success response
                        const titleElement = document.querySelector('.plot-container .svg-container .main-svg .infolayer .g-gtitle .gtitle');
        if (titleElement) {
            titleElement.classList.remove('gtitle'); // Remove the 'gtitle' class
            titleElement.classList.add('plotly-titles'); // Set the text content to an empty string
            titleElement.textContent = ' '; // Set the text content to 'User Statistics'
            //console.log('titleElement:', titleElement);
        } else {
            console.log('Title element not found.');
        }
          // Remove the title from the AJAX response
          let modifiedData = data[contentType];
          if (modifiedData) {
              // Use a regular expression to remove the title element
              modifiedData = modifiedData.replace(/"title":\{"text":"[^"]*"\}/, '"title":{"text":""}');
              $('#modalGraphContent').attr('srcdoc', modifiedData);
          } else {
              $('#modalGraphContent').attr('srcdoc', '<p>No data available for the selected graph.</p>');
          }
                        // if (data[contentType]) {
                        //     $('#modalGraphContent').attr('srcdoc', data[contentType]);
                        // } else {
                        //     $('#modalGraphContent').attr('srcdoc', '<p>No data available for the selected graph.</p>');
                        // }
                        // Hide the spinner after the content is loaded
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
        }

        $('#graphModal').modal({
            backdrop: false
        });
        spinnerContainer.style.display = 'none';

        // Hide download button for session_data modal
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
                            if (titleElement) {
                                titleElement.classList.remove('gtitle'); // Remove the 'gtitle' class
                                titleElement.classList.add('plotly-titles'); // Set the text content to an empty string
                                titleElement.textContent = ' '; // Set the text content to 'User Statistics'
                                //console.log('titleElement:', titleElement);
                            } else {
                                console.log('Title element not found.');
                            }
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
                                // console.error('Failed to fetch the content from ' + url);
                                // console.error('Status:', status);
                                // console.error('Error:', error);
                                // console.error('Response:', xhr.responseText);
                            }
                        });
                    });
                }
        });
    }
document.addEventListener('DOMContentLoaded', function() {
    let storedContentType = 'fig_html_report'; // Default contentType

    // Function to handle card click
    function handleCardClick(contentType) {
        storedContentType = contentType; // Store the contentType
        const baseUrl = getBaseUrl();
        const filterUrl = `${baseUrl}/filter/`;
        const spinnerContainer = document.getElementById('spinnerContainer');

        // Show the spinner
        spinnerContainer.style.display = 'block';

        $.ajax({
            url: filterUrl,
            type: 'GET',
            data: {
                contentType: contentType
            },
            success: function(data) {
                let modifiedData = data[contentType];
          if (modifiedData) {
              // Use a regular expression to remove the title element
              modifiedData = modifiedData.replace(/"title":\{"text":"[^"]*"\}/, '"title":{"text":""}');
              $('#modalGraphContent').attr('srcdoc', modifiedData);
          } else {
              $('#modalGraphContent').attr('srcdoc', '<p>No data available for the selected graph.</p>');
          }
                // $('#modalGraphContent').attr('srcdoc', data[contentType]);

                // Hide the spinner after the content is loaded
                spinnerContainer.style.display = 'none';
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
    }

    function showGraphInModal(contentType) {
        handleCardClick(contentType);
    }

    // Add event listeners to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('click', function() {
            const contentType = this.getAttribute('data-content-type');
            showGraphInModal(contentType);
        });
    });

    // Handle User Creation Report button click
    const userCreationReportButton = document.getElementById('userCreationReportButton');
    if (userCreationReportButton) {
        userCreationReportButton.addEventListener('click', function() {
            // Change the modal content
            const baseUrl = getBaseUrl();
            const filterUrl = `${baseUrl}/filter/`;
            const spinnerContainer = document.getElementById('spinnerContainer');

            // Show the spinner
            spinnerContainer.style.display = 'block';
            const reportContentType = storedContentType + '_report'; // Append '_report' to the stored contentType

            $.ajax({
                url: filterUrl,
                type: 'GET',
                data: {
                    contentType: reportContentType // Use the report contentType
                },
                success: function(data) {
                    const csrfToken = getCookie('csrftoken'); // Function to get CSRF token
                    const modifiedFormHtml = '<input type="file" name="file" required id="id_file" accept=".csv">'; // Example form HTML

                    let htmlContent = `
                           <p>Upload a CSV file to generate a report. 
                            <i class="fa fa-info-circle" data-toggle="tooltip" title="Ensure the CSV file has the correct headers and format. Only one column with header 'reporting_date' with date-format 'YYYY-MM-DD' (e.g. 2024-01-15) is allowed."></i>
                            </p>
                        
                        <form id="reportForm" method="post" enctype="multipart/form-data" data-url="${filterUrl}">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            ${modifiedFormHtml}
                            <input type="hidden" name="contenttype" id="contentType" value="${reportContentType}"> <!-- Use the report contentType -->
                            <button type="submit" class="btn btn-primary upload-btn">Upload</button>
                        </form>
                    `;

                    $('#dynamicContent').html(htmlContent);
                    $('#modalGraphContent').attr('srcdoc', data[reportContentType]);

                    // Hide the spinner after the content is loaded
                    spinnerContainer.style.display = 'none';

                    // Add event listener for form submission
                    document.getElementById('reportForm').addEventListener('submit', function(event) {
                        event.preventDefault(); // Prevent the default form submission

                        const formData = new FormData(this);
                        const url = this.getAttribute('data-url');
                        const contentType = document.getElementById('contentType').value;
                        
                       
                        if (!url) {
                            console.error('Form action URL is not set.');
                            return;
                        }
                        const fullUrl = `${url}?contentType=${encodeURIComponent(contentType)}`;
                        spinnerContainer.style.display = 'block';

                        $.ajax({
                            url: fullUrl,
                            type: 'POST',
                            data: formData,
                            processData: false,
                            contentType: false,
                            headers: {
                                'X-CSRFToken': formData.get('csrfmiddlewaretoken') // Include CSRF token in the headers
                            },
                            success: function(data) {
                                //console.log('Server response for form submission:', data); // Debugging: Log the server response
                                // try {
                                //     // Determine the correct content type to display
                                //     let reportContentType = 'fig_html_report'; // Default to fig_html_report
                                //     if (data.fig_wms_report) {
                                //         reportContentType = 'fig_wms_report';
                                //     } else if (data.fig_wfs_report) {
                                //         reportContentType = 'fig_wfs_report';
                                //     } else if (data.fig_wmc_report) {
                                //         reportContentType = 'fig_wmc_report';
                                //     } else if (data.fig_html) {
                                //         reportContentType = 'fig_html';
                                //     }
                    
                                //     if (data[reportContentType]) {
                                //         $('#modalGraphContent').attr('srcdoc', data[reportContentType]);
                                //     } else {
                                //         $('#modalGraphContent').attr('srcdoc', '<p>No data available for the selected graph.</p>');
                                //     }
                                // } catch (e) {
                                //     console.error('Response data:', data);
                                // }
                                try {
                                    // Update the graph container with the returned HTM
                                    const reportContainer = document.getElementById('modalGraphContent');
                                    reportContainer.srcdoc = '';
                                    console.log('Report container:', reportContainer);
                                    reportContainer.srcdoc = data.fig_upload_report;
                                } catch (e) {
                                    console.error('Error updating report container:', e);
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
// Initialize tooltips (requires jQuery and Bootstrap)
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip(); 
});
function generate_report(data) {
    // Example implementation of the generate_report function
    console.log('Generating report with data:', data);

    // Assuming data contains the necessary information to generate the report
    // You can update the DOM or perform other actions to display the report
    const reportContent = data.reportContent; // Example data field
    const reportContainer = document.getElementById('reportContainer');
    reportContainer.innerHTML = reportContent;
}
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