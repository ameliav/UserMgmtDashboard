#!/usr/bin/env python3
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import datetime

app = dash.Dash(__name__)
df = pd.read_csv('combinedUsers.csv')

df['RSTUDIO'] = pd.to_datetime(df['RSTUDIO'])
df['ZEPPELIN'] = pd.to_datetime(df['ZEPPELIN'])
df['HOME DIRECTORY'] = pd.to_datetime(df['HOME DIRECTORY'])
df["LAST UPDATE"] = df[["RSTUDIO", "ZEPPELIN", "HOME DIRECTORY"]].max(axis=1)
df["LAST UPDATE"] = df["LAST UPDATE"].dt.strftime('%Y-%m-%d %H:%M')

PAGE_SIZE = 5

tablehome= dash_table.DataTable(
                id='table-paging-with-graph',
                columns=[
                    {"name": i, "id": i} for i in df.columns
                ],
                page_current=0,
                page_size=25,
                page_action='custom',

                filter_action='custom',
                filter_query='',

                sort_action='custom',
                sort_mode='single',
                sort_by=[],

				style_cell_conditional=[
					{
					'if': {'column_id': c},
					'display': 'none'
					} for c in ['ZEPPELIN', 'RSTUDIO', 'HOME DIRECTORY']
				],

				style_table={
					'maxHeight': '450px',
					'overflowY': 'scroll'
				},
				style_as_list_view=True,
				style_cell={'fontSize':11, 'font-family':'Arial', 'text-align':'left'},
				style_header={'backgroundColor': 'white','fontWeight': 'bold', 'text-align':'left'}
				)

def serve_layout():
	return html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [html.Div(
                    [html.Img(
                            src=app.get_asset_url("logo.PNG"),
                            id="plotly-image",
                            style={
                                "height": "50px", #"width": "22%",
                                "marginBottom": "25px",
								"marginTop": "25px",
								"boxShadow": "2px 2px 2px lightgrey",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [html.Div(
                            [html.H3(
                                    "User Management Dashboard",
                                    style={"margin-bottom": "0px"},
                                ),
                                html.H5("Analytics Platform", style={"margin-top": "0px"}),
                            ]
                        )
                    ],
                    className="eight columns",
                    id="title",
                )
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        html.Div(
            [html.Div(
                    [html.Div(
                            [html.Div(
                                    [html.H6(id="well_text"), html.P("Business Users"), html.H5(len(df.index))],
                                    id="wells",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="gasText"), html.P("Groups"), html.H5(df['GROUP'].nunique())],
                                    id="gas",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="oilText"), html.P("Analytical Tools"),html.H5("2")],
                                    id="oil",
                                    className="mini_container",
                                )
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [html.Div(
                    [
					html.P("Users Last Update"),
					tablehome,
					html.Br(),
					html.P("Current time: "+str(datetime.datetime.now())),
					],
                    className="pretty_container",
                ),
            ], className="row flex-display",
        ),

    ],
    id="mainContainer",
    style={"display": "flex", "flexDirection": "column","margin":"auto","maxWidth":"850px"},
)

app.layout= serve_layout

operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]

def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value
    return [None] * 3


@app.callback(
    Output('table-paging-with-graph', "data"),
    [Input('table-paging-with-graph', "page_current"),
     Input('table-paging-with-graph', "page_size"),
     Input('table-paging-with-graph', "sort_by"),
     Input('table-paging-with-graph', "filter_query")])

def update_table(page_current, page_size, sort_by, filter):
    filtering_expressions = filter.split(' && ')
    dff = df
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    if len(sort_by):
        dff = dff.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )

    return dff.iloc[
        page_current*page_size: (page_current + 1)*page_size
    ].to_dict('records')

# Main
server = app.server
if __name__ == '__main__':
        app.run_server(debug=True)
