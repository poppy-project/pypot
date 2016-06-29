#! /usr/bin/env python
import argparse
try:
    import xmlrpclib
except ImportError:
    import xmlrpc.client as xmlrpclib

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Get the last Pypi version of a python package')
    parser.add_argument('package',
                        type=str,
                        help='Python package to check version.')
    args = parser.parse_args()
    client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
    available = client.package_releases(args.package)
    if not available:
        print('0')
    else:
        print(available[0])

# TODO return packages filename with client.release_urls('package',version)
# for element in client.release_urls('package',version):
#     print element['filename']
