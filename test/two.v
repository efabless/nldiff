module netlist_two (
    a,
    b
);
    input a;
    output b;
    invX4 z(.a(a), .b(b));
endmodule