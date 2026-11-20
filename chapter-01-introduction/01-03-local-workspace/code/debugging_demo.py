"""Reproduce a counting defect with a small, local test case."""


def count_confirmed(items):
    return len(items)


def check_case(items):
    expected = sum(item["status"] == "confirmed" for item in items)
    observed = count_confirmed(items)
    return expected, observed


if __name__ == "__main__":
    items = [
        {"status": "confirmed"},
        {"status": "cancelled"},
        {"status": "confirmed"},
    ]
    expected, observed = check_case(items)
    print(f"Expected: {expected}. Observed: {observed}.")
    print("Pass" if expected == observed else "Mismatch")
