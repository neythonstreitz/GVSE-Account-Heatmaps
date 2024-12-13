# Import packages
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

import pandas as pd
import plotly.express as px
import pgeocode

import os

def get_heatmap_data():

    # Upload Ready data
    ready_data_path = os.environ["READY_PATH"]
    ready_data_df = pd.read_excel(ready_data_path, engine='pyxlsb')

    ready_keep_columns = ["SAV Name", "Business Entity", "Product List Price $", "LDOS FY",
                "Install Site Name", "Install Site Address 1", "Install Site City", "Install Site State", "Install Site Postal Code"]
    ready_data_df = pd.DataFrame(ready_data_df, columns=ready_keep_columns)
    ready_data_df= ready_data_df.rename({"SAV Name": "Account Name", 
                                     "Product List Price $": "Total Spend"}, axis=1)

    # Upload SPOT data
    spot_data_path = os.environ["SPOT_PATH"]
    spot_data_df = pd.read_excel(spot_data_path)

    spot_keep_columns = ["Account Name", "Top EquipMake Share%", "Top Provider Share%",
                "Oppty Score ", "Threat Score", "Budget ($K)", "Remaining Budget ($K)"] #Oppty Score has a space after... need to fix
    spot_data_df = pd.DataFrame(spot_data_df, columns=spot_keep_columns)


    # Split Equipment share column to Equipment Maker + Percentage
    spot_data_df[["Primary Vendor", "Primary Vendor Share %"]] = spot_data_df["Top EquipMake Share%"].str.split("(", n=1, expand=True)


    # Split Partner share column to Top Partner + Percentage
    spot_data_df[["Top Partner", "Top Partner Share %"]] = spot_data_df["Top Provider Share%"].str.split("(", n=1, expand=True)

    return ready_data_df, spot_data_df

def get_lat_long(df: pd.DataFrame):

    nomi = pgeocode.Nominatim('us')
    
    df["Install Site Postal Code"] = df["Install Site Postal Code"].astype(str)
    df["Latitude"] = nomi.query_postal_code(df['Install Site Postal Code'].tolist()).latitude.tolist()
    df["Longitude"] = nomi.query_postal_code(df['Install Site Postal Code'].tolist()).longitude.tolist()

    return df

def enhance_spot_data(df):
    # Enhance account data with SPOT data if Education account
    df = pd.merge(df, spot_df, how="left", on='Account Name')

    return df

def generate_ldos_count(df: pd.DataFrame):

    ldos_df = df.copy()

    ldos_only_df = ldos_df[ldos_df["LDOS FY"].notna()]

    ldos_spend_df = ldos_only_df.groupby(by=["Account Name"])["Total Spend"].sum()

    ldos_spend_df = ldos_spend_df.reset_index()

    ldos_spend_df = ldos_spend_df.rename(columns={"Total Spend": "Total LDoS"})

    return ldos_spend_df

def generate_account_frame(df: pd.DataFrame, heatmap_focus, tech_focus):

    # Determine if SLG or EDU customer
    df["Vertical"] = df["Account Name"].str.contains("SCHOOL").map({True: 'Education', 
                                                False: 'State & Local Gov'})

    group_by_vals = ["Account Name"]
    if tech_focus != "All":
        group_by_vals.append("Business Entity")

    ldos_df = generate_ldos_count(df)

    grouped_account_df = df.groupby(by=group_by_vals)

    overall_df = grouped_account_df.apply(
            lambda df: pd.Series(
                {
                    "Total Spend": df["Total Spend"].sum(), # Aggregate total spend based on per-product List price
                    "Vertical": df["Vertical"].mode()[0],   # Vertical should be same across account, using mode to pass value through agg
                    "Install Site Postal Code": df["Install Site Postal Code"].mode()[0], # Use most common post code as primary address
                    "Total Sites": df["Install Site Postal Code"].nunique(), # Count number of unique sites
                    
                }
            ),
    include_groups=False)

    # Move account name from index to column
    overall_df = overall_df.reset_index()

    spot_df = enhance_spot_data(overall_df)

    spot_df = pd.merge(left=spot_df, right=ldos_df, how="left", on="Account Name")

    # Generate latitude longitude per account
    final_df = get_lat_long(spot_df)

    return final_df


