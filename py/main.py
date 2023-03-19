#!/usr/bin/env python3

from wayback_machine_downloader import WaybackMachineDownloader
import argparse
import pprint

parser = argparse.ArgumentParser(description="Download an entire website from the Wayback Machine.",
                                 usage="wayback_machine_downloader http://example.com")
parser.add_argument("base_url", help="The base URL of the website to download", nargs="?")
parser.add_argument("-d", "--directory", type=str, help="Directory to save the downloaded files into. "
                                                        "Default is ./websites/ plus the domain name")
parser.add_argument("-s", "--all-timestamps", action="store_true",
                    help="Download all snapshots/timestamps for a given website")
parser.add_argument("-f", "--from", dest="from_timestamp", type=int,
                    help="Only files on or after timestamp supplied (e.g., 20060716231334)")
parser.add_argument("-t", "--to", dest="to_timestamp", type=int,
                    help="Only files on or before timestamp supplied (e.g., 20100916231334)")
parser.add_argument("-e", "--exact-url", action="store_true",
                    help="Download only the url provided and not the full site")
parser.add_argument("-o", "--only", dest="only_filter", type=str,
                    help="Restrict downloading to urls that match this filter "
                         "(use // notation for the filter to be treated as a regex)")
parser.add_argument("-x", "--exclude", dest="exclude_filter", type=str,
                    help="Skip downloading of urls that match this filter "
                         "(use // notation for the filter to be treated as a regex)")
parser.add_argument("-a", "--all", dest="all", action="store_true",
                    help="Expand downloading to error files (40x and 50x) and redirections (30x)")
parser.add_argument("-c", "--concurrency", dest="threads_count", type=int,
                    help="Number of multiple files to download at a time. "
                         "Default is one file at a time (e.g., 20)")
parser.add_argument("-p", "--maximum-snapshot", dest="maximum_pages", type=int,
                    help="Maximum snapshot pages to consider (Default is 100). "
                         "Count an average of 150,000 snapshots per page")
parser.add_argument("-l", "--list", action="store_true",
                    help="Only list file urls in a JSON format with the archived timestamps, "
                         "won't download anything")
parser.add_argument("-v", "--version", action="store_true", help="Display version")

args = parser.parse_args()

if args.base_url:
    options = vars(args)
    wayback_machine_downloader = WaybackMachineDownloader(options)
    if args.list:
        wayback_machine_downloader.list_files()
    else:
        wayback_machine_downloader.download_files()
elif args.version:
    print(WaybackMachineDownloader.VERSION)
else:
    print("You need to specify a website to backup. (e.g., http://example.com)")
    print("Run `wayback_machine_downloader --help` for more help.")
