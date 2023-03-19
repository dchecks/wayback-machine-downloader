import json
import urllib.parse
import urllib.request

class ArchiveAPI:

    def get_raw_list_from_api(self, url, page_index):
        request_url = urllib.parse.urlunparse(('https', 'web.archive.org', '/cdx/search/xd', '', '', ''))
        params = [("output", "json"), ("url", url)]
        params += self.parameters_for_api(page_index)
        request_url = urllib.parse.urljoin(request_url, '?' + urllib.parse.urlencode(params))

        try:
            with urllib.request.urlopen(request_url) as response:
                content = response.read()
            json_data = json.loads(content)

            if json_data[0] == ["timestamp", "original"]:
                json_data.pop(0)

            return json_data
        except json.JSONDecodeError:
            return []

    def parameters_for_api(self, page_index):
        parameters = [("fl", "timestamp,original"), ("collapse", "digest"), ("gzip", "false")]

        if not self.all:
            parameters.append(("filter", "statuscode:200"))

        if self.from_timestamp and self.from_timestamp != 0:
            parameters.append(("from", str(self.from_timestamp)))

        if self.to_timestamp and self.to_timestamp != 0:
            parameters.append(("to", str(self.to_timestamp)))

        if page_index:
            parameters.append(("page", page_index))

        return parameters
