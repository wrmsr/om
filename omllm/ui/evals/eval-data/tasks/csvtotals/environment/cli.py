import json
import sys

from totals import sum_amounts


##


def _main() -> None:
    with open(sys.argv[1]) as file:
        rows = [dict(zip(['category', 'amount'], line.strip().split(','))) for line in file.readlines()[1:]]
    print(json.dumps(sum_amounts(rows)))


if __name__ == '__main__':
    _main()
