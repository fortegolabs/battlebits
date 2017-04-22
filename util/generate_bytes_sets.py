import random


nibbles_hard = (0xA, 0xB, 0xC, 0xD, 0xE)
nibbles_medium = (0x3, 0x5, 0x6, 0x7, 0x9, 0xF)
nibbles_easy = (0x1, 0x2, 0x4, 0x8)

ALL_BYTES = {0: [],
             1: [],
             2: [],
             3: [],
             4: [],
             5: [],
             6: [],
             7: [],
             8: []}

all_sets = [(nibbles_easy, nibbles_easy),
            (nibbles_easy, nibbles_medium),
            (nibbles_medium, nibbles_easy),
            (nibbles_medium, nibbles_medium),
            (nibbles_easy, nibbles_hard),
            (nibbles_hard, nibbles_easy),
            (nibbles_medium, nibbles_hard),
            (nibbles_hard, nibbles_medium),
            (nibbles_hard, nibbles_hard)]

for i in xrange(0, len(all_sets)):
    for x in all_sets[i][0]:
        for y in all_sets[i][1]:
            ALL_BYTES[i].append(x + (y << 4))

# print the set of possible game bytes
out = 'ALL_BYTES = {'
for k in ALL_BYTES:
    out += '%d: [%s],\n    ' % (k, ','.join(['%d' % x for x in ALL_BYTES[k]]))
    
print out
