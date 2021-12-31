from flask import Flask, render_template
from pages.hwtests import allboards as ab
from pages.pyadi.plots import gen_line_plot_html
from models import boards as b
from models import boot_tests as bt

# from junit2htmlreport import parser

app = Flask(__name__)


@app.route("/")
def hello_world():
    return render_template("index.html")


# @app.route("/report")
# def report():
#     ref = "pages/zynq_adrv9361_z7035_bob_reports.xml"
#     report = parser.Junit(ref)
#     return report.html()


@app.route("/boards")
def allboards():
    # retrieve boards from elastic server
    # filter by jenkins_project_name
    jenkins_project_name = "HW_tests/HW_test_multiconfig"
    boards_ref = b.Boards(jenkins_project_name).boards
    headers = ["Board", "Status"]
    boards = [
        {
            "Online": board.is_online,
            "Board": board.board_name,
            "Status": board.boot_test_result,
            "Jenkins Project Name": board.jenkins_project_name,
            "Build Number": board.jenkins_build_number,
            "Tested branch": board.source_adjacency_matrix,
            "HDL Commit": board.hdl_hash,
            "Linux Commit": board.linux_hash,
            "Failure reason": "None"
            if len(board.boot_test_failure) == 0
            else board.boot_test_failure,
        }
        for board in boards_ref
    ]

    summary = {
        "Total Boards": len(boards),
        "Passing": len([board for board in boards if board["Status"] == "Pass"]),
        "Online": len([board for board in boards if board["Online"] == True]),
    }
    summary.update(
        {"Passing Percent": 100 * summary["Passing"] / summary["Total Boards"]}
    )
    summary.update(
        {"Online Percent": 100 * summary["Online"] / summary["Total Boards"]}
    )
    return render_template(
        "hwtests/allboards.html", headers=headers, boards=boards, summary=summary
    )


@app.route("/board/<board_name>")
def board(board_name):
    # filter by jenkins_project_name
    jenkins_project_name = "HW_tests/HW_test_multiconfig"
    boot_tests = bt.BoardBootTests(board_name, jenkins_project_name).boot_tests

    boards = [
        {
            "Status": test.boot_test_result,
            "u-boot Reached": test.uboot_reached,
            "Linux Booted": test.linux_prompt_reached,
            "Linux Tests": {
                "dmesg_errors": test.dmesg_errors_found,
                "drivers_missing": test.drivers_missing,
            },
            "pyadi Tests": {
                "pass": str(int(test.pytest_tests) - int(test.pytest_failures)),
                "fail": test.pytest_failures,
            },
            "Tested branch": test.source_adjacency_matrix,
            "HDL Commit": test.hdl_hash,
            "Linux Commit": test.linux_hash,
            "Jenkins Project Name": test.jenkins_project_name,
            "Jenkins Build Number": test.jenkins_build_number,
            "Jenkins Job Date:": test.jenkins_job_date,
            "Failure reason": "None"
            if len(test.boot_test_failure) == 0
            else test.boot_test_failure,
        }
        for test in boot_tests
    ]
    return render_template("hwtests/board.html", board_name=board_name, boards=boards)


@app.route("/kibana/<visualization>")
def kibana(visualization):
    return render_template("kibana/index.html", visualization=visualization)


@app.route("/pyadi-iio/<vendor>")
def pyadi(vendor: str):
    import yaml

    with open("board_table.yaml", "r") as stream:
        data_loaded = yaml.safe_load(stream)
    # boards = list(data_loaded.keys())
    # print(boards)
    print("vendor", vendor)
    if vendor == "all" or vendor == "":
        return render_template("pyadi_iio/index.html", boards=data_loaded)

    out = {}
    for board in data_loaded:
        if vendor == "xilinx":
            if "xilinx" in board or "zynq" in board or "pluto" in board:
                out[board] = data_loaded[board]
        if vendor == "intel":
            if "intel" in board or "socfpga" in board or "arria10" in board:
                out[board] = data_loaded[board]

    return render_template("pyadi_iio/index.html", boards=out)


@app.route("/pyadi-iio/design/<design>")
def pyadi_design(design: str):
    # import yaml
    # with open("board_table.yaml", 'r') as stream:
    #     data_loaded = yaml.safe_load(stream)
    print(design)
    fightml = gen_line_plot_html([1, 2, 3], [1, 2, 3], "x", "y", "Test")

    return render_template("pyadi_iio/boards.html", fig=fightml, design=design)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
