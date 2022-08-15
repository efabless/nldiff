module netlist_one (
    input a,
    b
);
    input a;
    output b;
    invX1 z(.a(a), .b(b));
endmodule