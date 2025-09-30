"""Calculator app

Usage:
    python calculator.py add 2 3
    python calculator.py mul 4 5
"""
from __future__ import annotations
import argparse
from typing import List


def add(nums: List[float]) -> float:
    return sum(nums)


def sub(nums: List[float]) -> float:
    if not nums:
        return 0.0
    res = nums[0]
    for n in nums[1:]:
        res -= n
    return res


def mul(nums: List[float]) -> float:
    res = 1.0
    for n in nums:
        res *= n
    return res


def div(nums: List[float]) -> float:
    if not nums:
        raise ValueError("No operands")
    res = nums[0]
    for n in nums[1:]:
        if n == 0:
            raise ZeroDivisionError("division by zero")
        res /= n
    return res


def main() -> None:
    p = argparse.ArgumentParser(description="Simple Calculator app")
    p.add_argument("op", choices=["add", "sub", "mul", "div"], help="operation")
    p.add_argument("nums", nargs="+", help="numbers", type=float)
    args = p.parse_args()

    try:
        if args.op == "add":
            out = add(args.nums)
        elif args.op == "sub":
            out = sub(args.nums)
        elif args.op == "mul":
            out = mul(args.nums)
        else:
            out = div(args.nums)
    except Exception as e:
        print("Error:", e)
    else:
        print(out)


if __name__ == "__main__":
    main()