'''
INITIALIZE DASH APP
'''

# Initialise the App
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])


'''
PREPARE DATA FOR PROCESSING

'''
# Get Account data
raw_df, spot_df = get_heatmap_data()

# Preprocess data
final_df = get_lat_long(raw_df)

'''
BUILD APP LAYOUT
'''
# Title
title = dcc.Markdown("GVSE Account Geo-Heatmap", className="bg-dark", style={"font-size": 30})

# Dropdown for heatmap visual
focus_view_dropdown = dcc.Dropdown(
    id="focus-view-dropdown", 
    options=["Geographic", "Account Spend", "SPOT"], 
    value="Geographic",
    style={'color': 'black'})

# Checklist
checklist = dbc.Checklist(
    id="show-account-text",
    options=[{"label": "Show account names", "value": 1}],
    value=[0],
    switch=True,
)

# Filter options by vertical
vertical_radio_items = dbc.RadioItems(id="cp-vertical-filter",
    options=[
        {"label": "All", "value": "All"},
        {"label": "State & Local Gov", "value": "State & Local Gov"},
        {"label": "Education", "value": "Education"}
    ],
    value="All",
    inline=True,
)

# Filter options by Businesss Entity
tech_options = ["All"] + final_df["Business Entity"].unique().tolist()
tech_radio_items = dbc.RadioItems(id="cp-tech-filter-radio", 
    options=[
        {"label": k, "value": k} for k in tech_options
    ],
    value="All",
    inline=True,
    style={"display": "none"},
)

spot_radio_items = dbc.RadioItems(
    id="spot-filter-radio",
    options=[
        {"label": "Total Budget", "value": "Budget ($K)"},
        {"label": "Opportunity Score", "value": "Oppty Score "},
        {"label": "Remaining Budget", "value": "Remaining Budget ($K)"},
        {"label": "Primary Vendor", "value": "Primary Vendor"},
        {"label": "Top Partner", "value": "Top Partner"}
    ],
    value="Budget ($K)",
    style={"color": "black", "display": "none"}
)

vendor_options = ["All"] + spot_df["Primary Vendor"].unique().tolist()
spot_vendor_dropdown = dcc.Dropdown(
    id="spot-vendor-dropdown",
    options=vendor_options,
    value="All",
    style={"color":"black", "display": "none"}
)

color_by_radio = dbc.RadioItems(
    id="color-by-radio",
    options=["Total Spend", "Total LDoS"],
    value="Total Spend",
    style={"display": "none"},
)

size_by_radio = dbc.RadioItems(
    id="size-by-radio",
    options=["Total Spend", "Total LDoS"],
    value="Total Spend",
    style={"display": "none"},
)


# Card content
card_content = [
    dbc.CardBody(
        [
            html.H5("Heatmap Control Panel"),
            html.P(
                "Heatmap Focus:",
            ),
            focus_view_dropdown,
            html.Br(),
            html.P(id="size-by-text", children=["Size Accounts by"], style={"display": "none"}),
            size_by_radio,
            html.P(id="color-by-text", children=["Color Accounts by"], style={"display": "none"}),
            color_by_radio,
            html.Br(),
            html.P(id="cp-vertical-text", children=["Filter by Vertical"], style={"display": "block"}),
            vertical_radio_items,
            html.P(id="spot-filter-text", children=["Color by SPOT Metric"], style={"display": "none"}),
            spot_radio_items,
            html.Br(),
            html.P(id="cp-tech-filter-text", children=["Filter Total Spend by Technology"], style={"display": "none"}),
            tech_radio_items,
            html.P(id="spot-vendor-text", children=["Filter by Top Vendor Share"], style={"display": "none"}),
            spot_vendor_dropdown,
            html.Br(),
            html.Hr(),
            html.H6("Optional input"),
            checklist,
            html.Br(),
        ]
    ),
]

# App Layout
app.layout = html.Div(
    [
        dbc.Row([dbc.Col([title], style={"text-align": "center", "margin": "auto"})]),
        html.Br(),
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Row(dbc.Card(card_content, color="info")),
                            ],
                            width=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                dcc.Graph(id="heatmap-figure"), 
                                color="light"
                            ),
                            width=8,
                        ),
                    ]
                )
            ]
        ),
    ]
)


