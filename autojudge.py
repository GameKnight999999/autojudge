# /// autojudge
# requires-python = ">=3.12"
# dependencies = [
#   requests,
#   configparser
# ]
# ///

import requests, configparser, os, argparse


CONFIG_FILENAME = "autojudge.config"


def get(action: str, **params: str):
    response = requests.get(f"https://ejudge.letovo.ru/ej/client/{action}", params, headers=headers)
    response.raise_for_status()
    data = response.json()
    if not data["ok"]:
        raise requests.RequestException(data["error"], response=response, request=response.request)
    return data["result"]


def post(action: str, data, files, **params: str):
    response = requests.post(f"https://ejudge.letovo.ru/ej/client/{action}", data, params=params, headers=headers, files=files)
    response.raise_for_status()
    data = response.json()
    if not data["ok"]:
        raise requests.RequestException(data["error"], response=response, request=response.request)
    return data["result"]


def setup() -> None:
    global config, headers, args
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="a python file to send as solution", type=argparse.FileType(encoding="utf-8"))
    parser.add_argument("-n", "--no-config", help="Do not use data from config file", action="store_true")
    args = parser.parse_args()
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILENAME) and not args.no_config:
        config.read(CONFIG_FILENAME, encoding='utf-8')
    else:
        config.add_section("settings")
        config.set("settings", "token", input("Input your API token: "))
        config.set("settings", "contest", input("Input contest id: "))
    headers = {
        "Authorization": f"Bearer AQAA{config["settings"]["token"]}",
        "Accept": "application/json"
    }


def main() -> None:
    setup()
    result = get("contest-status-json", contest_id=config["settings"]["contest"])
    if not config.has_option("settings", "problem"):
        print("Avalible problems:", end=" ")
        print(*[problem["short_name"] for problem in result["problems"]], sep=", ")
        prob_name = input("Input problem name from the list: ")
        for problem in result["problems"]:
            if problem["short_name"] == prob_name:
                config["settings"]["problem"] = str(problem["id"])
    result = post("submit-run", {"prob_id": config["settings"]["problem"], "lang_id": "python3"}, {"file": args.file}, contest_id=config["settings"]["contest"])
    print("Run id:", result["run_id"])
    if not args.no_config:
        config.write(open(CONFIG_FILENAME, 'wt', encoding='utf-8'))


    


if __name__ == "__main__":
    main()
