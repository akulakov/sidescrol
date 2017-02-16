import board
from board import vpsize, sizex, sizey

def add_items(Item, B, Loc):
    stat1 = Item(B, ']', Loc(20,19), descr="An ugly skeleton statue with a thick wig and grotesquely long arms")

    for _ in range(10000):
        loc=B.level_random_loc()
        if loc[0]<(sizex-1) and loc[1]<(sizey-1):
            B.gen_viewport(loc)
            if B[loc] is board.blank:
                Item(B, '*', loc, descr="A simple white gem")
