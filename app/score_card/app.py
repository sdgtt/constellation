# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from datetime import date, datetime, timedelta

import dash_bootstrap_components as dbc
import dash_dangerously_set_inner_html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import Input, Output, State, dash_table, dcc, html
from flask import Markup

from ..models.score import Score


########################### Models #####################################
def request_data(project=None, branch=None, size=None, board=None, offset=None):
    default_jenkins_project = "HW_tests/HW_test_multiconfig"
    default_branch = "boot_partition_main"
    default_size = 7
    default_offset = 0
    jenkins_project = project if project else default_jenkins_project
    size = size if size else default_size
    offset = offset if offset else default_offset
    board = board if board else None
    branch = branch if branch else default_branch
    deprecated = []
    sc = Score(
        jenkins_project=jenkins_project,
        size=int(size),
        branch=branch,
        board=board,
        deprecated=deprecated,
        offset=offset,
    )
    return sc.to_dict()

    # request_raw = 'http://localhost:5000/constellation/api/sc?'
    # if project:
    #     request_raw += 'jenkins_project={}'.format(project)
    # if branch:
    #     request_raw += '&branch={}'.format(branch)
    # if size:
    #     request_raw += '&size={}'.format(size)
    # if board:
    #     request_raw += '&board={}'.format(board)

    # response = requests.get(request_raw)
    # if response.status_code == 200:
    #     return response.json()
    # else:
    #     print("Query Failed!")


def get_df_booted(data):
    # create time-series based data frame
    data_dict = {
        "total": [],
        "logs_missing": [],
        "boards": [],
        "booted": [],
        "not_booted": [],
        "linux_prompt_not_reached": [],
        "uboot_not_reached": [],
        "drivers_enumerated": [],
        "drivers_missing": [],
        "dmesg_warnings_found": [],
        "dmesg_errors_found": [],
        "pytest_errors": [],
        "pytest_failures": [],
        "pytest_skipped": [],
        "pytest_tests": [],
    }
    index_set = []
    builds = [build for build in data["builds"].keys()]
    sd = datetime.strptime(
        data["builds"][builds[-1]]["jenkins_job_date"].split("T")[0], "%Y-%m-%d"
    )
    ed = datetime.strptime(
        data["builds"][builds[0]]["jenkins_job_date"].split("T")[0], "%Y-%m-%d"
    )
    drs = [sd + timedelta(days=x) for x in range((ed - sd).days + 1)]
    for dr in drs:
        found = False
        for build, build_data in data["builds"].items():
            dr_string = dr.strftime("%Y-%m-%d")
            build_data_d = build_data["jenkins_job_date"].split("T")[0]
            build_data_summary = data["summaries"][build]
            regression_data_summary = data["regressions"][build]
            if build_data_d == dr_string:
                index_set.append((dr, build, build_data["jenkins_trigger"]))
                # index_set.append(dr)
                data_dict["total"].append(len(data["boards"]))
                for k in data_dict:
                    if k in ["total"]:
                        continue
                    elif k in ["logs_missing"]:
                        data_dict[k].append(
                            len(regression_data_summary["regress_missing_logs"])
                        )
                        continue
                    data_dict[k].append(int(build_data_summary[k]["count"]))
                found = True
        if not found:
            index_set.append((dr, "NA", "NA"))
            # index_set.append(dr)
            for k in data_dict:
                data_dict[k].append(0)

    df = pd.DataFrame(
        data_dict,
        # index = pd.to_datetime(index_set)
        index=pd.MultiIndex.from_tuples(index_set, names=["date", "build", "trigger"]),
    )
    return df


def get_fig_logs(data):
    df = get_df_booted(data)
    df_index_ts = [index_ts[0] for index_ts in df.index.tolist()]
    # df_index_build = [index_ts[1] for index_ts in df.index.tolist()]
    # missing = df.loc[:, "boards"]
    fig = go.Figure(
        data=[
            go.Bar(
                name="Logs",
                x=df_index_ts,
                y=df.loc[:, "boards"].values.tolist(),
                text=df.loc[:, "boards"].values.tolist(),
            ),
            go.Bar(
                name="Missing Logs",
                x=df_index_ts,
                y=df.loc[:, "logs_missing"].values.tolist(),
                text=df.loc[:, "logs_missing"].values.tolist(),
            ),
        ]
    )
    fig.update_layout(
        barmode="stack", 
        title="Boot Logs Turnout",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=20, r=20),
    )
    return fig


