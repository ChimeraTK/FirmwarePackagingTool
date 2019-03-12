#!/usr/bin/python3

import logging
import os
import shutil
import argparse
import pathlib
import re


package_params_template = [
    ("Section", "non-free"),
    # ("Architecture", "all"),
    ("Maintainer", "DESY"),
    ("Priority", "optional"),
]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FPGA firmware packager')
    parser.add_argument('--name', help='Target package name')
    parser.add_argument('--version', help='Package version rXXXX', required=False)
    parser.add_argument('--build', help='Build number', required=False)
    parser.add_argument('--dest', help='Destination of files in package', default='/usr/share/firmware')
    parser.add_argument('--param', '-p', nargs=2, action='append', help='Parameter for option file')
    parser.add_argument('files', nargs='+', help='Files to include in the package')

    args = parser.parse_args()
    name = args.name

    if args.version is None:
        print(args.files[0])
        folder = pathlib.Path(args.files[0]).parts[-2]
        print(folder)
        version = int(re.match(r'r(\d+)-b\d+', folder).group(1))
    else:
        version = args.version

    if args.build is None:
        folder = pathlib.Path(args.files[0]).parts[-2]
        build = int(re.match(r'r\d+-b(\d+)', folder).group(1))
    else:
        build = args.build

    print(version, build)
    tmp_folder_path = pathlib.Path('/tmp/fwpackager/{}-r{}'.format(name, version))
    dest_path = pathlib.Path('/tmp/fwpackager/{}-r{}'.format(name, version)) / pathlib.Path(args.dest).relative_to('/')
    tmp_folder_path.mkdir(parents=True, exist_ok=True)
    dest_path.mkdir(parents=True, exist_ok=True)
    print(dest_path)
    (tmp_folder_path / dest_path).mkdir(exist_ok=True)
    (tmp_folder_path / "DEBIAN").mkdir(exist_ok=True)

    for file in args.files:
        print(file)
        file_path = pathlib.Path(file)
        shutil.copy(str(file_path), str(dest_path))
        ext = file_path.suffix
        filename = file_path.stem[:file_path.stem.rfind('_')]  # file name with _rXXXX part removed
        try:
            (dest_path / '{}{}'.format(filename, ext)).symlink_to((dest_path / file_path.name).relative_to(dest_path))
        except FileExistsError:
            logging.warning("Symlink {} file exists".format(str(dest_path / '{}{}'.format(filename, ext))))
        logging.info('Processed file {}'.format(str(filename)))

    # create CONTROL file
    package_params = []
    package_params.append( ("Package", '{}-r{}'.format(name, version)))
    package_params.append( ("Version", '{}.{}'.format(version, build)))
    package_params.append( ("Architecture", "all") )
    package_params.append( ("Source", name) )
    package_params.append( ("Standards-Version", '{}.{}'.format(version, build) ))
    package_params.append( ("Provides", name))
    package_params.append( ("Confilicts", name))
    package_params.append( ("Description", 'Firmware for {}'.format(name)))
    package_params += package_params_template

    # add params from config file
    if args.param is not None:
        for pair in args.param:
            package_params.append((pair[0], pair[1]))

    with open(str(tmp_folder_path / "DEBIAN/control"), "w") as control_file:
        control_file.writelines("{}: {}\r\n".format(k, v) for (k, v) in package_params)

    logging.info("Building deb package:")
    os.system("dpkg-deb --build {} ./{}".format(str(tmp_folder_path), '{}-r{}.deb'.format(name, version)))
    ##fix \|/
    # subprocess.call(
    #     ["dpkg-deb",
    #      "--build {}".format(str(tmp_folder_path)),
    #      "./{}".format('{}-r{}.deb'.format(name, version))])

    logging.info("Removing temp directory")
    shutil.rmtree("/tmp/fwpackager")
