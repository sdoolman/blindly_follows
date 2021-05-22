#!/usr/bin/python3
import random
import string
from progressbar import progressbar

LINE_LENGTH = 100
FILE_LENGTH = 50 * 1024 ** 2

def main():
    number_of_lines = FILE_LENGTH // LINE_LENGTH
    with open('some_text.txt', 'w') as f:
        for _ in progressbar(range(number_of_lines)):
            f.write(''.join(random.choices(string.ascii_letters + '. ', k=random.randrange(LINE_LENGTH))) + '\n')
    print('Done!')


if __name__ == '__main__':
    main()

