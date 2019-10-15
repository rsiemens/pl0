class OP_CODE:
    LIT = "LIT"  # Load constant literal
    OPR = "OPR"  # Execute operation
    LOD = "LOD"  # Load variable
    STO = "STO"  # Store variable
    CAL = "CAL"  # Call procedure
    INT = "INT"  # Increment topstack register
    JMP = "JMP"  # Jump
    JPC = "JPC"  # Jump conditional


class OPERATION:
    RETURN = 0
    NEGATE = 1
    ADD = 2
    SUB = 3
    MULT = 4
    DIV = 5
    ODD = 6
    EQUAL = 8
    NOT_EQUAL = 9
    LESS = 10
    GREATER_EQUAL = 11
    GREATER = 12
    LESS_EQUAL = 13
    WRITE = 14
    DEBUG = 15
