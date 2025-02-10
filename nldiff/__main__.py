# Copyright 2022 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys

import click
from pyverilog.vparser.parser import parse, ParseError


from .data import Netlist
from .error import UnsupportedNetlistError


def diff(first_nl: str, second_nl: str) -> bool:
    try:
        ast_1 = parse([first_nl])[0]
    except ParseError as e:
        print(f"Syntax error in the first netlist: {e}", file=sys.stderr)
        exit(os.EX_DATAERR)

    try:
        ast_2 = parse([second_nl])[0]
    except ParseError as e:
        print(f"Syntax error in the second netlist: {e}", file=sys.stderr)
        exit(os.EX_DATAERR)

    try:
        metadata_1 = Netlist(ast_1)
    except UnsupportedNetlistError as e:
        print(f"The first netlist is not supported: {e}")
        exit(os.EX_DATAERR)

    try:
        metadata_2 = Netlist(ast_2)
    except UnsupportedNetlistError as e:
        print(f"The second netlist is not supported: {e}")
        exit(os.EX_DATAERR)

    differences = metadata_1.diff(metadata_2)
    for difference in differences:
        print(difference)

    if len(differences):
        exit(1)
    else:
        exit(0)


@click.command()
@click.argument("first_nl")
@click.argument("second_nl")
def diff_cmd(first_nl, second_nl):
    diff(first_nl, second_nl)


if __name__ == "__main__":
    diff_cmd()
