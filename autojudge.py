# /// autojudge
# requires-python = ">=3.12"
# dependencies = [
#   requests
# ]
# ///

import requests, os, json, argparse

CONFIG_FILENAME = os.path.expanduser(os.path.sep.join(["~", ".config", "autojudge", "settings.json"]))


class Data:
    def __init__(self, token: str, contest: str, dir: str | None, data=None) -> None:
        self.token = token
        self.contest = contest
        self.data = {"token": self.token, "contests": {dir: self.contest}} if data is None else data
        self.connection = Connection(self.token)
        result = self.connection.get("contest-status-json", contest_id=self.contest)
        self.problems = result["problems"]
        self.lang_name = result["compilers"][0]["short_name"]
        self.sfx = result["compilers"][0]["src_sfx"]
    

    @classmethod
    def read(cls, filename: str, dir: str):
        data = json.load(open(filename, 'rt', encoding="utf-8"))
        if dir not in data["contests"]:
            data["contests"][dir] = input("Input contest id for this directory: ")
        return cls(data["token"], data["contests"][dir], None, data)
    

    def write(self, filename: str) -> None:
        json.dump(self.data, open(filename, "wt", encoding="utf-8"))
    

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
        result = self.connection.post("submit-run", {"prob_id": id, "lang_id": self.lang_name}, {"file": file}, contest_id=self.contest)
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
    if not os.path.exists(CONFIG_FILENAME):
        token = input("Input your API token: ")
        contest = input("Input contest id for this dir: ")
        data = Data(token, contest, os.path.dirname(args.file.name))
        data.write(CONFIG_FILENAME)
    data = Data.read(CONFIG_FILENAME, os.path.dirname(args.file.name))
    try:
        run_id = data.send_problem(os.path.basename(args.file.name).removesuffix(data.sfx), args.file)
    except KeyError:
        print("Avalible problems:", ", ".join([problem["short_name"] for problem in data.problems]))
        prob_name = input("Choose problem from listed above: ")
        run_id = data.send_problem(prob_name, args.file)
    print(run_id)

if __name__ == "__main__":
    main()
