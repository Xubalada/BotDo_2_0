import numpy as np

a = [
    [(1,1,1),(1,1,1),(1,1,1),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)],
    [(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)],
    [(0,0,0),(0,0,0),(0,0,0),(1,1,1),(0,0,0),(0,0,0),(0,0,0),(0,0,0)],
    [(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)],
    [(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)]
]
print([x+y for x,y in a])