def get_fig_booted(data):
    df = get_df_booted(data)
    df_index_ts = [index_ts[0] for index_ts in df.index.tolist()]
    # df_index_build = [index_ts[1] for index_ts in df.index.tolist()]
    fig = go.Figure(
        data=[
            go.Bar(
                name="Booted",
                x=df_index_ts,
                y=df.loc[:, "booted"].values.tolist(),
                text=df.loc[:, "booted"].values.tolist(),
            ),
            go.Bar(
                name="Linux Not Reached",
                x=df_index_ts,
                y=df.loc[:, "linux_prompt_not_reached"].values.tolist(),
                text=df.loc[:, "linux_prompt_not_reached"].values.tolist(),
            ),
            go.Bar(
                name="U-boot Not Reached",
                x=df_index_ts,
                y=df.loc[:, "uboot_not_reached"].values.tolist(),
                text=df.loc[:, "uboot_not_reached"].values.tolist(),
            ),
        ]
    )
    fig.update_layout(
        barmode="stack", 
        title="Boot Histogram",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=20, r=20),
    )
    return fig


def get_fig_linux(data):
    df = get_df_booted(data)
    df_index_ts = [index_ts[0] for index_ts in df.index.tolist()]
    # df_index_build = [index_ts[1] for index_ts in df.index.tolist()]
    fig = go.Figure(
        data=[
            go.Bar(
                name="IIO Devices Found",
                x=df_index_ts,
                y=df.loc[:, "drivers_enumerated"].values.tolist(),
                text=df.loc[:, "drivers_enumerated"].values.tolist(),
            ),
            go.Bar(
                name="IIO Devices not Found",
                x=df_index_ts,
                y=df.loc[:, "drivers_missing"].values.tolist(),
                text=df.loc[:, "drivers_missing"].values.tolist(),
            ),
        ]
    )
    fig.update_layout(
        barmode="stack", 
        title="IIO Devices",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=20, r=20),
    )
    return fig


def get_fig_dmesg(data):
    df = get_df_booted(data)
    df_index_ts = [index_ts[0] for index_ts in df.index.tolist()]
    # df_index_build = [index_ts[1] for index_ts in df.index.tolist()]
    fig = go.Figure(
        data=[
            go.Bar(
                name="Dmesg Warnings Found",
                x=df_index_ts,
                y=df.loc[:, "dmesg_warnings_found"].values.tolist(),
                text=df.loc[:, "dmesg_warnings_found"].values.tolist(),
            ),
            go.Bar(
                name="Dmesg Errors Found",
                x=df_index_ts,
                y=df.loc[:, "dmesg_errors_found"].values.tolist(),
                text=df.loc[:, "dmesg_errors_found"].values.tolist(),
            ),
        ]
    )
    fig.update_layout(
        barmode="stack", 
        title="DMESG Errors",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=20, r=20),
    )
    return fig


def get_fig_pyadi(data):
    df = get_df_booted(data)
    df_index_ts = [index_ts[0] for index_ts in df.index.tolist()]
    # df_index_build = [index_ts[1] for index_ts in df.index.tolist()]
    pytest_fails = (
        df.loc[:, "pytest_failures"]
        + df.loc[:, "pytest_skipped"]
        + df.loc[:, "pytest_errors"]
    )

    pytest_passed = df.loc[:, "pytest_tests"] - pytest_fails

    fig = go.Figure(
        data=[
            go.Bar(
                name="PYADI-IIO Tests Passed",
                x=df_index_ts,
                y=pytest_passed.values.tolist(),
                text=pytest_passed.values.tolist(),
            ),
            go.Bar(
                name="PYADI-IIO Tests Failures",
                x=df_index_ts,
                y=df.loc[:, "pytest_failures"].values.tolist(),
                text=df.loc[:, "pytest_failures"].values.tolist(),
            ),
            go.Bar(
                name="PYADI-IIO Tests Skipped",
                x=df_index_ts,
                y=df.loc[:, "pytest_skipped"].values.tolist(),
                text=df.loc[:, "pytest_skipped"].values.tolist(),
            ),
        ]
    )
    fig.update_layout(
        barmode="stack", 
        title="PYADI-IIO Tests",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=dict(l=20, r=20),
    )
    return fig


