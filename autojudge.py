# /// autojudge
# requires-python = ">=3.12"
# dependencies = [
#   requests
# ]
# ///

import requests, os, json, argparse, time

CONFIG_FILENAME = os.path.expanduser(os.path.sep.join(["~", ".config", "autojudge", "settings.json"]))
STATUS = ["OK", "CE", "RT", "TL", "PE", "WA", "CF", "PT", "AC", "IG", "DQ", "PD", "ML", "SE", "SV", "WT", "PR", "RJ", "SK", "SY", "SM"]


class Data:
    def __init__(self, token: str, contest: str, dir: str | None, data=None) -> None:
        self.token = token
        self.contest = contest
        self.data = {"token": self.token, "contests": {dir: self.contest}} if data is None else data
        self.connection = Connection(self.token)
        result = self.connection.get("contest-status-json", contest_id=self.contest)
        self.problems = result["problems"]
        self.compilers = result["compilers"]
    

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
        file_ext = os.path.splitext(file.name)[1]
        for compiler in self.compilers:
            if compiler["src_sfx"] == file_ext:
                lang_id = compiler["id"]
                break
        else:
            raise KeyError(file_ext)
        result = self.connection.post("submit-run", {"prob_id": id, "lang_id": lang_id}, {"file": file}, contest_id=self.contest)
        return result["run_id"]
    

    def get_status(self, run_id: str) -> str:
        result = self.connection.get("run-status-json", contest_id=self.contest, run_id=run_id)
        while result["run"]["status"] >= len(STATUS):
            time.sleep(1)
            result = self.connection.get("run-status-json", contest_id=self.contest, run_id=run_id)
        return STATUS[result["run"]["status"]]


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
        if not os.path.isdir(os.path.dirname(CONFIG_FILENAME)):
            os.makedirs(os.path.dirname(CONFIG_FILENAME))
    else:
        data = Data.read(CONFIG_FILENAME, os.path.dirname(args.file.name))
    data.write(CONFIG_FILENAME)
    try:
        run_id = data.send_problem(os.path.splitext(os.path.basename(args.file.name))[0], args.file)
    except KeyError:
        print("Avalible problems:", ", ".join([problem["short_name"] for problem in data.problems]))
        prob_name = input("Choose problem from listed above: ")
        run_id = data.send_problem(prob_name, args.file)
    print("Run id:", run_id)
    print("Staus: ", end="", flush=True)
    print(data.get_status(run_id))


if __name__ == "__main__":
    main()
