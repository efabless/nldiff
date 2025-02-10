<h1 align="center">🔍 nldiff (ALPHA)</h1>
<p align="center">
    <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License: Apache 2.0"/></a>
    <img src="https://github.com/efabless/nldiff/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI Status" />
    <a href="https://invite.skywater.tools"><img src="https://img.shields.io/badge/Community-Open%20Source%20Silicon-ff69b4?logo=slack" alt="Invite to the Open Source Silicon Slack"/></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style: Black"/></a>
</p>

<p align="center">A simple utility using Pyverilog that lists the differences between two netlists.</p>

# Requirements
* Python 3.8+ with PIP
* IcarusVerilog

# Installation
```sh
python3 -m pip install --upgrade --no-cache-dir nldiff
```

# Usage
```sh
nldiff <first netlist> <second netlist>
```

# Limitations
The tool is designed to operate on netlists coming out of OpenROAD and Yosys. In the interest of expedience, these limitations currently exist:

* Port polarity and widths must be declared inside the module: the module's port argument list must only have the port names.
* Only exactly one netlist allowed per file (flat netlist.)
* Each instance declaration statement must declare exactly one instance: arrays of instances are not allowed and more than one instance in a declaration statement are not allowed.
* Multi-dimensional nets and ports are not supported.

While the previous ones may be addressed in the future, the following will assuredly not:
* Parameters are not supported.
    * `wire`, `input` and `output` widths must be expressed in the form of integer constants and not expressions.
* Assign statements and procedural blocks are not supported.

# License
The Apache License, version 2.0. See 'License'.

