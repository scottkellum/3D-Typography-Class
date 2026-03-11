from coldtype import *
from random import Random

names = ["bert", "anna rose", "zeh", "zak", "scott", "seth", "adam", "wendrich", "stephen", "jennifer", "kirstin", "benjamin", "alec"]

rndm = Random()
rndm.seed(1)
rndm.shuffle(names)

@animation(tl=len(names), bg=0)
def namer(f:Frame):
    return (StSt(names[f.i], "ObviouslyV", 200
        , wght=1
        , slnt=1
        , wdth=1
        , fit=f.a.r.w-100
        , case="upper")
        .f(1)
        .layer([7, lambda i, p: p.t(-i*60, 0)])
        .stack(11)
        .align(f.a.r))
