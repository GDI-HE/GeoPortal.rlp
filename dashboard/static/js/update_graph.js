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