########################### Generators #####################################


def generate_logo():
    logo_path = "app/static/gco.svg"
    svg = open(logo_path).read()
    sc_logo_div = html.Div(
        children=[
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML(Markup(svg)),
            html.H3("Kuiper Linux CT Score Card"),
        ],
        id="sc_logo_div",
        style={"font-size": "15px"},
    )
    return sc_logo_div

def generate_filters_offcanvas(data):
    offcanvas = html.Div(
        [
            dbc.Button("Filters", id="open_filters_offcanvas", n_clicks=0),
            dbc.Offcanvas(
                generate_options(data),
                id="filters_offcanvas",
                title="Filters",
                is_open=False,
            ),
        ],
        style={
            "position": "absolute",
            "right": "0%",
            "bottom": "0%",
            "font-size": "15px"
        }
    )
    return offcanvas

def generate_header(data):
    header_div = html.Div(
        [
            dbc.Row(
                [
                    # dbc.Col(generate_logo(), width=10),
                    dbc.Col(generate_filters_offcanvas(data), width=2),
                ],
                align="start",
            ),
        ],
        style={
            "margin-left":"2%",
            "margin-right":"2%",
            "margin-top": "3%",
            "position": "relative",
            "font-size": "15px"
        }
    )

    return header_div

def generate_options(data):

    options_div = html.Div(
        children=[
            html.H5("Project"),
            dcc.Input(
                id="sc_project_options",
                type="text",
                placeholder="Jenkins project name",
                value="HW_tests/HW_test_multiconfig",
                style={"width": "100%", "font-size": "15px"},
            ),
            html.H5("Branch"),
            dcc.Dropdown(
                options=[
                    {
                        "label": "Boot Partition Main",
                        "value": "boot_partition_main",
                    },
                    {
                        "label": "Boot Partition Release",
                        "value": "boot_partition_release",
                    },
                    {
                        "label": "Boot Partition Next Stable",
                        "value": "boot_partition_next_stable",
                    },
                    {
                        "label": "Boot Partition 2022_r2",
                        "value": "boot_partition_2022_r2",
                    },
                ],
                placeholder="Select target branch",
                value="boot_partition_main",
                id="sc_branch_options",
            ),
            html.H5("Size"),
            dcc.Input(
                id="sc_size_options",
                type="number",
                min=1,
                max=10,
                placeholder="No. of builds to Analyze",
                value=7,
                style={"width": "100%","font-size": "15px"},
            ),
            html.H5("Offset"),
            dcc.Input(
                id="sc_offset_options",
                type="number",
                min=0,
                max=20,
                placeholder="No. of builds from the latest to analyze",
                value=0,
                style={"width": "100%","font-size": "15px"},
            ),
            html.H5("Board"),
            dcc.Dropdown(
                options=[{"label": board, "value": board} for board in data["boards"]],
                placeholder="Select target board",
                id="sc_board_options",
            ),
        ],
    )

    sc_filters_row = html.Div(
        children=[options_div], id="sc_filters_row", className="row"
    )

    sc_filters_container = html.Div(
        children=[sc_filters_row], id="sc_filters_container", className="container"
    )

    return sc_filters_container


