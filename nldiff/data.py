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
from typing import Optional, List, Iterable, Union, Tuple, Dict
from enum import Enum
from collections import OrderedDict as ODC

from pyverilog.vparser.ast import (
    ModuleDef,
    Ioport,
    Parameter,
    Input,
    Output,
    Decl,
    IntConst,
    Wire,
    InstanceList,
    Source,
    PortArg,
)
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
from pyverilog.vparser.ast import Port as PortNode, Instance as InstanceNode

from .error import UnsupportedNetlistError


class Base(object):
    def __repr__(self) -> str:
        return str(self)


class Net(Base):
    def __init__(
        self,
        name: str,
        frm: int = 0,
        to: int = 0,
    ):
        self.name = name
        self.frm = frm
        self.to = to

    def width_expr(self) -> str:
        return f"[{self.frm}:{self.to}]"

    def __str__(self) -> str:
        bus_expr = ""
        if self.frm != 0 or self.to != 0:
            bus_expr = f" {self.width_expr()}"
        return f"<{self.__class__.__qualname__} {self.name}{bus_expr}>"


class Port(Net):
    class Polarity(Enum):
        unknown = 0
        output = 1
        input = 2

    def __init__(
        self,
        name: str,
        frm: int = 0,
        to: int = 0,
        polarity: Optional["Port.Polarity"] = None,
    ):
        super().__init__(name, frm, to)
        if polarity is None:
            polarity = Port.Polarity.unknown
        self.polarity: "Port.Polarity" = polarity

    def __str__(self) -> str:
        bus_expr = ""
        if self.frm != 0 or self.to != 0:
            bus_expr = f" {self.width_expr()}"
        return f"<{self.__class__.__qualname__} {self.polarity.name} {self.name}{bus_expr}>"


class Instance(Base):
    def __init__(self, name: str, module: str, hooks: Dict[str, Tuple[str, str]]):
        self.name = name
        self.module = module
        self.hooks = hooks

    def __str__(self):
        return f"<{self.__class__.__qualname__} {self.name}, Ports: ({self.module}) {', '.join([str(hook) for hook in self.hooks.values()])}>"


