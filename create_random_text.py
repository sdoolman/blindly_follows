#!/usr/bin/python3
import random
import string
from sys import stdout

LINE_LENGTH = 100
FILE_LENGTH = 20 * 1024 ** 2

number_of_lines = FILE_LENGTH // LINE_LENGTH
with open('some_text.txt', 'w') as f:
    for i in range(number_of_lines):
        stdout.write(f'{i}/{number_of_lines - 1}\r')
        f.write(''.join(random.choices(string.ascii_letters + '. ', k=random.randrange(LINE_LENGTH))) + '\n')
        #f.write('a' * LINE_LENGTH)

stdout.flush()
print('Done!')
