# /// autojudge
# requires-python = ">=3.12"
# dependencies = [
#   requests
# ]
# ///

import requests, os, json, argparse

CONFIG_FILENAME = "autojudge.json"


class Data:
    def __init__(self, token: str, contest: str) -> None:
        self.token = token
        self.contest = contest
        self.connection = Connection(self.token)
        self.problems = self.connection.get("contest-status-json", contest_id=self.contest)["problems"]
    

    @classmethod
    def read(cls, filename: str):
        data = json.load(open(filename, 'rt', encoding="utf-8"))
        return cls(data["token"], data["contest"])
    

    def write(self, filename: str) -> None:
        json.dump({"token": self.token, "contest": self.contest}, open(filename, "wt", encoding="utf-8"))
    

    def send_problem(self, prob_id: str, file) -> str:
        if not prob_id.isdigit():
            for problem in self.problems:
                if prob_id == problem["short_name"]:
                    id = problem["id"]
                    break
            else:
                raise KeyError(prob_id)
        else:
            id = prob_id
        result = self.connection.post("submit-run", {"prob_id": id, "lang_id": "python3"}, {"file": file}, contest_id=self.contest)
        return result["run_id"]
    

    @property
    def headers(self) -> dict[str, str]:
        return {
        "Authorization": f"Bearer AQAA{self.token}",
        "Accept": "application/json"
        }


class Connection:
    def __init__(self, token: str) -> None:
        self.headers = {
        "Authorization": f"Bearer AQAA{token}",
        "Accept": "application/json"
        }


    def get(self, action: str, **params: str):
        response = requests.get(f"https://ejudge.letovo.ru/ej/client/{action}", params, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        if not data["ok"]:
            raise requests.RequestException(data["error"], response=response, request=response.request)
        return data["result"]


    def post(self, action: str, data, files, **params: str):
        response = requests.post(f"https://ejudge.letovo.ru/ej/client/{action}", data, params=params, headers=self.headers, files=files)
        response.raise_for_status()
        data = response.json()
        if not data["ok"]:
            raise requests.RequestException(data["error"], response=response, request=response.request)
        return data["result"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="file to send", type=argparse.FileType(encoding="utf-8"))
    args = parser.parse_args()
    config_path = os.path.join(os.path.dirname(args.file.name), CONFIG_FILENAME)
    if not os.path.exists(config_path):
        token = input("Input your API token: ")
        contest = input("Input contest id for this dir: ")
        data = Data(token, contest)
        data.write(config_path)
    data = Data.read(config_path)
    try:
        run_id = data.send_problem(os.path.basename(args.file.name).removesuffix(".py"), args.file)
    except KeyError:
        print("Avalible problems:", ", ".join([problem["short_name"] for problem in data.problems]))
        prob_name = input("Choose problem from listed above: ")
        run_id = data.send_problem(prob_name, args.file)
    print(run_id)

if __name__ == "__main__":
    main()
