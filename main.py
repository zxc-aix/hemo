import os
import json
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


RecordTemplate = {  # Тут подгоним темплейт потом, когда будет известна рег.карта
    # "id": None,
    # "comment": None,
    # "laser": None,
    "servo_angle": None,
    "frames" : None,
    "flat_auto_wnd" : None,
    "flatten_strength": None,
}

class Record:
    record = RecordTemplate.copy()

    def __init__(self, Raw: Path, Data: list, date: str) -> None:
        self.record["raw_name"] = str(Raw)
        self.record["date"] = date  # add full date
        self.record["data"] = Data  # add automatic data fill [[value, value],...]

    def save(self, filename: str) -> None:
        with open(filename, 'w') as f:
            json.dump(self.record, f)

class CustomEventHandler(FileSystemEventHandler):
    def __init__(self, path_save: str):
        self.path_save = Path(path_save)

    def on_created(self, event):
        if not event.is_directory: 
            file_path = Path(event.src_path)
            print(f"New file detected: {file_path}")
            self.process_new_file(file_path)

    def getData(self, file_path: Path):
        try:
            with file_path.open() as file:
                values = []
                configs = {}

                for _ in range(2):
                    line = file.readline().strip()
                    if line.startswith("#exp_cfg="):
                        configs.update(json.loads(line[len("#exp_cfg="):]))
                    elif line.startswith("#proc_cfg="):
                        configs.update(json.loads(line[len("#proc_cfg="):]))

                for line in file:
                    parts = map(float, line.strip().split())
                    values.append(list(parts))

                return values, configs

        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return [], {}

    def process_new_file(self, file_path: Path):
        data, configs = self.getData(file_path)
        dtime = time.ctime(file_path.stat().st_birthtime)
        record = Record(file_path, data, dtime)

        # update record with values from configs
        for key in RecordTemplate:
            if key in configs:
                record.record[key] = configs[key]

        json_filename = self.path_save / f"{file_path.stem}.json"
        record.save(json_filename)
        print(f"Saved record to {json_filename}")

if __name__ == "__main__":
    path = input("Enter path to monitor: ")  # full path to monitor
    path_save = input("Enter path to save: ")  # path to save

    event_handler = CustomEventHandler(path_save)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    print(f"Monitoring directory: {path}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