def generate_dash_table(data, target, groupby="item"):

    latest_build = list(data["builds"].keys())[0]
    label = " ".join([ele.title() for ele in target.split("_")])

    # groupby config
    table_cols = {"item": label, "board": "Board", "build": "Build"}
    if groupby == "board":
        table_cols = {"board": "Board", "item": label, "build": "Build"}

    # unpack data
    data_raw = []
    for build, build_data in data["summaries"].items():
        for item, boards in build_data[target]["data"].items():
            for board in boards:
                data_raw.append([build, item, board])

    # convert data into data frame
    df = pd.DataFrame(data_raw, columns=["build", "item", "board"])

    # group data by item
    data_processed = []
    for fname, fdata in df.groupby(by=groupby):
        fields = [k for k in table_cols.keys()]
        data_processed.append(
            {
                fields[0]: fname,
                fields[1]: "\n".join(fdata[fields[1]].tolist()),
                fields[2]: "\n".join(
                    [
                        f"{build} (L)" if build == latest_build else build
                        for build in fdata[fields[2]].tolist()
                    ]
                ),
            }
        )

    # generate dash table
    cols = [{"name": _label, "id": _id} for _id, _label in table_cols.items()]
    dt = dash_table.DataTable(
        style_data={"whiteSpace": "pre-line", "height": "auto"},
        style_cell={
            "textAlign": "left",
            "vertical-align": "top",
            "font-weight": "var(--bs-body-font-weight)",
        },
        style_header={
            "color": "3e3e3e",
        },
        data=data_processed,
        columns=cols,
    )
    return dt


def generate_top_boot_failing(data):

    tabs = dbc.Tabs(
                [
                    dbc.Tab(
                        generate_dash_table(data, "not_booted", "board"),
                        tab_id="tab-1",
                        label="Failing Boards (Non Booting)",
                    ),
                    dbc.Tab(generate_dash_table(data, "not_booted"),
                    tab_id="tab-2",
                    label="Failures"),
                ],
                active_tab="tab-1",
            )
    style = {"margin-top": "2%", "margin-bottom": "2%"}
    top_boot_failing_div = dbc.Row(
        children=[
            dbc.Col(tabs, style=style, width=8),
            dbc.Col(
                dcc.Graph(id="g_boot_test_summary", figure=get_fig_booted(data)),width=4
            ),
        ],
        id="top_boot_failing_div",
    )
    return top_boot_failing_div


def generate_drivers_enumeration(data):
    tabs = dbc.Tabs(
            [
                dbc.Tab(
                        generate_dash_table(data, "drivers_missing", "board"),
                        tab_id="tab-1",
                        label="Failing Boards (Failed Device Enumeration)",
                    ),
                dbc.Tab(
                    generate_dash_table(data, "drivers_missing"),
                    tab_id="tab-2",
                    label="Missing Drivers",
                ),
            ],
            active_tab="tab-1"
        )
    style = {"margin-top": "2%", "margin-bottom": "2%"}
    drivers_enumeration_div = dbc.Row(
        children=[
            dbc.Col(tabs, style=style, width=8),
            dbc.Col(
                dcc.Graph(id="g_linux_test_summary", figure=get_fig_linux(data)),width=4
            ),
        ],
        id="drivers_enumeration_div",
    )
    return drivers_enumeration_div


def generate_dmesg_errors(data):
    tabs = dbc.Tabs(
        [
            dbc.Tab(
                generate_dash_table(data, "dmesg_errors_found", "board"),
                tab_id="tab-1",
                label="Failing Boards (Dmesg Errors)",
            ),
            dbc.Tab(
                generate_dash_table(data, "dmesg_errors_found"),
                tab_id="tab-2",
                label="Dmeg Errors",
            ),
        ],
        active_tab="tab-1"
    )
    style = {"margin-top": "2%", "margin-bottom": "2%"}
    dmesg_errors_div = dbc.Row(
        children=[
            dbc.Col(tabs, style=style, width=8),
            dbc.Col(
                dcc.Graph(id="g_linux_dmesg_summary", figure=get_fig_dmesg(data)),width=4
            ),
        ],
        id="dmesg_errors_div",
    )
    return dmesg_errors_div


def generate_pytest_results(data):

    tabs = dbc.Tabs(
        [
            dbc.Tab(
                generate_dash_table(data, "pytest_failures", "board"),
                tab_id="tab-1",
                label="PyADI IIO Failures",
            ),
            dbc.Tab(
                generate_dash_table(data, "pytest_errors", "board"),
                tab_id="tab-2",
                label="PyADI IIO Errors",
            ),
            dbc.Tab(
                generate_dash_table(data, "pytest_skipped", "board"),
                tab_id="tab-3",
                label="PyADI IIO Skipped",
            ),
        ], active_tab="tab-1"
    )
    style = {"margin-top": "2%", "margin-bottom": "2%"}
    pyadi_test_div = dbc.Row(
        children=[
            dbc.Col(tabs, style=style, width=8),
            dbc.Col(
                dcc.Graph(id="g_pyadi_test", figure=get_fig_pyadi(data)),width=4
            ),
        ],
        id="pyadi_test_div",
    )
    return pyadi_test_div


