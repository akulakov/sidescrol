import board
from board import vpsize, sizex, sizey

def add_items(Item, B, Loc):
    stat1 = Item(B, ']', B.placeable_loc_at_vp((0,0)), descr="An ugly skeleton statue with a thick wig and grotesquely long arms")

    for _ in range(1000):
        loc=B.viewport(B.level_random_loc())
        if loc[0]<(sizex-1) and loc[1]<(sizey-1):
            B.gen_viewport(loc)
            if B[loc] is board.blank:
                try:
                    x = B.placeable_loc_at_vp(loc)
                    if not x: continue
                    Item(B, '*', x, descr="A simple white gem")
                except Exception as e:
                    print("x", x)
                    raise e
