Here’s a breakdown of **five common ways to calculate the Fibonacci sequence**, ranging from the naive to the highly efficient, each with an explanation, pros and cons, and practical use cases.

---

## 1. **Recursive (Naive)**

### Code (Python)

```python
def fib_recursive(n):
    if n <= 1:
        return n
    return fib_recursive(n - 1) + fib_recursive(n - 2)
```

### Strengths

* **Simple and elegant**.
* Easy to understand for educational purposes.

### Weaknesses

* **Exponential time complexity**: `O(2^n)` due to redundant calculations.
* Deep recursion can cause **stack overflow** for large `n`.

### When to Use

* Teaching recursion and base cases.
* Exploring tree recursion and call stack behavior.
* *Never* in performance-sensitive situations.

---

## 2. **Memoization (Top-Down Dynamic Programming)**

### Code

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib_memo(n):

    if n <= 1:
        return n
    return fib_memo(n - 1) + fib_memo(n - 2)
```

### Strengths

* **Drastically improves performance** to `O(n)`.
* Retains clarity and recursive structure.

### Weaknesses

* Still uses recursion and can hit **recursion depth limits** in some languages.
* Slight **memory overhead** due to caching.

### When to Use

* When recursion is preferred but performance is important.
* For problems that benefit from **memoized recursion patterns**.

---

## 3. **Bottom-Up Iterative (Tabulation)**

### Code

```python
def fib_iterative(n):
    if n <= 1:
        return n
    prev, curr = 0, 1
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr
    return curr
```

### Strengths

* **Time complexity**: `O(n)`
* **Space complexity**: `O(1)`
* No recursion; works for large `n`.

### Weaknesses

* Slightly less elegant than recursion.
* Requires understanding of iterative patterns.

### When to Use

* In production code where **efficiency matters**.
* On embedded systems or environments with **limited memory**.

---

## 4. **Matrix Exponentiation**

### Code

```python
def fib_matrix(n):
    def multiply(F, M):
        x = F[0][0]*M[0][0] + F[0][1]*M[1][0]
        y = F[0][0]*M[0][1] + F[0][1]*M[1][1]
        z = F[1][0]*M[0][0] + F[1][1]*M[1][0]
        w = F[1][0]*M[0][1] + F[1][1]*M[1][1]
        return [[x, y], [z, w]]

    def power(F, n):
        result = [[1, 0], [0, 1]]
        while n > 0:
            if n % 2 == 1:
                result = multiply(result, F)
            F = multiply(F, F)
            n //= 2
        return result

    if n == 0:
        return 0
    base = [[1, 1], [1, 0]]
    result = power(base, n - 1)
    return result[0][0]
```

### Strengths

* **Time complexity**: `O(log n)`
* Elegant use of **exponentiation by squaring**.

### Weaknesses

* More **complex** to understand and implement.
* Not suitable for people new to linear algebra or recursion.

### When to Use

* When performance for **very large `n`** matters.
* In algorithm competitions or **systems-level** code.

---

## 5. **Closed-Form Expression (Binet’s Formula)**

### Code

```python
import math

def fib_closed_form(n):
    sqrt_5 = math.sqrt(5)
    phi = (1 + sqrt_5) / 2
    return round((phi ** n) / sqrt_5)
```

### Strengths

* **Constant time**: `O(1)`
* Very short and elegant.

### Weaknesses

* **Floating point errors** for large `n` (> 70).
* Depends on `math` functions, so precision is limited.

### When to Use

* For small `n` where **speed is critical**.
* In mathematical derivations or quick approximations.

---

## Summary Table

| Method                | Time Complexity | Space Complexity | Pros                    | Cons                           | Best Use Case                         |
| --------------------- | --------------- | ---------------- | ----------------------- | ------------------------------ | ------------------------------------- |
| Recursive (Naive)     | O(2^n)          | O(n)             | Simple, educational     | Extremely slow, stack overflow | Teaching recursion                    |
| Memoized Recursion    | O(n)            | O(n)             | Fast, retains recursion | Memory usage, recursion depth  | Fast prototyping, interviews          |
| Iterative             | O(n)            | O(1)             | Fast, memory efficient  | Less elegant                   | Production code, constrained devices  |
| Matrix Exponentiation | O(log n)        | O(1)             | Extremely fast          | Complex, hard to debug         | Large `n`, algorithm contests         |
| Closed-Form           | O(1)            | O(1)             | Fastest, very short     | Inaccurate for large `n`       | Quick approximations, math-heavy code |

---

Let me know if you'd like this turned into an article draft, code notebook, or embedded in your Obsidian vault.

