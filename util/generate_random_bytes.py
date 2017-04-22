import sys
import argparse
import random

SETA = range(0x11,0x100)

def main():
    all = []
    for i in xrange(0, args.number):
        all.append(SETA.pop(random.randint(0, len(SETA)-1)))
    
    print '[' + ', '.join(['0x%02X' % x for x in all]) + ']'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='generates list of random bytes to use for a game')
    parser.add_argument('number', type=int, help='number of bytes to generate')
    args = parser.parse_args()
    print args
    sys.exit(main())