def generate_at_glance(data):
    sc_at_glance_div = html.Ul(
        children=[
            # html.Li("Summary", className="list-group-item display-6"),
            html.Li(
                "Jenkins Project: {}".format(data["jenkins_project"]),
                className="list-group-item",
            ),
            html.Li("Branch: {}".format(data["branch"]), className="list-group-item"),
            html.Li(
                "Builds Analyzed ({}):\n {}".format(
                    len(data["builds"]), ",".join([build for build in data["builds"]])
                ),
                className="list-group-item",
                style={"whiteSpace": "pre-line"},
            ),
            html.Li(
                "Boards Tested ({}):\n {}".format(
                    len(data["boards"]), "\n".join([build for build in data["boards"]])
                ),
                className="list-group-item",
                style={"whiteSpace": "pre-line"},
            ),
        ],
        id="sc_at_glance_div",
        className="list-group list-group-flush",
    )
    return sc_at_glance_div


def generate_panel(data):
    style = {"margin-top": "2%", "margin-bottom": "2%"}
    sc_panel_div = dbc.Row(
        children=[
            dbc.Col(generate_at_glance(data), style=style, width=4),
            dbc.Col(
                [
                    dbc.Row(dcc.Graph(id="g_logs_turnout", figure=get_fig_logs(data))),
                ], width=4
            ),
        ],
        justify="between",
        id="sc_panel_div",
    )
    return sc_panel_div

def generate_report(data):
    report_div = generate_summaries(data)
    return report_div

def report_tabs(data, active_tab="t_summary"):

    tabs = dbc.Tabs([
                    dbc.Tab(label='Summaries', tab_id="t_summary", children=[
                        generate_panel(data)
                    ]),
                    dbc.Tab(label='Boot Test', tab_id="t_boot_test", children=[
                        generate_top_boot_failing(data),
                    ]),
                    dbc.Tab(label='Linux Test - IIO Drivers', tab_id="t_iio", children=[
                        generate_drivers_enumeration(data)
                    ]),
                    dbc.Tab(label='Linux Test - DMESG', tab_id="t_dmesg", children=[
                        generate_dmesg_errors(data),
                    ]),
                    dbc.Tab(label='PYADI-IIO Tests', tab_id="t_pyadi", children=[
                        generate_pytest_results(data)
                    ]),
            ],
            active_tab=active_tab,
            id="sc_report_tab"
        )
    return tabs

def generate_report_tabs(data):
    return html.Div(
        id="sc_report_div",
        style = {},
        children=[
            report_tabs(data)
        ]
    )

########################### Callbacks #####################################


def register_callbacks(app):
    @app.callback(
        Output("sc_report_div", "children"),
        [
            Input("sc_project_options", "value"),
            Input("sc_branch_options", "value"),
            Input("sc_size_options", "value"),
            Input("sc_board_options", "value"),
            Input("sc_offset_options", "value"),
            Input("sc_report_tab","active_tab"),
        ],
    )
    def update_report(project, branch, size, board, offset, active_tab):
        return report_tabs(
            request_data(project=project, branch=branch, size=size, board=board, offset=offset),
            active_tab=active_tab
        )

    @app.callback(
        Output("filters_offcanvas", "is_open"),
        Input("open_filters_offcanvas", "n_clicks"),
        [State("filters_offcanvas", "is_open")],
    )
    def toggle_offcanvas(n1, is_open):
        if n1:
            return not is_open
        return is_open


########################### Main Layout #####################################

layout = html.Div(
    children=[
        generate_header(request_data()),
        generate_report_tabs(request_data()),
    ],
    id="main_panel",
    style={ "font-size": "15px"}
)