class Netlist(Base):
    def __init__(self, ast: Source):
        description = ast.description
        module_def: Optional[ModuleDef] = None
        for definition in description.definitions:
            if type(definition) == ModuleDef:
                if module_def is None:
                    module_def = definition
                else:
                    raise UnsupportedNetlistError("More than one module found")
        if module_def is None:
            raise UnsupportedNetlistError("No module found")

        self.name: str = module_def.name
        self.ports: Dict[str, Port] = ODC()
        self.nets: Dict[str, Net] = ODC()
        self.instances: Dict[str, Instance] = ODC()

        declared_ports: Iterable[Union[PortNode, Ioport]] = module_def.portlist.ports
        for port in declared_ports:
            kwargs = {}

            if type(port) == Ioport:
                raise UnsupportedNetlistError(
                    "Port polarities and widths must not be declared at the top level"
                )
            else:
                kwargs["name"] = port.name

            port_object = Port(**kwargs)
            self.ports[port_object.name] = port_object

        generator = ASTCodeGenerator()
        for item in module_def.items:
            if type(item) == Decl:
                if len(item.list) != 1:
                    raise UnsupportedNetlistError(
                        "Declarations must consist of exactly one item"
                    )

                declaration = item.list[0]

                if type(declaration) == Parameter:
                    raise UnsupportedNetlistError("Parameters are not supported")
                elif type(declaration) in [Input, Output]:
                    name = declaration.name
                    port = self.ports[name]
                    if port is None:
                        raise Exception(f"Unknown port {name}")
                    if declaration.width is not None:
                        if type(declaration.width.msb) != IntConst:
                            raise UnsupportedNetlistError(
                                "Widths must be expressed in integers"
                            )
                        if type(declaration.width.lsb) != IntConst:
                            raise UnsupportedNetlistError(
                                "Widths must be expressed in integers"
                            )
                        port.frm = declaration.width.msb.value
                        port.to = declaration.width.lsb.value
                    if type(declaration) == Input:
                        port.polarity = Port.Polarity.input
                    elif type(declaration) == Output:
                        port.polarity = Port.Polarity.output
                elif type(declaration) in [Wire]:
                    name = declaration.name
                    frm = 0
                    to = 0
                    if declaration.width is not None:
                        if type(declaration.width.msb) != IntConst:
                            raise UnsupportedNetlistError(
                                "Widths must be expressed in integers"
                            )
                        if type(declaration.width.lsb) != IntConst:
                            raise UnsupportedNetlistError(
                                "Widths must be expressed in integers"
                            )
                        frm = declaration.width.msb.value
                        to = declaration.width.lsb.value
                    self.nets[name] = Net(name, frm, to)
            elif type(item) == InstanceList:
                if item.parameterlist is not None and len(item.parameterlist) != 0:
                    raise UnsupportedNetlistError("Parameters are not supported")
                if len(item.instances) > 1:
                    raise UnsupportedNetlistError(
                        "Only one instance may be declared in a single statement"
                    )
                instance: InstanceNode = item.instances[0]
                name = instance.name
                ports: Iterable[PortArg] = instance.portlist
                hooks = ODC()
                for port in ports:
                    result = generator.visit(port.argname)
                    hooks[port.portname] = (port.portname, result)
                self.instances[name] = Instance(name, item.module, hooks)

    def diff(lhs, rhs: "Netlist") -> List[str]:
        differences = []
        if lhs.name != rhs.name:
            differences.append(f"Name mismatch: {lhs.name} vs. {rhs.name}")

        # Ports
        rhs_ports = rhs.ports.copy()
        for id, port in lhs.ports.items():
            vs = rhs_ports.get(id)
            if vs is None:
                differences.append(f"Port {id} does not exist in the second netlist")
                continue
            if port.polarity != vs.polarity:
                differences.append(
                    f"Port {id} is an {port.polarity.name} in the first netlist but an {vs.polarity.name} in the second netlist"
                )
            if port.frm != vs.frm or port.to != vs.to:
                differences.append(
                    f"Port {id} is {port.width_expr()} in the first netlist but an {vs.width_expr} in the second netlist"
                )
            del rhs_ports[id]

        for id in rhs_ports.keys():
            differences.append(f"Port {id} does not exist in the first netlist")

        # Nets
        rhs_nets = rhs.nets.copy()
        for id, net in lhs.nets.items():
            vs = rhs_nets.get(id)
            if vs is None:
                differences.append(f"Net {id} does not exist in the second netlist")
                continue
            if net.frm != vs.frm or net.to != vs.to:
                differences.append(
                    f"Net {id} is {net.width_expr()} in the first netlist but an {vs.width_expr} in the second netlist"
                )
            del rhs_nets[id]

        for id in rhs_nets.keys():
            differences.append(f"Net {id} does not exist in the first netlist")

        # Instances
        rhs_instances = rhs.instances.copy()
        for id, instance in lhs.instances.items():
            vs = rhs_instances.get(id)
            if vs is None:
                differences.append(
                    f"Instance {id} does not exist in the second netlist"
                )
                continue

            if instance.module != vs.module:
                differences.append(
                    f"Instance {id} is of type {instance.module} in the first netlist but an {vs.module} in the second netlist"
                )

            rhs_hooks = vs.hooks.copy()
            for hid, hook in instance.hooks.items():
                hvs = rhs_hooks.get(hid)
                if hvs is None:
                    differences.append(
                        f"Instance {id}'s {hid} port exists in the first netlist but not the second"
                    )
                    continue
                _, ptr = hook
                _, rhs_ptr = hvs
                if ptr != rhs_ptr:
                    differences.append(
                        f"Instance {id}'s {hid} port is hooked to {ptr} in the first netlist but {rhs_ptr} in the second"
                    )

                del rhs_hooks[hid]

            for hid in rhs_hooks.keys():
                differences.append(
                    f"Instance {id}'s port {hid} is not present in the first netlist"
                )

            del rhs_instances[id]

        for id in rhs_instances.keys():
            differences.append(f"Instance {id} does not exist in the first netlist")

        return differences

    def __str__(self) -> str:
        return f"<Netlist {self.name}>"
