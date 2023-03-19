import os
import re
import sys
import json
import queue
import threading
import urllib.parse
import urllib.request
from collections import OrderedDict

class WaybackMachineDownloader:

    VERSION = "2.3.1"

    def __init__(self, params):
        self.base_url = params.get('base_url')
        self.exact_url = params.get('exact_url')
        self.directory = params.get('directory')
        self.all_timestamps = params.get('all_timestamps')
        self.from_timestamp = int(params.get('from_timestamp', 0))
        self.to_timestamp = int(params.get('to_timestamp', 0))
        self.only_filter = params.get('only_filter')
        self.exclude_filter = params.get('exclude_filter')
        self.all = params.get('all')
        self.maximum_pages = int(params.get('maximum_pages', 100))
        self.threads_count = int(params.get('threads_count', 1))

    def backup_name(self):
        if '//' in self.base_url:
            return self.base_url.split('/')[2]
        else:
            return self.base_url

    def backup_path(self):
        if self.directory:
            if self.directory[-1] == '/':
                return self.directory
            else:
                return self.directory + '/'
        else:
            return 'websites/' + self.backup_name() + '/'

    def match_only_filter(self, file_url):
        if self.only_filter:
            only_filter_regex = self.only_filter
            if only_filter_regex:
                return bool(re.search(only_filter_regex, file_url))
            else:
                return self.only_filter.lower() in file_url.lower()
        else:
            return True

    def match_exclude_filter(self, file_url):
        if self.exclude_filter:
            exclude_filter_regex = self.exclude_filter
            if exclude_filter_regex:
                return bool(re.search(exclude_filter_regex, file_url))
            else:
                return self.exclude_filter.lower() in file_url.lower()
        else:
            return False

    def get_file_list_curated(self):
        file_list_curated = {}
        for file_timestamp, file_url in self.get_all_snapshots_to_consider():
            if '/' not in file_url:
                continue
            file_id = '/'.join(file_url.split('/')[3:])
            file_id = urllib.unquote(file_id)
            file_id = file_id.encode('utf-8', 'ignore').decode('utf-8') if file_id != "" else file_id
            if file_id is None:
                print(f"Malformed file url, ignoring: {file_url}")
            else:
                if self.match_exclude_filter(file_url):
                    print(f"File url matches exclude filter, ignoring: {file_url}")
                elif not self.match_only_filter(file_url):
                    print(f"File url doesn't match only filter, ignoring: {file_url}")
                elif file_id in file_list_curated:
                    if not file_list_curated[file_id]['timestamp'] > file_timestamp:
                        file_list_curated[file_id] = {'file_url': file_url, 'timestamp': file_timestamp}
                else:
                    file_list_curated[file_id] = {'file_url': file_url, 'timestamp': file_timestamp}
        return file_list_curated

    from urllib.parse import unquote

    def get_file_list_all_timestamps(self):
        file_list_curated = {}
        for file_timestamp, file_url in self.get_all_snapshots_to_consider():
            if '/' not in file_url:
                continue
            file_id = '/'.join(file_url.split('/')[3:])
            file_id_and_timestamp = '/'.join([file_timestamp, file_id])
            file_id_and_timestamp = unquote(file_id_and_timestamp)
            file_id_and_timestamp = file_id_and_timestamp.encode('utf-8', 'ignore').decode('utf-8') if file_id_and_timestamp != "" else file_id_and_timestamp
            if file_id is None:
                print(f"Malformed file url, ignoring: {file_url}")
            else:
                if self.match_exclude_filter(file_url):
                    print(f"File url matches exclude filter, ignoring: {file_url}")
                elif not self.match_only_filter(file_url):
                    print(f"File url doesn't match only filter, ignoring: {file_url}")
                elif file_id_and_timestamp in file_list_curated:
                    if self.verbose:
                        print(f"Duplicate file and timestamp combo, ignoring: {file_id}")
                else:
                    file_list_curated[file_id_and_timestamp] = {'file_url': file_url, 'timestamp': file_timestamp}
        print(f"file_list_curated: {len(file_list_curated)}")
        return file_list_curated

    def get_file_list_by_timestamp(self):
        if self.all_timestamps:
            file_list_curated = self.get_file_list_all_timestamps()
            return [{**file_info, 'file_id': file_id_and_timestamp} for file_id_and_timestamp, file_info in file_list_curated.items()]
        else:
            file_list_curated = self.get_file_list_curated()
            file_list_curated = sorted(file_list_curated.items(), key=lambda x: x[1]['timestamp'], reverse=True)
            return [{**file_info, 'file_id': file_id} for file_id, file_info in file_list_curated]

    import json
    import sys
    import threading
    import time
    from pathlib import Path
    import shutil

    def list_files(self):
        orig_stdout = sys.stdout
        sys.stdout = sys.stderr
        files = self.get_file_list_by_timestamp()
        sys.stdout = orig_stdout
        print("[")
        for file in files[:-1]:
            print(json.dumps(file) + ",")
        print(json.dumps(files[-1]))
        print("]")

    def download_files(self):
        start_time = time.time()
        print(f"Downloading {self.base_url} to {self.backup_path} from Wayback Machine archives.")
        print()

        files = self.get_file_list_by_timestamp()
        if len(files) == 0:
            print("No files to download.")
            print("Possible reasons:")
            print("\t* Site is not in Wayback Machine Archive.")
            print("\t* From timestamp too much in the future." if self.from_timestamp and self.from_timestamp != 0 else "")
            print("\t* To timestamp too much in the past." if self.to_timestamp and self.to_timestamp != 0 else "")
            print("\t* Only filter too restrictive ({self.only_filter})" if self.only_filter else "")
            print("\t* Exclude filter too wide ({self.exclude_filter})" if self.exclude_filter else "")
            return

        print(f"{len(files)} files to download:")

        self.processed_file_count = 0
        self.threads_count = 1 if self.threads_count == 0 else self.threads_count
        threads = []
        for _ in range(self.threads_count):
            thread = threading.Thread(target=self.download_file_worker)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        end_time = time.time()
        print()
        print(f"Download completed in {round(end_time - start_time, 2)}s, saved in {self.backup_path} ({len(files)} files)")

    def structure_dir_path(self, dir_path):
        try:
            dir_path.mkdir(parents=True, exist_ok=False)
        except FileExistsError as e:
            file_already_existing = Path(str(e).split("File exists: ")[-1].strip("'"))
            file_already_existing_temporary = file_already_existing.with_suffix('.temp')
            file_already_existing_permanent = file_already_existing / 'index.html'
            shutil.move(str(file_already_existing), str(file_already_existing_temporary))
            file_already_existing.mkdir()
            shutil.move(str(file_already_existing_temporary), str(file_already_existing_permanent))
            print(f"{file_already_existing} -> {file_already_existing_permanent}")
            self.structure_dir_path(dir_path)

    import urllib.request
    from queue import Queue
    from threading import Lock

    def download_file(self, file_remote_info):
        current_encoding = "utf-8"
        file_url = file_remote_info["file_url"].encode(current_encoding).decode("utf-8")
        file_id = file_remote_info["file_id"]
        file_timestamp = file_remote_info["timestamp"]
        file_path_elements = file_id.split('/')

        if file_id == "":
            dir_path = self.backup_path
            file_path = self.backup_path / 'index.html'
        elif file_url[-1] == '/' or '.' not in file_path_elements[-1]:
            dir_path = self.backup_path.joinpath(*file_path_elements[:-1])
            file_path = dir_path / 'index.html'
        else:
            dir_path = self.backup_path.joinpath(*file_path_elements[:-1])
            file_path = self.backup_path.joinpath(*file_path_elements)

        if not file_path.exists():
            try:
                self.structure_dir_path(dir_path)
                with file_path.open("wb") as file:
                    try:
                        with urllib.request.urlopen(f"https://web.archive.org/web/{file_timestamp}id_/{file_url}") as uri:
                            file.write(uri.read())
                    except urllib.error.HTTPError as e:
                        print(f"{file_url} # {e}")
                        if self.all:
                            file.write(e.read())
                            print(f"{file_path} saved anyway.")
                    except Exception as e:
                        print(f"{file_url} # {e}")
            except Exception as e:
                print(f"{file_url} # {e}")
            finally:
                if not self.all and file_path.exists() and file_path.stat().st_size == 0:
                    file_path.unlink()
                    print(f"{file_path} was empty and was removed.")
        else:
            with self.semaphore:
                self.processed_file_count += 1
                print(f"{file_url} # {file_path} already exists. ({self.processed_file_count}/{len(self.get_file_list_by_timestamp())})")

    def download_file_worker(self):
        while True:
            try:
                file_remote_info = self.file_queue.get_nowait()
            except Exception:
                break
            self.download_file(file_remote_info)

    @property
    def file_queue(self):
        if not hasattr(self, "_file_queue"):
            self._file_queue = Queue()
            for file_info in self.get_file_list_by_timestamp():
                self._file_queue.put(file_info)
        return self._file_queue

    @property
    def file_list_by_timestamp(self):
        if not hasattr(self, "_file_list_by_timestamp"):
            self._file_list_by_timestamp = self.get_file_list_by_timestamp()
        return self._file_list_by_timestamp

    @property
    def semaphore(self):
        if not hasattr(self, "_semaphore"):
            self._semaphore = Lock()
        return self._semaphore

def main():
    params = {
        'base_url': 'https://example.com',
        'exact_url': None,
        'directory': None,
        'all_timestamps': False,
        'from_timestamp': 0,
        'to_timestamp': 0,
        'only_filter': None,
        'exclude_filter': None,
        'all': False,
        'maximum_pages': 100,
        'threads_count': 1,
    }

    downloader = WaybackMachineDownloader(params)
    # Execute the appropriate methods to list or download files

if __name__ == "__main__":
    main()
