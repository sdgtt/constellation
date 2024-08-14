def url_gen(
    jenkins_server,
    jenkins_port,
    project_name,
    build_number,
    board,
    hdl_commit="NA",
    linux_commit="NA",
    trigger="NA",
    jenkins_base_path="/jenkins",
):
    """Utility method for generating urls"""

    if jenkins_port:
        jenkins_server = jenkins_server + ":" + jenkins_port

    if jenkins_base_path:
        jenkins_server = jenkins_server + jenkins_base_path

    url_project_name = "http://{}/job/{}/".format(
        jenkins_server, project_name.replace("/", "/job/")
    )

    url_build_number = "http://{}/job/{}/{}/".format(
        jenkins_server, project_name.replace("/", "/job/"), build_number
    )

    url_pytest_report = "http://{}/job/{}/{}/{}/".format(
        jenkins_server,
        project_name.replace("/", "/job/"),
        build_number,
        board.replace("-", "_"),
    )
    url_artifacts_dmesg = "http://{}/job/{}/{}/artifact/dmesg_{}_err.log".format(
        jenkins_server, project_name.replace("/", "/job/"), build_number, board
    )

    url_artifacts_drivers = "http://{}/job/{}/{}/artifact/{}_missing_devs.log".format(
        jenkins_server, project_name.replace("/", "/job/"), build_number, board
    )

    trigger_dict = trigger.split(":")

    if len(trigger_dict) == 3:
        if trigger_dict[0] == "auto":
            trigger_project_name = trigger_dict[1].split("/")[0]
            trigger_build_number = trigger_dict[2]
            url_trigger = "http://{}/job/{}/{}/".format(
                jenkins_server, trigger_project_name, trigger_build_number
            )
    else:
        url_trigger = trigger

    if not hdl_commit == "NA":
        url_hdl_commit = "https://github.com/analogdevicesinc/hdl/commits/{}".format(
            hdl_commit
        )
    else:
        url_hdl_commit = "NA"

    if not linux_commit == "NA":
        url_linux_commit = (
            "https://github.com/analogdevicesinc/linux/commits/{}".format(linux_commit)
        )
    else:
        url_linux_commit = "NA"

    return {
        "Jenkins Project Name": url_project_name,
        "Jenkins Build Number": url_build_number,
        "pyadi Tests": url_pytest_report,
        "Linux Tests dmesg": url_artifacts_dmesg,
        "Linux Tests drivers": url_artifacts_drivers,
        "HDL Commit": url_hdl_commit,
        "Linux Commit": url_linux_commit,
        "Trigger": url_trigger,
    }


def artifact_url_gen(
    jenkins_server,
    jenkins_port,
    project_name,
    build_number,
    board,
    jenkins_base_path="/jenkins",
):
    """Utility method for generating artifact urls"""

    if jenkins_port:
        jenkins_server = jenkins_server + ":" + jenkins_port

    if jenkins_base_path:
        jenkins_server = jenkins_server + jenkins_base_path

    uart_boot_log = "http://{}/job/{}/{}/artifact/uart_boot_{}.log".format(
        jenkins_server, project_name.replace("/", "/job/"), build_number, board
    )
    adi_diagnostic = "http://{}/job/{}/{}/artifact/{}_diag_report.tar.bz2".format(
        jenkins_server, project_name.replace("/", "/job/"), build_number, board
    )

    return {
        "UART BOOT LOG": uart_boot_log,
        "ADI DIAGNOSTIC REPORT": adi_diagnostic,
    }


def filter_gen(query):
    filter_dict = {}
    if query:
        fields = query.split("&")
        for field in fields:
            if len(field.split("=")) >= 2:
                field_name = field.split("=")[0]
                field_value = field.split("=")[1]
                filter_dict.update({field_name: field_value.split(",")})
    return filter_dict


def append_url_to_dict(
    boot_test_dict,
    jenkins_url="localhost",
    jenkins_port=None,
    jenkins_base_path="/jenkins",
):
    # print(boot_test_dict)
    url_dict = url_gen(
        jenkins_server=jenkins_url,
        jenkins_port=jenkins_port,
        jenkins_base_path=jenkins_base_path,
        project_name=boot_test_dict["jenkins_project_name"],
        build_number=boot_test_dict["jenkins_build_number"],
        board=boot_test_dict["boot_folder_name"],
        hdl_commit=boot_test_dict["hdl_hash"].split()[0],
        linux_commit=boot_test_dict["linux_hash"].split()[0],
        trigger=boot_test_dict["jenkins_trigger"],
    )
    artifacts_url_dict = artifact_url_gen(
        jenkins_server=jenkins_url,
        jenkins_port=jenkins_port,
        project_name=boot_test_dict["jenkins_project_name"],
        build_number=boot_test_dict["jenkins_build_number"],
        board=boot_test_dict["boot_folder_name"],
        jenkins_base_path=jenkins_base_path,
    )
    url_dict.update(artifacts_url_dict)
    for field, url_value in url_dict.items():
        boot_test_dict.update({field.lower().replace(" ", "_") + "_url": url_value})
    return boot_test_dict


def result_json_url(
    result_json,
    jenkins_url="localhost",
    jenkins_port=None,
    jenkins_base_path="/jenkins",
):
    new_result_json = {}
    for k, v in result_json.items():
        if k in ["hits"]:
            new_v = []
            for el in v:
                new_el = append_url_to_dict(
                    el, jenkins_url, jenkins_port, jenkins_base_path
                )
                new_v.append(new_el)
            new_result_json[k] = new_v
        else:
            new_result_json[k] = v
    return new_result_json
