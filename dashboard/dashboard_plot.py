
import os
import plotly.graph_objs as go
from dashboard.dashboard_request import process_request
def generate_wms_plot(request, start_date, end_date):
        
        sorted_months_wms, sorted_counts_wms, cumulative_counts_wms, _, _, _,_,_,_,_,_,_,deleted_wms_count, _,_ = process_request(request)
        fig_wms_html, image_path_wms = create_plotly_figure(
        sorted_months_wms, 
        sorted_counts_wms, 
        cumulative_counts_wms, 
        deleted_wms_count, 
        'WMS per Month', 
        'Month', 
        'Cumulative Number of WMS', 
        'WMS per Month', 
        'Deleted WMS per Month', 
        'plotly_image_wms'
          )
        return fig_wms_html, image_path_wms

def generate_wfs_plot(request, start_date, end_date):
        
        _, _, _, sorted_months_wfs, sorted_counts_wfs, cumulative_counts_wfs, _, _, _,_,_,_,_,deleted_wfs_count,_ = process_request(request)
        fig_wfs_html, image_path_wfs = create_plotly_figure(
            sorted_months_wfs, sorted_counts_wfs, cumulative_counts_wfs, deleted_wfs_count, 'WFS per Month', 'Month', 'Cumulative Number of WFS', 'WFS per Month', 'Deleted WFS per Month', 'plotly_image_wfs'
        )
        return fig_wfs_html, image_path_wfs

def generate_wmc_plot(request, start_date, end_date):
        
        _, _, _,_, _, _, sorted_months_wmc, sorted_counts_wmc, cumulative_counts_wmc,_,_,_,_,_,deleted_wmc_count = process_request(request)
        fig_wmc_html, image_path_wmc = create_plotly_figure(
        sorted_months_wmc, 
        sorted_counts_wmc, 
        cumulative_counts_wmc, 
        deleted_wmc_count, 
        'WMC per Month', 
        'Month', 
        'Cumulative Number of WMC', 
        'WMC per Month', 
        'Deleted WMC per Month', 
        'plotly_image_wmc'
        )
        return fig_wmc_html, image_path_wmc


def create_plotly_figure(sorted_periods, sorted_counts, cumulative_counts, sorted_deleted_counts, title, xaxis_title, yaxis_title, yaxis2_title, yaxis3_title, image_filename):
    fig = go.Figure()

    # Add new users bar graph
    fig.add_trace(go.Bar(
        x=sorted_periods, 
        y=sorted_counts, 
        name=f'New Users per {title}', 
        yaxis='y2', 
        marker=dict(color='rgba(255, 99, 132, 1)'),
        offset=1 
    ))

    # Add cumulative new users line graph
    fig.add_trace(go.Scatter(
        x=sorted_periods, 
        y=cumulative_counts, 
        mode='lines+markers', 
        name=f'Cumulative New Users', 
        line=dict(color='rgba(54, 162, 235, 1)'),
    ))

    # Add deleted users bar graph
    fig.add_trace(go.Bar(
        x=sorted_periods, 
        y=sorted_deleted_counts, 
        name=f'Deleted Users per {title}', 
        yaxis='y3', 
        marker=dict(color='rgba(255, 159, 64, 1)'),
    ))

    # Update layout
    fig.update_layout(
        title=f'User Statistics per {title}',
        xaxis=dict(title=xaxis_title),
        yaxis=dict(
            title=yaxis_title,
            titlefont=dict(color='rgba(54, 162, 235, 1)'),
            tickfont=dict(color='rgba(54, 162, 235, 1)')
        ),
        yaxis2=dict(
            title=yaxis2_title,
            titlefont=dict(color='rgba(255, 99, 132, 1)'),
            tickfont=dict(color='rgba(255, 99, 132, 1)'),
            overlaying='y',
            side='right'
        ),
        yaxis3=dict(
            title=yaxis3_title,
            titlefont=dict(color='rgba(255, 159, 64, 1)'),
            tickfont=dict(color='rgba(255, 159, 64, 1)'),
            anchor='free',
            overlaying='y',
            side='right',
            position=1
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        barmode='group',
    )

    # Save the figure as an image
    image_path = f'static/images/{image_filename}.png'
    full_image_path = os.path.join(os.path.dirname(__file__), image_path)
    fig.write_image(full_image_path)
    fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    return fig_html, image_path
