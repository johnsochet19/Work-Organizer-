# Section 1: Core Programming — Complete Study Guide

This guide takes you from zero to the point where you can start building an AI assistant.
Work through it in order. Each lesson has:

- **Concepts**: what to understand
- **Code**: examples to type out yourself (don't copy-paste; typing builds memory)
- **Common mistakes**: errors beginners hit
- **Exercises**: do them before moving on
- **Check yourself**: you should be able to answer these without looking

Total time: roughly **10–14 weeks at 1–2 hours a day**. Going slower is fine; skipping is not.

---

## Table of Contents

- [Part 0: Setting Up Your Computer](#part-0-setting-up-your-computer)
- [Part A: Python](#part-a-python)
  - [Lesson 1: Your First Program](#lesson-1-your-first-program)
  - [Lesson 2: Variables and Data Types](#lesson-2-variables-and-data-types)
  - [Lesson 3: Strings in Depth](#lesson-3-strings-in-depth)
  - [Lesson 4: Numbers and Math](#lesson-4-numbers-and-math)
  - [Lesson 5: Getting Input](#lesson-5-getting-input)
  - [Lesson 6: Conditions (if / elif / else)](#lesson-6-conditions-if--elif--else)
  - [Lesson 7: Loops](#lesson-7-loops)
  - [Lesson 8: Lists](#lesson-8-lists)
  - [Lesson 9: Dictionaries](#lesson-9-dictionaries)
  - [Lesson 10: Tuples and Sets](#lesson-10-tuples-and-sets)
  - [Lesson 11: Nested Data (How AI APIs Talk)](#lesson-11-nested-data-how-ai-apis-talk)
  - [Lesson 12: Comprehensions](#lesson-12-comprehensions)
  - [Lesson 13: Functions](#lesson-13-functions)
  - [Lesson 14: Type Hints and Docstrings](#lesson-14-type-hints-and-docstrings)
  - [Lesson 15: Errors and Exceptions](#lesson-15-errors-and-exceptions)
  - [Lesson 16: Files and JSON](#lesson-16-files-and-json)
  - [Lesson 17: Modules, Imports, and the Standard Library](#lesson-17-modules-imports-and-the-standard-library)
  - [Lesson 18: Virtual Environments and Packages](#lesson-18-virtual-environments-and-packages)
  - [Lesson 19: Environment Variables and Secrets](#lesson-19-environment-variables-and-secrets)
  - [Lesson 20: Calling Web APIs](#lesson-20-calling-web-apis)
  - [Lesson 21: Classes and Objects](#lesson-21-classes-and-objects)
  - [Lesson 22: Dataclasses and Pydantic](#lesson-22-dataclasses-and-pydantic)
  - [Lesson 23: Async Programming](#lesson-23-async-programming)
  - [Lesson 24: Logging, Testing, and Code Quality](#lesson-24-logging-testing-and-code-quality)
  - [Lesson 25: Debugging](#lesson-25-debugging)
- [Part B: Command Line and Git](#part-b-command-line-and-git)
- [Part C: JavaScript / TypeScript (Optional)](#part-c-javascript--typescript-optional)
- [Capstone Project: CLI Work Organizer](#capstone-project-cli-work-organizer)
- [Weekly Schedule](#weekly-schedule)
- [Final Checklist](#final-checklist)
- [Exercise Solutions](#exercise-solutions)

---

## Part 0: Setting Up Your Computer

### 0.1 Install Python

| OS | How |
|---|---|
| **Windows** | Download from python.org. **Tick "Add Python to PATH"** during install. |
| **macOS** | `brew install python` (install Homebrew first from brew.sh), or download from python.org. |
| **Linux** | Usually preinstalled. Otherwise `sudo apt install python3 python3-venv python3-pip`. |

Check it worked (open a terminal):

```bash
python --version
```

If that fails, try `python3 --version`. On macOS/Linux you'll often type `python3` instead of `python`.
You want **3.12 or newer**.

### 0.2 Install VS Code

1. Download from code.visualstudio.com.
2. Open it, go to Extensions (the four-squares icon), install:
   - **Python** (by Microsoft)
   - **Pylance** (usually comes with Python)
   - **Ruff** (formatting and catching mistakes)
3. Open a folder: File → Open Folder → make a folder called `learning-python`.

### 0.3 Two ways to run Python

**Interactive (REPL)** — good for quick experiments:
```bash
python
>>> 2 + 2
4
>>> exit()
```

**Script** — how real programs run. Create `hello.py`, then:
```bash
python hello.py
```

**Tip:** Keep a REPL open while you study. Whenever you wonder "what does this do?", try it there.

---

## Part A: Python

### Lesson 1: Your First Program

**Concepts**
- A program is a list of instructions run top to bottom.
- `print()` shows output.
- `#` starts a comment — Python ignores it; it's notes for humans.
- Python uses **indentation** (4 spaces) to group code, instead of `{ }`.

**Code**
```python
# hello.py
print("Hello, world!")
print("My name is John")
print("2 + 3 =", 2 + 3)   # print can take several things, separated by commas
print()                    # prints an empty line
print("Done", end="!\n")   # end= changes what goes at the end of the line
```

**Common mistakes**
- `Print("hi")` → `NameError`. Python is **case-sensitive**.
- `print("hi)` → `SyntaxError`. Every opening quote needs a closing quote.
- Mixing tabs and spaces → `IndentationError`. Let VS Code handle indentation.

**Exercises**
1. Print your name, age and city on three separate lines.
2. Print a box made of `*` characters, 5 wide and 3 tall.

**Check yourself**
- What's the difference between running code in the REPL and in a `.py` file?

---

### Lesson 2: Variables and Data Types

**Concepts**
A **variable** is a name pointing at a value. Python figures out the type itself.

| Type | Meaning | Example |
|---|---|---|
| `str` | Text | `"hello"`, `'hi'` |
| `int` | Whole number | `42`, `-7` |
| `float` | Decimal number | `3.14`, `0.5` |
| `bool` | True/False | `True`, `False` |
| `NoneType` | "Nothing / no value yet" | `None` |

**Code**
```python
name = "John"
age = 30
height = 1.82
is_student = False
manager = None

print(type(name))      # <class 'str'>
print(type(age))       # <class 'int'>

# Variables can be reassigned
age = age + 1
age += 1               # shortcut for the line above
print(age)             # 32

# Converting between types ("casting")
num_text = "25"
num = int(num_text)    # "25" -> 25
price = float("9.99")  # "9.99" -> 9.99
label = str(100)       # 100 -> "100"
print(bool(""), bool("x"), bool(0), bool(5))   # False True False True
```

**Naming rules**
- Letters, numbers, underscores; can't start with a number.
- Use `snake_case`: `due_date`, not `dueDate` or `DueDate`.
- Use meaningful names: `task_count`, not `x`.
- Constants (values that never change) in CAPS: `MAX_TASKS = 100`.

**Truthy / falsy** (important later): these count as `False` in conditions:
`False`, `None`, `0`, `0.0`, `""`, `[]`, `{}`, `set()`. Everything else is `True`.

**Common mistakes**
- `"5" + 5` → `TypeError`. You can't add text and numbers. Use `int("5") + 5` or `"5" + str(5)`.
- `int("3.5")` → `ValueError`. Use `float("3.5")` first.

**Exercises**
1. Create variables for a task: title, priority (1–3), hours estimate (decimal), done (bool). Print each with its type.
2. Convert `"42"` to a number, add 8, and print the result.

---

### Lesson 3: Strings in Depth

You'll spend a lot of time handling text (AI models read and write text), so learn strings well.

**Code**
```python
title = "  Finish Quarterly Report  "

# Cleaning
print(title.strip())          # "Finish Quarterly Report"
print(title.lower())          # lowercase
print(title.upper())          # UPPERCASE
print(title.strip().title())  # "Finish Quarterly Report"

# Searching
t = "Email the client about the invoice"
print("client" in t)          # True
print(t.startswith("Email"))  # True
print(t.find("invoice"))      # index where it starts, or -1
print(t.count("the"))         # 2

# Replacing and splitting
print(t.replace("client", "boss"))
words = t.split()             # ['Email', 'the', 'client', ...]
print(len(words))
csv = "work,urgent,email"
tags = csv.split(",")         # ['work', 'urgent', 'email']
print(" | ".join(tags))       # "work | urgent | email"

# Indexing and slicing  (positions start at 0)
s = "Python"
print(s[0])      # 'P'
print(s[-1])     # 'n'  (negative counts from the end)
print(s[0:3])    # 'Pyt' (start included, end excluded)
print(s[2:])     # 'thon'
print(s[::-1])   # 'nohtyP' (reversed)

# f-strings: the best way to build text
name, count = "John", 3
print(f"Hi {name}, you have {count} tasks.")
print(f"{3.14159:.2f}")       # '3.14' — 2 decimal places
print(f"{'left':<10}|")       # pad to 10 chars, left aligned
print(f"{count * 2 = }")      # 'count * 2 = 6'  — great for debugging

# Multi-line strings (you'll use these for AI prompts!)
prompt = """You are a helpful assistant.
Summarize the user's tasks for today.
Be brief."""
print(prompt)

# Escape characters
print("Line1\nLine2")         # \n = new line
print("Tab\there")            # \t = tab
print("She said \"hi\"")      # \" = a quote inside a string
```

**Key idea:** Strings are **immutable** — methods return a *new* string; they don't change the original.
```python
s = "hello"
s.upper()
print(s)         # still "hello"
s = s.upper()    # you must reassign
```

**Exercises**
1. Given `raw = "  buy MILK, eggs ,bread  "`, produce `["buy milk", "eggs", "bread"]`.
2. Ask for a task title and print it centred in a 40-character line of `=` (hint: `.center(40, "=")`).
3. Build a prompt string with an f-string that includes a user's name and a list of 3 tasks.

---

### Lesson 4: Numbers and Math

**Code**
```python
print(7 + 2)    # 9
print(7 - 2)    # 5
print(7 * 2)    # 14
print(7 / 2)    # 3.5  (always a float)
print(7 // 2)   # 3    (floor division — drops the decimal)
print(7 % 2)    # 1    (remainder — "modulo")
print(7 ** 2)   # 49   (power)

print(round(3.14159, 2))  # 3.14
print(abs(-5))            # 5
print(max(3, 9, 2), min(3, 9, 2))  # 9 2
print(sum([1, 2, 3]))     # 6

import math
print(math.sqrt(16), math.ceil(2.1), math.floor(2.9))  # 4.0 3 2

# Floats are not perfectly precise:
print(0.1 + 0.2)          # 0.30000000000000004
print(round(0.1 + 0.2, 2))  # 0.3
```

**Useful patterns**
- `n % 2 == 0` → n is even.
- `minutes // 60, minutes % 60` → hours and leftover minutes.

**Exercises**
1. Convert 135 minutes into "2h 15m".
2. Given hourly rate 45.50 and hours 7.25, print the pay with 2 decimals.

---

### Lesson 5: Getting Input

**Code**
```python
name = input("What's your name? ")       # input() ALWAYS returns a string
age = int(input("How old are you? "))    # convert if you need a number
print(f"Next year {name} will be {age + 1}.")
```

**Common mistake:** forgetting to convert. `input("Age: ") + 1` → `TypeError`.

**Exercise:** Ask for a task and how many minutes it takes; print "Task X will take Hh Mm".

---

### Lesson 6: Conditions (if / elif / else)

**Code**
```python
priority = 2

if priority == 1:
    print("Do it now")
elif priority == 2:
    print("Do it today")
else:
    print("Do it this week")

# Comparisons: ==  !=  <  >  <=  >=
# Logic: and, or, not
hours = 3
urgent = True
if urgent and hours < 4:
    print("Squeeze it in this morning")

if not urgent or hours > 8:
    print("Schedule it later")

# Checking membership
if "email" in "Email the client".lower():
    print("It's an email task")

# Checking for None
manager = None
if manager is None:
    print("No manager assigned")

# Truthiness shortcut
tasks = []
if not tasks:
    print("Nothing to do!")

# One-line conditional ("ternary")
status = "done" if hours == 0 else "pending"

# Chained comparison
if 1 <= priority <= 3:
    print("valid priority")
```

**match statement** (Python 3.10+) — clean way to handle commands, which you'll do a lot:
```python
command = "add"
match command:
    case "add":
        print("Adding a task")
    case "list" | "ls":
        print("Listing tasks")
    case "quit":
        print("Bye")
    case _:
        print("Unknown command")
```

**Common mistakes**
- `if x = 5:` → `SyntaxError`. Use `==` to compare; `=` assigns.
- Forgetting the colon `:` at the end of `if` lines.
- Use `is` only for `None`, `True`, `False`. Use `==` for everything else.

**Exercises**
1. Ask for a score 0–100 and print a letter grade (A ≥ 90, B ≥ 80, C ≥ 70, else F). Reject numbers outside 0–100.
2. Ask for a day name and print whether it's a weekday or weekend (accept any capitalisation).

---

### Lesson 7: Loops

**`for` loops** repeat for each item in something.
```python
for i in range(5):           # 0,1,2,3,4
    print(i)

for i in range(1, 11, 2):    # 1,3,5,7,9  (start, stop, step)
    print(i)

tasks = ["email", "gym", "report"]
for task in tasks:
    print("-", task)

# Need the position too? Use enumerate
for number, task in enumerate(tasks, start=1):
    print(f"{number}. {task}")

# Loop over two lists together: zip
hours = [1, 2, 3]
for task, h in zip(tasks, hours):
    print(f"{task}: {h}h")
```

**`while` loops** repeat while a condition is true.
```python
count = 3
while count > 0:
    print(count)
    count -= 1
print("Go!")

# The "main loop" pattern — every chat assistant uses this
while True:
    text = input("You: ")
    if text == "quit":
        break                  # leave the loop
    if text.strip() == "":
        continue               # skip to the next round
    print("Echo:", text)
```

**Common mistakes**
- Infinite loop: forgetting to change the condition in a `while` loop. Press **Ctrl+C** to stop.
- Changing a list while looping over it — loop over a copy: `for t in tasks[:]:`.

**Exercises**
1. Print the 7 times table (7 × 1 … 7 × 12).
2. Sum all numbers from 1 to 1000 that are divisible by 3 or 5.
3. Number-guessing game: `import random; secret = random.randint(1, 100)`. Tell the user "higher"/"lower" and count attempts.

---

### Lesson 8: Lists

A **list** is an ordered, changeable collection.

**Code**
```python
tasks = ["email", "gym", "report"]

# Access
print(tasks[0], tasks[-1], len(tasks))

# Add
tasks.append("groceries")          # to the end
tasks.insert(0, "coffee")          # at position 0
tasks.extend(["call mom", "read"]) # add several

# Remove
tasks.remove("gym")                # by value (first match)
last = tasks.pop()                 # remove & return last item
first = tasks.pop(0)               # remove & return item at index 0
del tasks[0]                       # delete by index

# Search
print("report" in tasks)
print(tasks.index("report"))       # position (error if missing)

# Sort
nums = [5, 2, 9, 1]
nums.sort()                        # changes the list in place
nums.sort(reverse=True)
new = sorted(nums)                 # returns a NEW sorted list
words = ["banana", "Apple", "cherry"]
words.sort(key=str.lower)          # sort ignoring case
words.sort(key=len)                # sort by length

# Slicing works like strings
print(nums[:2], nums[-2:])

# Copying — IMPORTANT
a = [1, 2, 3]
b = a          # b is the SAME list, not a copy!
b.append(4)
print(a)       # [1, 2, 3, 4]  — surprise!
c = a.copy()   # a real copy
```

**Exercises**
1. Start with an empty list. Let the user type tasks until they type `done`, then print them numbered and sorted alphabetically.
2. Given `[3, 7, 7, 2, 9, 2, 2]`, print the largest, smallest, average, and how many times `2` appears.

---

### Lesson 9: Dictionaries

A **dictionary** stores **key → value** pairs. This is the single most important structure for AI work: JSON from every API turns into dictionaries.

**Code**
```python
task = {
    "title": "Write report",
    "priority": 1,
    "done": False,
    "tags": ["work", "urgent"],
}

# Read
print(task["title"])
print(task.get("due_date"))               # None instead of crashing
print(task.get("due_date", "no date"))    # default value

# Add / change
task["due_date"] = "2026-11-10"
task["priority"] = 2
task.update({"done": True, "hours": 3})

# Remove
del task["hours"]
removed = task.pop("due_date", None)

# Loop
for key in task:
    print(key)
for key, value in task.items():
    print(f"{key}: {value}")
print(list(task.keys()), list(task.values()))

# Check a key exists
if "tags" in task:
    print("has tags")

# Counting pattern
words = "the cat and the hat".split()
counts = {}
for w in words:
    counts[w] = counts.get(w, 0) + 1
print(counts)   # {'the': 2, 'cat': 1, 'and': 1, 'hat': 1}
```

**Rules**
- Keys must be unique and unchangeable (strings and numbers are usual).
- `task["missing"]` → `KeyError`. Use `.get()` when unsure.

**Exercises**
1. Make a dictionary of 5 contacts: name → email. Let the user look up a name; print "not found" if missing.
2. Count how often each letter appears in a sentence (ignore spaces).

---

### Lesson 10: Tuples and Sets

**Tuples** — like lists but **can't be changed**. Good for fixed groups.
```python
point = (10, 20)
x, y = point            # "unpacking"
print(x, y)

def min_max(nums):
    return min(nums), max(nums)   # returns a tuple
low, high = min_max([4, 1, 9])
```

**Sets** — unordered, **no duplicates**, very fast `in` checks.
```python
tags = {"work", "urgent", "work"}
print(tags)                   # {'work', 'urgent'}
tags.add("email")
tags.discard("urgent")

a = {"work", "email"}
b = {"email", "home"}
print(a | b)   # union: all
print(a & b)   # intersection: in both
print(a - b)   # difference: in a not b

unique = list(set([1, 2, 2, 3, 3]))   # remove duplicates
```

**Exercise:** Two people's lists of free days — print the days both are free.

---

### Lesson 11: Nested Data (How AI APIs Talk)

Real API responses are dictionaries inside lists inside dictionaries. Practise reading them.

```python
response = {
    "id": "msg_123",
    "model": "some-model",
    "content": [
        {"type": "text", "text": "Here are your tasks."},
        {"type": "tool_use", "name": "get_calendar", "input": {"date": "2026-11-05"}},
    ],
    "usage": {"input_tokens": 120, "output_tokens": 45},
}

# Get the first text block
print(response["content"][0]["text"])

# Total tokens
usage = response["usage"]
print(usage["input_tokens"] + usage["output_tokens"])

# Find any tool calls
for block in response["content"]:
    if block["type"] == "tool_use":
        print("Model wants to call:", block["name"], "with", block["input"])
```

**Strategy for reading nested data:** go one level at a time and print as you go:
```python
print(type(response))                    # dict
print(response.keys())
print(type(response["content"]))         # list
print(response["content"][0].keys())
```

**Pretty-print big structures:**
```python
from pprint import pprint
pprint(response)
```

**Exercises**
1. Given a list of 5 task dicts (title, priority, done), print only the unfinished ones, highest priority first.
2. Given the `response` above, write code that collects **all** text blocks into one string.

---

### Lesson 12: Comprehensions

A short way to build lists/dicts/sets from loops. You'll see these everywhere.

```python
nums = [1, 2, 3, 4, 5, 6]

squares = [n * n for n in nums]                 # [1, 4, 9, ...]
evens   = [n for n in nums if n % 2 == 0]       # [2, 4, 6]
labels  = ["even" if n % 2 == 0 else "odd" for n in nums]

tasks = [
    {"title": "email", "done": True},
    {"title": "gym", "done": False},
]
todo_titles = [t["title"] for t in tasks if not t["done"]]   # ['gym']

# Dict comprehension
lengths = {t["title"]: len(t["title"]) for t in tasks}

# Set comprehension
first_letters = {t["title"][0] for t in tasks}

# any() / all() — very handy
print(any(t["done"] for t in tasks))   # True if at least one is done
print(all(t["done"] for t in tasks))   # True only if all are done
```

**Rule of thumb:** if a comprehension doesn't fit on one readable line, use a normal loop.

**Exercise:** From a list of words, make a dict of word → number of vowels, only for words longer than 3 letters.

---

### Lesson 13: Functions

Functions are named, reusable blocks of code. **In an AI assistant, each "tool" the AI can use is a function you write.**

**Code**
```python
def greet(name):
    """Return a greeting for name."""
    return f"Hello, {name}!"

message = greet("John")
print(message)

# Default values
def add_task(title, priority=3, done=False):
    return {"title": title, "priority": priority, "done": done}

add_task("gym")                       # uses defaults
add_task("report", priority=1)        # keyword argument — clearer
add_task(title="email", done=True)

# Return several values
def stats(nums):
    return min(nums), max(nums), sum(nums) / len(nums)
lo, hi, avg = stats([2, 4, 9])

# Functions without return give back None
def say(x):
    print(x)
result = say("hi")    # result is None
```

**`*args` and `**kwargs`** — accept any number of arguments:
```python
def total(*numbers):              # numbers is a tuple
    return sum(numbers)
total(1, 2, 3)

def make_task(title, **extra):    # extra is a dict
    return {"title": title, **extra}
make_task("gym", priority=1, tags=["health"])

# Unpacking when calling
args = {"title": "read", "priority": 2}
add_task(**args)    # same as add_task(title="read", priority=2)
```
That last line is exactly how you'll run the tool an AI asks for: the AI gives you a dict of arguments, and you call `tool_function(**arguments)`.

**Scope**
```python
count = 0
def increment():
    count = 1          # this is a NEW local variable, not the outer one
increment()
print(count)           # 0
```
Prefer passing values in and returning results out, instead of changing outside variables.

**Functions are values** — you can store them in a dict. This is the core trick behind AI tool calling:
```python
def get_weather(city):
    return f"Sunny in {city}"

def get_time(zone):
    return f"12:00 in {zone}"

TOOLS = {"get_weather": get_weather, "get_time": get_time}

# Pretend the AI responded with this:
tool_name = "get_weather"
tool_args = {"city": "Boston"}

result = TOOLS[tool_name](**tool_args)
print(result)   # Sunny in Boston
```

**Lambda** — tiny one-line function, mostly used for sorting:
```python
tasks.sort(key=lambda t: t["priority"])
```

**Common mistakes**
- Mutable default argument trap:
  ```python
  def add(item, items=[]):    # BAD — the same list is reused every call
      items.append(item)
      return items
  def add(item, items=None):  # GOOD
      if items is None:
          items = []
      items.append(item)
      return items
  ```
- Printing inside a function instead of returning — return values so other code can use them.

**Exercises**
1. Write `is_overdue(due_date_str, today_str)` that compares two `"YYYY-MM-DD"` strings and returns True/False. (Hint: these strings compare correctly with `<`.)
2. Write a calculator with functions `add`, `subtract`, `multiply`, `divide` stored in a dict, and a loop that reads input like `add 3 5`.
3. Write `summarize(tasks)` returning a dict: `{"total": ..., "done": ..., "pending": ...}`.

---

### Lesson 14: Type Hints and Docstrings

Type hints say what types a function expects and returns. Python doesn't enforce them, but editors and **AI frameworks read them** to describe your tools to the model.

```python
def add_task(title: str, priority: int = 3, tags: list[str] | None = None) -> dict:
    """Create a new task.

    Args:
        title: Short description of the task.
        priority: 1 (high) to 3 (low).
        tags: Optional labels like "work" or "home".

    Returns:
        A dictionary representing the task.
    """
    return {"title": title, "priority": priority, "tags": tags or []}
```

**Common hints**

| Hint | Meaning |
|---|---|
| `str`, `int`, `float`, `bool` | Basic types |
| `list[str]` | List of strings |
| `dict[str, int]` | Dict with string keys, int values |
| `tuple[int, int]` | Tuple of two ints |
| `str \| None` | A string or None |
| `Any` (from `typing`) | Anything |
| `Literal["low", "high"]` (from `typing`) | Only these exact values |

**Why docstrings matter for AI:** when you give a function to an AI as a tool, the docstring often *becomes* the description the AI reads to decide when to use it. A vague docstring means the AI uses your tool wrongly.

**Exercise:** Add full type hints and docstrings to every function from Lesson 13.

---

### Lesson 15: Errors and Exceptions

Programs that talk to the internet fail all the time (network down, bad API key, rate limits). You must handle errors gracefully.

**Reading an error (traceback)** — read from the **bottom up**:
```
Traceback (most recent call last):
  File "app.py", line 5, in <module>
    print(tasks[10])
IndexError: list index out of range
```
Bottom line = what went wrong. Line above = where.

**Common exceptions**

| Exception | Cause |
|---|---|
| `SyntaxError` | Code isn't valid Python |
| `NameError` | Using a variable that doesn't exist |
| `TypeError` | Wrong type (e.g. `"a" + 1`) |
| `ValueError` | Right type, bad value (`int("abc")`) |
| `KeyError` | Missing dict key |
| `IndexError` | List position doesn't exist |
| `FileNotFoundError` | File missing |
| `ZeroDivisionError` | Divided by zero |

**Handling them**
```python
try:
    n = int(input("Number: "))
    print(100 / n)
except ValueError:
    print("That's not a number.")
except ZeroDivisionError:
    print("Can't divide by zero.")
else:
    print("Worked fine.")        # runs only if no error
finally:
    print("This always runs.")   # cleanup goes here

# Capture the error message
try:
    {}["x"]
except KeyError as e:
    print("Missing key:", e)
```

**Raising your own errors**
```python
def set_priority(p: int) -> int:
    if p not in (1, 2, 3):
        raise ValueError(f"priority must be 1-3, got {p}")
    return p
```

**Custom exceptions**
```python
class TaskNotFoundError(Exception):
    pass

def find_task(tasks, title):
    for t in tasks:
        if t["title"] == title:
            return t
    raise TaskNotFoundError(title)
```

**Retry pattern** (you'll use this for AI API calls):
```python
import time

def call_with_retry(func, attempts=3):
    for i in range(attempts):
        try:
            return func()
        except ConnectionError:
            wait = 2 ** i               # 1s, 2s, 4s
            print(f"Failed, retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError("All retries failed")
```

**Rules**
- Catch **specific** exceptions. Never `except:` alone — it hides bugs (and even blocks Ctrl+C).
- Don't wrap huge blocks in `try`; wrap only the line that can fail.

**Exercises**
1. Write `safe_int(text, default=0)` that returns the int or the default.
2. Keep asking the user for a number until they enter a valid one.

---

### Lesson 16: Files and JSON

**Text files**
```python
# Write (creates or overwrites)
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("First line\n")
    f.write("Second line\n")

# Append
with open("notes.txt", "a", encoding="utf-8") as f:
    f.write("Another line\n")

# Read everything
with open("notes.txt", encoding="utf-8") as f:
    content = f.read()

# Read line by line
with open("notes.txt", encoding="utf-8") as f:
    for line in f:
        print(line.strip())
```
`with` automatically closes the file, even if an error happens. Always use it.

**pathlib** — the modern way to handle paths:
```python
from pathlib import Path

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
file = data_dir / "tasks.json"     # works on Windows and Mac/Linux

print(file.exists(), file.name, file.suffix)
file.write_text("hello", encoding="utf-8")
print(file.read_text(encoding="utf-8"))

for p in Path(".").glob("*.py"):   # list all .py files
    print(p)
```

**JSON** — the universal data format for APIs and AI:
```python
import json

tasks = [
    {"title": "email", "priority": 1, "done": False},
    {"title": "gym", "priority": 2, "done": True},
]

# Python -> JSON text
text = json.dumps(tasks, indent=2)
print(text)

# JSON text -> Python
back = json.loads(text)
print(back[0]["title"])

# Save to / load from a file
with open("tasks.json", "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=2)

with open("tasks.json", encoding="utf-8") as f:
    loaded = json.load(f)
```

**JSON vs Python**

| JSON | Python |
|---|---|
| object `{}` | dict |
| array `[]` | list |
| `"string"` | str |
| number | int / float |
| `true` / `false` | True / False |
| `null` | None |

Note: JSON can't store dates, sets or custom objects directly — convert them to strings/lists first.

**Load-or-create pattern** (used in the capstone):
```python
from pathlib import Path
import json

DATA_FILE = Path("tasks.json")

def load_tasks() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Warning: tasks.json is corrupted; starting fresh.")
        return []

def save_tasks(tasks: list[dict]) -> None:
    DATA_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
```

**CSV** (spreadsheets) — briefly:
```python
import csv
with open("tasks.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["title", "priority", "done"])
    writer.writeheader()
    writer.writerows(tasks)
```

**Exercises**
1. Write a journal program: each run asks for an entry and appends it with today's date to `journal.txt`.
2. Save a contacts dict to JSON, then load it in a separate run and print it.

---

### Lesson 17: Modules, Imports, and the Standard Library

**Splitting code into files.** Project layout:
```
organizer/
├── main.py
├── storage.py
└── tasks.py
```

```python
# storage.py
import json
from pathlib import Path

def load(path: Path) -> list:
    ...

# main.py
from storage import load          # import one function
import tasks                      # import the whole module
tasks.add_task(...)
```

**`if __name__ == "__main__":`** — code that only runs when the file is run directly, not when imported:
```python
def main():
    print("Running app")

if __name__ == "__main__":
    main()
```
Put this at the bottom of every script.

**Standard library highlights** (built in, no install needed)

| Module | Use | Example |
|---|---|---|
| `datetime` | Dates & times | see below |
| `pathlib` | File paths | `Path("a") / "b.txt"` |
| `json` | JSON | `json.loads(...)` |
| `os` | OS stuff, env vars | `os.getenv("API_KEY")` |
| `sys` | Interpreter info, args | `sys.argv` |
| `random` | Random values | `random.choice(list)` |
| `time` | Sleep, timing | `time.sleep(1)` |
| `logging` | Proper logs | Lesson 24 |
| `argparse` | Command-line arguments | capstone |
| `collections` | `Counter`, `defaultdict` | `Counter(words)` |
| `uuid` | Unique IDs | `str(uuid.uuid4())` |
| `re` | Regular expressions (patterns in text) | `re.findall(r"\d+", s)` |

**datetime in depth** (task apps live on dates):
```python
from datetime import datetime, date, timedelta

now = datetime.now()
today = date.today()
print(now.strftime("%Y-%m-%d %H:%M"))      # format -> '2026-11-04 14:30'
d = datetime.strptime("2026-11-10", "%Y-%m-%d").date()   # parse text -> date
print((d - today).days, "days left")
tomorrow = today + timedelta(days=1)
print(today.isoformat())                   # '2026-11-04' — good for JSON
print(date.fromisoformat("2026-12-25"))
print(today.strftime("%A"))                # weekday name
```

**Exercises**
1. Split your Lesson 13 calculator into `operations.py` and `main.py`.
2. Print how many days until New Year and what weekday it falls on.
3. Use `collections.Counter` to find the 3 most common words in a paragraph.

---

### Lesson 18: Virtual Environments and Packages

**Why:** Each project needs its own set of installed packages, so projects don't break each other.

**Create and use a virtual environment**
```bash
cd my-project
python -m venv .venv
```
Activate it:
```bash
# macOS / Linux
source .venv/bin/activate
```
```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```
Your prompt will show `(.venv)`. Now install packages:
```bash
pip install requests python-dotenv
```
Save your package list:
```bash
pip freeze > requirements.txt
```
Someone else (or future you) installs them with:
```bash
pip install -r requirements.txt
```
Leave the environment:
```bash
deactivate
```

**Modern alternative: `uv`** (much faster, recommended once you're comfortable):
```bash
pip install uv
```
```bash
uv init my-project
```
```bash
uv add requests
```
```bash
uv run main.py
```
`uv` manages the venv and a `pyproject.toml` file for you.

**In VS Code:** Ctrl+Shift+P → "Python: Select Interpreter" → pick the `.venv` one.

**Rules**
- Add `.venv/` to `.gitignore` — never commit it.
- Packages you'll use soon: `requests`, `httpx`, `python-dotenv`, `pydantic`, `pytest`, `ruff`, `rich` (pretty terminal output), and later `anthropic` / `openai`.

---

### Lesson 19: Environment Variables and Secrets

API keys are like passwords. If you put one in your code and push to GitHub, bots will find and abuse it within minutes.

**Create a `.env` file** (in the project folder):
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
WEATHER_API_KEY=abc123
```

**Add it to `.gitignore` immediately:**
```
.env
.venv/
__pycache__/
```

**Load it in Python:**
```python
import os
from dotenv import load_dotenv   # pip install python-dotenv

load_dotenv()                     # reads .env into environment variables
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to .env")
```

**Also commit a `.env.example`** with fake values, so others know which keys they need:
```
ANTHROPIC_API_KEY=your-key-here
```

**If you leak a key:** revoke/regenerate it immediately in the provider's dashboard. Deleting the commit is not enough.

---

### Lesson 20: Calling Web APIs

An **API** is a URL your program can request data from (or send data to).

**HTTP basics**

| Method | Meaning |
|---|---|
| `GET` | Read data |
| `POST` | Send/create data (AI chat calls use POST) |
| `PUT` / `PATCH` | Update |
| `DELETE` | Remove |

| Status code | Meaning |
|---|---|
| 200–299 | Success |
| 400 | You sent something wrong |
| 401 / 403 | Bad or missing key / not allowed |
| 404 | Not found |
| 429 | Too many requests (slow down, retry later) |
| 500–599 | Server's fault (retry later) |

**GET request with `requests`:**
```python
import requests

url = "https://api.github.com/repos/python/cpython"
response = requests.get(url, timeout=10)     # ALWAYS set a timeout
print(response.status_code)
response.raise_for_status()                   # raises an error on 4xx/5xx
data = response.json()                        # JSON -> dict
print(data["full_name"], data["stargazers_count"])
```

**Query parameters and headers:**
```python
response = requests.get(
    "https://api.github.com/search/repositories",
    params={"q": "todo app", "sort": "stars"},     # becomes ?q=todo+app&sort=stars
    headers={"Accept": "application/vnd.github+json"},
    timeout=10,
)
for repo in response.json()["items"][:5]:
    print(repo["full_name"])
```

**POST request with JSON body** — this is the exact shape of an AI API call:
```python
response = requests.post(
    "https://httpbin.org/post",          # a free test endpoint that echoes back
    json={"title": "gym", "priority": 2},
    headers={"Authorization": "Bearer YOUR_KEY"},
    timeout=10,
)
print(response.json()["json"])
```

**Handling failures properly:**
```python
import requests

def fetch_json(url: str) -> dict | None:
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.HTTPError as e:
        print("HTTP error:", e.response.status_code)
    except requests.exceptions.RequestException as e:
        print("Network problem:", e)
    return None
```

**Free APIs to practise with (no key needed)**
- `https://api.github.com/users/<username>`
- `https://httpbin.org` (test anything)
- `https://api.open-meteo.com/v1/forecast?latitude=40.7&longitude=-74&current_weather=true` (weather)
- `https://official-joke-api.appspot.com/random_joke`

**Exercises**
1. Print the current temperature for your city using Open-Meteo.
2. Ask for a GitHub username and print their name, public repo count, and 5 most recently updated repos.
3. Add retry with exponential backoff for 429 and 5xx responses.

---

### Lesson 21: Classes and Objects

A **class** bundles data and the functions that work on it. Most libraries you'll use (including AI SDKs) are built from classes, so you need to read and write them.

```python
class Task:
    def __init__(self, title: str, priority: int = 3):
        self.title = title          # attributes: data stored on each object
        self.priority = priority
        self.done = False

    def complete(self) -> None:     # methods: functions that belong to the object
        self.done = True

    def __str__(self) -> str:       # how it looks when printed
        mark = "x" if self.done else " "
        return f"[{mark}] {self.title} (p{self.priority})"

t = Task("Write report", 1)          # create an object (an "instance")
t.complete()
print(t)                             # [x] Write report (p1)
```

**`self`** is the object the method is being called on. `t.complete()` is really `Task.complete(t)`.

**A manager class:**
```python
class TaskManager:
    def __init__(self):
        self.tasks: list[Task] = []

    def add(self, title: str, priority: int = 3) -> Task:
        task = Task(title, priority)
        self.tasks.append(task)
        return task

    def pending(self) -> list[Task]:
        return [t for t in self.tasks if not t.done]

    def __len__(self) -> int:
        return len(self.tasks)

manager = TaskManager()
manager.add("gym")
manager.add("email", 1)
print(len(manager), [str(t) for t in manager.pending()])
```

**Inheritance** — a class based on another:
```python
class RecurringTask(Task):
    def __init__(self, title: str, every_days: int, priority: int = 3):
        super().__init__(title, priority)   # run the parent's setup
        self.every_days = every_days

    def __str__(self) -> str:
        return super().__str__() + f" every {self.every_days}d"
```

**Class methods & properties** (you'll see these in libraries):
```python
class Task:
    def __init__(self, title, priority=3):
        self.title = title
        self.priority = priority

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(data["title"], data.get("priority", 3))

    @property
    def is_urgent(self) -> bool:     # accessed like an attribute: t.is_urgent
        return self.priority == 1
```

**When to use a class vs plain dicts/functions:** use a class when you have data plus several operations that belong together and keep state (like a TaskManager, or an AI "Agent" holding conversation history).

**Exercises**
1. Write a `BankAccount` class with `deposit`, `withdraw` (raise an error if insufficient funds), and `balance`.
2. Add `to_dict()` and `from_dict()` to `Task`, and `save(path)`/`load(path)` to `TaskManager` using JSON.

---

### Lesson 22: Dataclasses and Pydantic

**Dataclasses** remove the boilerplate for classes that mainly hold data:
```python
from dataclasses import dataclass, field, asdict
from datetime import date

@dataclass
class Task:
    title: str
    priority: int = 3
    done: bool = False
    tags: list[str] = field(default_factory=list)   # mutable default done right
    due: date | None = None

t = Task("Write report", priority=1, tags=["work"])
print(t)                 # Task(title='Write report', priority=1, done=False, ...)
print(asdict(t))         # convert to dict (great for JSON)
print(t == Task("Write report", 1, tags=["work"]))   # True — equality for free
```

**Pydantic** (`pip install pydantic`) — like dataclasses, but it **validates** data. AI frameworks use it to define tool inputs and to check AI outputs.
```python
from pydantic import BaseModel, Field, ValidationError

class Task(BaseModel):
    title: str = Field(min_length=1, description="What needs to be done")
    priority: int = Field(default=3, ge=1, le=3, description="1=high, 3=low")
    done: bool = False

t = Task(title="gym", priority="2")     # "2" is converted to 2 automatically
print(t.model_dump())                   # -> dict
print(t.model_dump_json())              # -> JSON string

try:
    Task(title="", priority=7)
except ValidationError as e:
    print(e)                            # tells you exactly what's wrong

# Parse JSON straight into a validated object
t2 = Task.model_validate_json('{"title": "read", "priority": 1}')

# Generate a JSON Schema — this is what you send to an AI to describe a tool!
print(Task.model_json_schema())
```

**Exercise:** Rewrite your Task with Pydantic. Write code that loads tasks from JSON and reports any invalid entries instead of crashing.

---

### Lesson 23: Async Programming

**The problem:** an AI API call can take 5–30 seconds. A normal (synchronous) program sits idle while waiting. If your assistant needs to check email, calendar and weather, doing them one after another is slow.

**The solution:** `async` lets the program start several waits at once.

**Analogy:** a chef who puts pasta on to boil, then chops vegetables while waiting, instead of staring at the pot.

**Core syntax**
```python
import asyncio

async def make_coffee():            # "async def" = a coroutine
    print("Start coffee")
    await asyncio.sleep(3)          # "await" = pause here, let other work run
    print("Coffee ready")
    return "coffee"

async def make_toast():
    print("Start toast")
    await asyncio.sleep(2)
    print("Toast ready")
    return "toast"

async def main():
    # Sequential: ~5 seconds
    # c = await make_coffee()
    # t = await make_toast()

    # Concurrent: ~3 seconds
    c, t = await asyncio.gather(make_coffee(), make_toast())
    print("Breakfast:", c, t)

asyncio.run(main())                 # entry point: starts the event loop
```

**Rules**
- You can only use `await` inside an `async def` function.
- Calling `make_coffee()` without `await` does **nothing** except create a coroutine object (and a warning).
- Use `asyncio.sleep`, never `time.sleep`, inside async code — `time.sleep` freezes everything.
- Use async libraries for I/O: `httpx` (instead of `requests`), `aiofiles`, the async clients of AI SDKs.

**Real example with httpx** (`pip install httpx`):
```python
import asyncio
import time
import httpx

URLS = [
    "https://api.github.com/users/python",
    "https://api.github.com/users/torvalds",
    "https://api.github.com/users/gvanrossum",
]

async def fetch(client: httpx.AsyncClient, url: str) -> dict:
    r = await client.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

async def main():
    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*(fetch(client, u) for u in URLS))
    for user in results:
        print(user["login"], user.get("public_repos"))
    print(f"Took {time.perf_counter() - start:.2f}s")

asyncio.run(main())
```

**Timeouts and error handling in async:**
```python
async def main():
    try:
        await asyncio.wait_for(make_coffee(), timeout=1)
    except asyncio.TimeoutError:
        print("Too slow!")

    results = await asyncio.gather(fetch_a(), fetch_b(), return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            print("One call failed:", r)
```

**Exercises**
1. Fetch 5 GitHub users sequentially with `requests`, then concurrently with `httpx` + `gather`. Compare times.
2. Write an async function that "checks" email, calendar and weather (simulate each with `asyncio.sleep` of different lengths) and prints a morning summary once all finish.

---

### Lesson 24: Logging, Testing, and Code Quality

**Logging** — replace `print` for anything that isn't meant for the user. An AI agent makes many decisions; logs are how you find out what it did.
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
log = logging.getLogger(__name__)

log.debug("Detailed info for debugging")   # hidden at INFO level
log.info("Loaded %d tasks", 12)
log.warning("Task file missing; creating new one")
log.error("API call failed")
try:
    1 / 0
except ZeroDivisionError:
    log.exception("Something broke")       # includes the traceback
```

**Testing with pytest** (`pip install pytest`). Tests are code that checks your code still works after changes.
```python
# tasks.py
def add_task(tasks: list[dict], title: str, priority: int = 3) -> dict:
    if not title.strip():
        raise ValueError("title cannot be empty")
    task = {"title": title.strip(), "priority": priority, "done": False}
    tasks.append(task)
    return task
```
```python
# test_tasks.py
import pytest
from tasks import add_task

def test_add_task_appends():
    tasks = []
    add_task(tasks, "gym")
    assert len(tasks) == 1
    assert tasks[0]["title"] == "gym"

def test_add_task_strips_whitespace():
    tasks = []
    t = add_task(tasks, "  read  ")
    assert t["title"] == "read"

def test_empty_title_raises():
    with pytest.raises(ValueError):
        add_task([], "   ")

@pytest.mark.parametrize("priority", [1, 2, 3])
def test_priorities(priority):
    t = add_task([], "x", priority)
    assert t["priority"] == priority
```
Run:
```bash
pytest -v
```

**Testing with temporary files** (pytest gives you `tmp_path`):
```python
def test_save_and_load(tmp_path):
    path = tmp_path / "tasks.json"
    save_tasks(path, [{"title": "a"}])
    assert load_tasks(path) == [{"title": "a"}]
```

**Code quality with ruff** (`pip install ruff`):
```bash
ruff check .
```
```bash
ruff format .
```
`check` finds bugs and bad patterns; `format` makes code style consistent.

**Style basics (PEP 8)**
- 4-space indents, lines under ~88–100 characters.
- `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- One blank line between methods, two between top-level functions/classes.
- Small functions that do one thing.

---

### Lesson 25: Debugging

**Strategy**
1. **Read the error message** fully, bottom up.
2. **Reproduce** it reliably.
3. **Shrink** the problem — remove code until the smallest version still fails.
4. **Inspect values**: `print(f"{variable=}")`, or use the debugger.
5. **Form a guess, test it**, repeat. Change one thing at a time.

**Built-in debugger**
```python
def total(prices):
    result = 0
    for p in prices:
        breakpoint()        # program pauses here
        result += p
    return result
```
At the `(Pdb)` prompt: `p result` (print), `n` (next line), `s` (step into), `c` (continue), `q` (quit).

**VS Code debugger:** click left of a line number to set a red-dot breakpoint, press **F5**, then hover over variables to see their values. Learn this — it's faster than print statements.

**Asking for help effectively** (from people or AI): include the full error, the smallest code that reproduces it, what you expected, and what you already tried.

---

## Part B: Command Line and Git

### B.1 Terminal Basics

Open: **Terminal** (macOS), **Windows Terminal / PowerShell** (Windows), any terminal (Linux).
On Windows, consider installing **WSL** (Windows Subsystem for Linux) so these commands work exactly as shown.

| Command | What it does | Example |
|---|---|---|
| `pwd` | Show current folder | `pwd` |
| `ls` / `ls -la` | List files (incl. hidden) | `ls -la` |
| `cd folder` | Enter folder | `cd projects` |
| `cd ..` | Go up one level | |
| `cd ~` | Go to home folder | |
| `mkdir name` | Make folder | `mkdir -p a/b/c` |
| `touch file` | Create empty file | `touch main.py` |
| `cp a b` | Copy | `cp -r src backup` |
| `mv a b` | Move / rename | `mv old.py new.py` |
| `rm file` | Delete (no recycle bin!) | `rm -r folder` |
| `cat file` | Print file | |
| `less file` | Scroll file (`q` quits) | |
| `head -n 20 file` / `tail -f app.log` | Start of file / follow a growing log | |
| `grep "text" file` | Search in files | `grep -rn "TODO" .` |
| `which python` | Where is a program | |
| `echo $HOME` | Print a variable | |
| `export KEY=value` | Set env var (this session) | |
| `clear` | Clear screen | |

**Combining commands**
```bash
ls | grep .py
```
```bash
python app.py > output.txt
```
```bash
python app.py >> output.txt 2>&1
```
`|` sends output to another command. `>` writes output to a file (overwrite), `>>` appends, `2>&1` includes errors.

**Shortcuts:** `Tab` autocompletes names, `↑` recalls previous commands, `Ctrl+C` stops a running program, `Ctrl+R` searches history.

**Exercise:** Using only the terminal, create `practice/src/main.py`, write a print statement into it with `echo "print('hi')" > practice/src/main.py`, run it, then delete the `practice` folder.

### B.2 Git Concepts

- **Repository (repo):** a project folder whose history Git tracks.
- **Commit:** a saved snapshot with a message.
- **Branch:** a separate line of work.
- **Remote:** a copy on GitHub.
- **Working directory → staging area → commit:** you choose which changes go into each snapshot.

### B.3 One-time setup
```bash
git config --global user.name "Your Name"
```
```bash
git config --global user.email "you@example.com"
```
```bash
git config --global init.defaultBranch main
```

### B.4 Daily workflow
```bash
git status
```
```bash
git add main.py
```
```bash
git commit -m "Add task listing command"
```
```bash
git push
```
`git add .` stages everything — check `git status` first so you don't commit secrets.

**Good commit messages:** short, present tense, says *what* and *why*: "Add due dates to tasks", not "stuff" or "fixed".

### B.5 Looking at history
```bash
git log --oneline --graph
```
```bash
git diff
```
```bash
git diff --staged
```
```bash
git show <commit-id>
```

### B.6 Undoing things
| Situation | Command |
|---|---|
| Discard unsaved changes to a file | `git restore file.py` |
| Unstage a file | `git restore --staged file.py` |
| Fix the last commit message (not pushed yet) | `git commit --amend -m "new msg"` |
| Undo a pushed commit safely | `git revert <commit-id>` |

### B.7 Branches
```bash
git switch -c add-due-dates
```
Work and commit, then:
```bash
git switch main
```
```bash
git merge add-due-dates
```
On GitHub you normally push the branch and open a **Pull Request** instead of merging locally.

**Merge conflicts:** Git marks the clash in the file like this:
```
<<<<<<< HEAD
priority = 1
=======
priority = 2
>>>>>>> add-due-dates
```
Edit the file to keep what you want, delete the markers, then `git add` and `git commit`.

### B.8 GitHub
```bash
git clone https://github.com/<you>/<repo>.git
```
```bash
git pull
```
```bash
git push -u origin add-due-dates
```

### B.9 .gitignore for Python projects
```
.venv/
__pycache__/
*.pyc
.env
*.log
.pytest_cache/
.ruff_cache/
.DS_Store
```

---

## Part C: JavaScript / TypeScript (Optional)

Only start this after the Python capstone. It's for building web interfaces for your assistant.

### C.1 Python ↔ JavaScript cheat sheet

| Python | JavaScript |
|---|---|
| `name = "x"` | `const name = "x";` / `let count = 0;` |
| `print(x)` | `console.log(x);` |
| `f"Hi {name}"` | `` `Hi ${name}` `` |
| `True / False / None` | `true / false / null` (and `undefined`) |
| `list` `[1, 2]` | array `[1, 2]` |
| `dict` `{"a": 1}` | object `{ a: 1 }` |
| `len(x)` | `x.length` |
| `x.append(1)` | `x.push(1)` |
| `def f(a):` | `function f(a) {}` or `const f = (a) => {}` |
| `for x in items:` | `for (const x of items) {}` |
| `[x*2 for x in items]` | `items.map(x => x * 2)` |
| `[x for x in items if x > 1]` | `items.filter(x => x > 1)` |
| `try / except` | `try { } catch (e) { }` |
| `async def` / `await` | `async function` / `await` |
| `json.loads` / `json.dumps` | `JSON.parse` / `JSON.stringify` |
| `requests.get(url)` | `await fetch(url)` |
| `==` | `===` (always use triple equals) |

### C.2 Learning order
1. Install **Node.js** (LTS) and run `node file.js`.
2. Variables, functions, arrays, objects, `map`/`filter`/`reduce`.
3. `fetch` + `async/await` + `JSON`.
4. HTML and CSS basics; the DOM (`document.querySelector`, event listeners).
5. **TypeScript**: add types (`let count: number = 0`, `interface Task { title: string; done: boolean }`).
6. **React** (components, props, state, `useEffect`), then **Next.js** for full apps.

### C.3 Example
```typescript
interface Task {
  title: string;
  priority: 1 | 2 | 3;
  done: boolean;
}

const tasks: Task[] = [
  { title: "email", priority: 1, done: false },
  { title: "gym", priority: 2, done: true },
];

const pending = tasks.filter((t) => !t.done).map((t) => t.title);
console.log(`Pending: ${pending.join(", ")}`);

async function getUser(name: string): Promise<void> {
  const res = await fetch(`https://api.github.com/users/${name}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  console.log(data.login, data.public_repos);
}
getUser("torvalds");
```

---

## Capstone Project: CLI Work Organizer

Build this yourself, step by step. It uses everything from Part A and B, and it becomes the set of "tools" your AI assistant will control in Section 3.

### Requirements

**Level 1 — basics**
- `add` a task (title, priority 1–3, optional due date, optional tags)
- `list` tasks (pending first, sorted by priority then due date)
- `done <id>` marks complete
- `delete <id>`
- Saves to `data/tasks.json` automatically

**Level 2 — better**
- `list --tag work`, `list --all`, `list --overdue`
- `edit <id>` to change fields
- `today` shows tasks due today or overdue
- Each task has a unique `id` and a `created_at` timestamp
- Invalid input never crashes the program

**Level 3 — professional**
- Code split into modules
- Pydantic models
- Logging to `app.log`
- At least 10 pytest tests
- `ruff check` passes
- README explaining how to install and use it
- Pushed to GitHub with meaningful commits on branches

### Suggested structure
```
work_organizer/
├── .gitignore
├── README.md
├── pyproject.toml           # or requirements.txt
├── organizer/
│   ├── __init__.py
│   ├── models.py            # Task model
│   ├── storage.py           # load/save JSON
│   ├── service.py           # add/list/complete/delete logic (future AI tools!)
│   └── cli.py               # argparse commands
├── data/                    # tasks.json lives here (gitignored)
└── tests/
    ├── test_service.py
    └── test_storage.py
```

### Starter skeleton (fill in the TODOs)

```python
# organizer/models.py
from datetime import date, datetime
from uuid import uuid4
from pydantic import BaseModel, Field

class Task(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:8])
    title: str = Field(min_length=1)
    priority: int = Field(default=3, ge=1, le=3)
    due: date | None = None
    tags: list[str] = Field(default_factory=list)
    done: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

    def is_overdue(self, today: date | None = None) -> bool:
        # TODO: return True if not done and due is before today
        ...
```

```python
# organizer/storage.py
import json
from pathlib import Path
from organizer.models import Task

def load_tasks(path: Path) -> list[Task]:
    # TODO: return [] if the file doesn't exist
    # TODO: read JSON and convert each dict with Task.model_validate(...)
    ...

def save_tasks(path: Path, tasks: list[Task]) -> None:
    # TODO: create parent folder, then write [t.model_dump(mode="json") for t in tasks]
    ...
```

```python
# organizer/service.py
from datetime import date
from organizer.models import Task

class TaskNotFoundError(Exception):
    pass

def add_task(tasks: list[Task], title: str, priority: int = 3,
             due: date | None = None, tags: list[str] | None = None) -> Task:
    """Create a task and add it to the list."""
    # TODO
    ...

def complete_task(tasks: list[Task], task_id: str) -> Task:
    """Mark a task as done. Raises TaskNotFoundError if the id doesn't exist."""
    # TODO
    ...

def delete_task(tasks: list[Task], task_id: str) -> Task:
    """Remove a task and return it."""
    # TODO
    ...

def list_tasks(tasks: list[Task], include_done: bool = False,
               tag: str | None = None, overdue_only: bool = False) -> list[Task]:
    """Filter and sort tasks: priority first, then due date (no date last)."""
    # TODO — hint: sorted(..., key=lambda t: (t.priority, t.due or date.max))
    ...
```

```python
# organizer/cli.py
import argparse
from datetime import date
from pathlib import Path
from organizer import service, storage

DATA_FILE = Path("data/tasks.json")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="organizer", description="Work Organizer")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add a task")
    add.add_argument("title")
    add.add_argument("-p", "--priority", type=int, default=3)
    add.add_argument("-d", "--due", type=date.fromisoformat, help="YYYY-MM-DD")
    add.add_argument("-t", "--tag", action="append", default=[])

    ls = sub.add_parser("list", help="List tasks")
    ls.add_argument("--all", action="store_true")
    ls.add_argument("--tag")
    ls.add_argument("--overdue", action="store_true")

    done = sub.add_parser("done", help="Complete a task")
    done.add_argument("id")

    rm = sub.add_parser("delete", help="Delete a task")
    rm.add_argument("id")
    return parser

def main() -> None:
    args = build_parser().parse_args()
    tasks = storage.load_tasks(DATA_FILE)
    try:
        match args.command:
            case "add":
                # TODO: call service.add_task, save, print confirmation
                ...
            case "list":
                # TODO: call service.list_tasks and print a nice table
                ...
            case "done":
                ...
            case "delete":
                ...
    except service.TaskNotFoundError as e:
        print(f"No task with id {e}")

if __name__ == "__main__":
    main()
```

Run it with:
```bash
python -m organizer.cli add "Write report" -p 1 -d 2026-11-10 -t work
```
```bash
python -m organizer.cli list
```

**Why `service.py` matters:** in Section 3 you'll hand `add_task`, `list_tasks`, `complete_task` etc. to an AI model as tools. Because they have type hints and docstrings and don't print or read input, the AI can call them directly. Keeping logic separate from the CLI is what makes that possible.

---

## Weekly Schedule

| Week | Lessons | Mini-project |
|---|---|---|
| 1 | Part 0, Lessons 1–5, Terminal basics (B.1) | Tip calculator, minutes converter |
| 2 | Lessons 6–7, Git setup & daily workflow (B.2–B.4) | Number-guessing game, pushed to GitHub |
| 3 | Lessons 8–10 | Interactive in-memory to-do list |
| 4 | Lessons 11–12 | Parse a fake AI API response |
| 5 | Lessons 13–14 | Tool-dispatch calculator (functions in a dict) |
| 6 | Lessons 15–16 | To-do list that saves to JSON |
| 7 | Lessons 17–19, Git branches (B.5–B.9) | Split to-do app into modules, add `.env` |
| 8 | Lesson 20 | Weather + GitHub API scripts |
| 9 | Lessons 21–22 | Class/Pydantic-based to-do app |
| 10 | Lesson 23 | Concurrent "morning summary" |
| 11 | Lessons 24–25 | Add tests + logging to to-do app |
| 12–13 | Capstone Levels 1–3 | CLI Work Organizer |
| 14+ | Part C (optional) | Small web page that shows your tasks |

**Daily routine (1–2 hours):** 20 min reading → 40 min typing examples and experimenting → 30 min exercises → 5 min writing notes on what confused you.

---

## Final Checklist

Before starting Section 2 (APIs & AI models), you should be able to do all of this **without looking things up**:

**Python fundamentals**
- [ ] Use variables, all basic types, and convert between them
- [ ] Format strings with f-strings, including decimals
- [ ] Write if/elif/else, for, while, break, continue, match
- [ ] Use lists, dicts, tuples, sets and know when to use each
- [ ] Read deeply nested dict/list data and extract values
- [ ] Write list and dict comprehensions

**Functions & structure**
- [ ] Write functions with defaults, keyword args, `*args`, `**kwargs`
- [ ] Call a function from a dict using `func(**arguments)`
- [ ] Add type hints and docstrings
- [ ] Split code into modules with `if __name__ == "__main__":`

**Robustness**
- [ ] Read a traceback and find the bug
- [ ] Handle specific exceptions and raise your own
- [ ] Write a retry with exponential backoff
- [ ] Use the VS Code debugger

**Data & environment**
- [ ] Read/write text and JSON files with `pathlib`
- [ ] Work with dates using `datetime`
- [ ] Create a virtual environment and install packages
- [ ] Keep API keys in `.env` and out of Git

**Web & advanced**
- [ ] Make GET and POST requests and handle errors and status codes
- [ ] Write classes, dataclasses, and Pydantic models
- [ ] Run several requests concurrently with `async`/`await` and `httpx`
- [ ] Use `logging` and write pytest tests

**Tools**
- [ ] Navigate and manage files in the terminal
- [ ] Commit, branch, push, open a PR, and resolve a merge conflict

---

## Exercise Solutions

Try every exercise yourself first. Look here only after a real attempt (at least 20 minutes).

**Lesson 3, Exercise 1**
```python
raw = "  buy MILK, eggs ,bread  "
items = [part.strip().lower() for part in raw.split(",")]
print(items)   # ['buy milk', 'eggs', 'bread']
```

**Lesson 4, Exercise 1**
```python
minutes = 135
print(f"{minutes // 60}h {minutes % 60}m")
```

**Lesson 6, Exercise 1**
```python
score = int(input("Score: "))
if not 0 <= score <= 100:
    print("Score must be 0-100")
elif score >= 90:
    print("A")
elif score >= 80:
    print("B")
elif score >= 70:
    print("C")
else:
    print("F")
```

**Lesson 7, Exercise 2**
```python
print(sum(n for n in range(1, 1001) if n % 3 == 0 or n % 5 == 0))   # 234168
```

**Lesson 7, Exercise 3**
```python
import random

secret = random.randint(1, 100)
attempts = 0
while True:
    try:
        guess = int(input("Guess (1-100): "))
    except ValueError:
        print("Enter a whole number.")
        continue
    attempts += 1
    if guess < secret:
        print("Higher")
    elif guess > secret:
        print("Lower")
    else:
        print(f"Correct in {attempts} attempts!")
        break
```

**Lesson 8, Exercise 2**
```python
nums = [3, 7, 7, 2, 9, 2, 2]
print(max(nums), min(nums), sum(nums) / len(nums), nums.count(2))
```

**Lesson 9, Exercise 2**
```python
sentence = "hello world"
counts = {}
for ch in sentence.replace(" ", ""):
    counts[ch] = counts.get(ch, 0) + 1
print(counts)
```

**Lesson 11, Exercise 1**
```python
tasks = [
    {"title": "email", "priority": 2, "done": False},
    {"title": "gym", "priority": 3, "done": True},
    {"title": "report", "priority": 1, "done": False},
    {"title": "call", "priority": 3, "done": False},
    {"title": "read", "priority": 2, "done": True},
]
pending = sorted((t for t in tasks if not t["done"]), key=lambda t: t["priority"])
for t in pending:
    print(t["priority"], t["title"])
```

**Lesson 11, Exercise 2**
```python
text = " ".join(b["text"] for b in response["content"] if b["type"] == "text")
```

**Lesson 13, Exercise 2**
```python
def add(a, b): return a + b
def subtract(a, b): return a - b
def multiply(a, b): return a * b
def divide(a, b): return a / b

OPS = {"add": add, "subtract": subtract, "multiply": multiply, "divide": divide}

while True:
    line = input("> ").strip()
    if line == "quit":
        break
    try:
        op, a, b = line.split()
        print(OPS[op](float(a), float(b)))
    except KeyError:
        print("Unknown operation. Use:", ", ".join(OPS))
    except ValueError:
        print("Format: <op> <number> <number>")
    except ZeroDivisionError:
        print("Can't divide by zero")
```

**Lesson 13, Exercise 3**
```python
def summarize(tasks: list[dict]) -> dict:
    done = sum(1 for t in tasks if t["done"])
    return {"total": len(tasks), "done": done, "pending": len(tasks) - done}
```

**Lesson 15, Exercise 1**
```python
def safe_int(text: str, default: int = 0) -> int:
    try:
        return int(text)
    except ValueError:
        return default
```

**Lesson 20, Exercise 1**
```python
import requests

r = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={"latitude": 40.71, "longitude": -74.01, "current_weather": "true"},
    timeout=10,
)
r.raise_for_status()
weather = r.json()["current_weather"]
print(f"{weather['temperature']}°C, wind {weather['windspeed']} km/h")
```

**Lesson 21, Exercise 1**
```python
class InsufficientFundsError(Exception):
    pass

class BankAccount:
    def __init__(self, owner: str, balance: float = 0.0):
        self.owner = owner
        self._balance = balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        if amount > self._balance:
            raise InsufficientFundsError(f"Balance is only {self._balance:.2f}")
        self._balance -= amount

    @property
    def balance(self) -> float:
        return self._balance
```

**Lesson 23, Exercise 2**
```python
import asyncio

async def check(name: str, seconds: float, result: str) -> str:
    await asyncio.sleep(seconds)
    return f"{name}: {result}"

async def main():
    results = await asyncio.gather(
        check("Email", 2, "3 unread"),
        check("Calendar", 1, "2 meetings"),
        check("Weather", 1.5, "Sunny, 18°C"),
    )
    print("Good morning!")
    for line in results:
        print(" -", line)

asyncio.run(main())   # takes ~2s, not 4.5s
```

---

## Recommended Resources

| Resource | Type | Best for |
|---|---|---|
| docs.python.org/3/tutorial | Official tutorial | Accurate reference |
| *Automate the Boring Stuff with Python* (free online) | Book | Practical beginners' projects |
| CS50's Introduction to Programming with Python (Harvard, free) | Video course | Structured lessons + problem sets |
| *Python Crash Course* (Eric Matthes) | Book | Projects-based learning |
| Real Python (realpython.com) | Articles | Deep dives on single topics |
| Exercism.org (Python track) | Exercises | Practice with mentor feedback |
| *Pro Git* (git-scm.com/book, free) | Book | Git |
| learngitbranching.js.org | Interactive | Understanding branches visually |
| javascript.info | Tutorial | JavaScript (Part C) |

**Next:** Section 2 — Working with Data and APIs (HTTP in depth, OAuth, and your first AI model call).
