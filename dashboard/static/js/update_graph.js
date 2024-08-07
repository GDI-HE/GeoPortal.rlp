$(document).ready(function() {
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
});
