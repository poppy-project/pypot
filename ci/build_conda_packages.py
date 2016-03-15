#!/usr/bin/env python

"""
build_conda_packages.py creates conda packages for the specified recipe for all operating systems and python versions.

Usage:
anaconda login --user USER --password PASSWORD
python build_conda_packages.py ANACONDA_USER --destination-path conda_recipe/build/ --recipe-path conda_recipe/

where:
    conda build . is run at path
    and
    anaconda_user is the upload user

"""
import os
import shutil
from subprocess import *
import sys
import time

dists = ['linux-32', 'linux-64', 'osx-64', 'win-32', 'win-64']


def build_conda_packages(input_args):

    # Check if anaconda-client is installed
    try:
        Popen(["anaconda", "--help"], stdout=PIPE)
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            print(
                "You have to install anaconda-client (conda install anaconda-client)")
            sys.exit(1)
    if not input_args.recipe_path:
        input_args.recipe_path = '.'
    if not input_args.destination_path:
        input_args.destination_path = input_args.recipe_path

    path = input_args.destination_path
    env = os.environ.copy()
    retvals = []
    for CONDA_PY in ('27', '34', '35'):
        print('Clean build dirs')
        for dist_dir in dists:
            dist_dir = os.path.join(path, dist_dir)
            if os.path.exists(dist_dir):
                shutil.rmtree(dist_dir)
        env['CONDA_PY'] = CONDA_PY
        args = [
            'conda', 'build', input_args.recipe_path, '--no-anaconda-upload']
        print(args, "python %s " % CONDA_PY)
        proc = Popen(args,
                     cwd=path, stdout=PIPE,
                     stderr=STDOUT, env=env)
        out = []
        while proc.poll() is None:
            out.append(proc.stdout.readline().decode('utf-8').rstrip())
            if not input_args.quiet:
                print(out[-1])
            time.sleep(0.02)
        pos = len(out)
        out.extend([line.decode('utf-8') for line in proc.stdout.readlines()])
        if proc.wait():
            print('FAILED conda build %s for python %s' % (args, CONDA_PY))
            print(out)
            return proc.poll()
        print("conda build . (OK) for", CONDA_PY)
        files = []
        for line in out:
            if line.startswith('#') and 'anaconda' in line and 'upload' in line:
                f = line.split()[-1]
                if os.path.exists(f):
                    files.append(f)
        print('convert: ', files)
        for file in files:
            cmd = ['conda', 'convert', '--platform',
                   'all', file, '--output-dir', path]
            if input_args.force_convert:
                cmd.append('-f')
            print(cmd)
            proc = Popen(cmd,
                         stdout=PIPE, stderr=STDOUT, cwd=path, env=env)
            out = []
            while proc.poll() is None:
                out.append(proc.stdout.readline().decode('utf-8').rstrip())
                if not input_args.quiet:
                    print(out[-1])
                time.sleep(0.02)
            retvals.append(proc.poll())
            if retvals[-1] or out[-1].startswith('WARNING'):
                print(
                    'Failed on conda convert. You shoud sue the --force-convert argument.')
                print(out)
                sys.exit(1)
            else:
                print("Conversion ok for", file)
                for dist_dir in dists:
                    dist_dir = os.path.join(path, dist_dir)
                    for dist_file in os.listdir(dist_dir):
                        cmd = ['anaconda', 'upload', '--user', input_args.user,
                               os.path.abspath(
                                   os.path.join(dist_dir, dist_file))]
                        if input_args.force_upload:
                            cmd.append('--force')
                        proc = Popen(cmd, cwd='.')
                        if proc.wait():
                            print('Failed on anaconda upload')
                            sys.exit(proc.poll())
    return 1 if not len(retvals) else max(retvals)


def cli():
    import argparse
    parser = argparse.ArgumentParser(
        description='Generate conda packages for every Python version and platform. You should have login before with `anacconda login`')
    parser.add_argument('user',
                        help='anaconda user')
    parser.add_argument('-rp', '--recipe-path',
                        help='Path to the recipe. Default is `.`',
                        action='store')
    parser.add_argument('-dp', '--destination-path',
                        help='Path to the local destination of built conda packages. Default is same path as recipe-path argument',
                        action='store')
    parser.add_argument('-fc', '--force-convert',
                        help='Force conda convert, even if binaries are detected',
                        action='store_true')
    parser.add_argument('-fu', '--force-upload',
                        help='Force anaconda to upload packages, even if the same version already exist',
                        action='store_true')
    parser.add_argument('-q', '--quiet',
                        help='Mute conda build output',
                        action='store_true')

    return parser.parse_args()


def main():
    args = cli()
    sys.exit(build_conda_packages(args))

if __name__ == "__main__":
    main()