@app.callback(
    [
        Output(component_id="color-by-text", component_property="style"),
        Output(component_id="color-by-radio", component_property="style"),
        Output(component_id="size-by-text", component_property="style"),
        Output(component_id="size-by-radio", component_property="style"),
        Output(component_id="cp-tech-filter-text", component_property="style"),
        Output(component_id="cp-tech-filter-radio", component_property="style"),
    ],
    Input(component_id="focus-view-dropdown", component_property="value")
)
def update_account_filter_options(dropdown_selection):

    if dropdown_selection == "Account Spend":
        return {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}

    return {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}

@app.callback(
    [
        Output(component_id="cp-vertical-text", component_property="style"),
        Output(component_id="cp-vertical-filter", component_property="style"),
        Output(component_id="spot-vendor-text", component_property="style"),
        Output(component_id="spot-vendor-dropdown", component_property="style"),
        Output(component_id="spot-filter-text", component_property="style"),
        Output(component_id="spot-filter-radio", component_property="style"),
    ],
    Input(component_id="focus-view-dropdown", component_property="value")
)
def update_spot_filter_options(dropdown_selection):

    if dropdown_selection == "SPOT":
        return {"display": "none"}, {"display": "none"}, {"display": "block"}, {"color": "black", "display": "block"}, {"display": "block"}, {"color": "black", "display": "block"}

    return {"display": "block"}, {"display": "block"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}

@app.callback(
    Output(component_id="heatmap-figure", component_property="figure"),
    [
        Input(component_id="focus-view-dropdown", component_property="value"),
        Input(component_id="show-account-text", component_property="value"),
        Input(component_id="cp-vertical-filter", component_property="value"),
        Input(component_id="cp-tech-filter-radio", component_property="value"),
        Input(component_id="spot-filter-radio", component_property="value"),
        Input(component_id="spot-vendor-dropdown", component_property="value"),
        Input(component_id="color-by-radio", component_property="value"),
        Input(component_id="size-by-radio", component_property="value"),
    ]
)
def create_mapbox(heatmap_focus, toggle_text, vertical_filter, data_filter, spot_filter, vendor_filter, color_by, size_by):

    df = generate_account_frame(final_df, heatmap_focus, data_filter)

    if vertical_filter != "All":
        df = df.query("Vertical == @vertical_filter")

    if data_filter != "All":
        print(f"Data filter: {data_filter}")
        df = df.query("`Business Entity` == @data_filter")

    # Enable/disable account name annotations
    text_trigger = [None, "Account Name"][len(toggle_text) - 1]

    if heatmap_focus == "Geographic":

        fig = px.scatter_mapbox(df, 
                                lat="Latitude", 
                                lon="Longitude",
                                text=text_trigger, 
                                hover_name="Account Name", 
                                hover_data=["Total Spend", "Total Sites"],
                                labels="Account Name",
                                color="Vertical",
                                zoom=6, 
                                height=800,
                                width=900,)
    elif heatmap_focus == "Account Spend":

        print(df.columns)

        fig = px.scatter_mapbox(df, 
                                lat="Latitude", 
                                lon="Longitude", 
                                hover_name="Account Name", 
                                hover_data=["Total Spend", "Total Sites"],
                                text=text_trigger,
                                color=color_by,
                                size=size_by,
                                color_continuous_scale=px.colors.sequential.RdBu, 
                                size_max=25,
                                labels="Account Name",
                                zoom=6, 
                                opacity=0.5,
                                height=800,
                                width=900,)
    else:
        if vendor_filter != "All":
            df = df.query("`Primary Vendor` == @vendor_filter")

        df = df.query("Vertical == 'Education'")
        fig = px.scatter_mapbox(df, 
                        lat="Latitude", 
                        lon="Longitude", 
                        hover_name="Account Name", 
                        hover_data=["Total Spend", "Total Sites", "Budget ($K)", "Primary Vendor", "Top Partner"],
                        text=text_trigger,
                        color=spot_filter,
                        size="Total Spend",
                        color_continuous_scale=px.colors.sequential.RdBu, 
                        size_max=15,
                        labels="Account Name",
                        zoom=6, 
                        opacity=0.5,
                        height=800,
                        width=900,)
    
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return fig


# Run the App
if __name__ == "__main__":
    app.run_server(debug=True)