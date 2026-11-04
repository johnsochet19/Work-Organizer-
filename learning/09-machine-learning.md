# Section 9: Deeper Machine Learning (Optional) — Complete Study Guide

**This section is optional.** You do not need any of it to build, run or improve the AI assistant you deployed in Section 8 — hosted models called over an API remain the best choice for most assistants. This section is for you if you want to understand *what happens inside the model*, or to run and customise models yourself: on your own machine, offline, cheaply, or trained on your own data.

By the end you will have fine-tuned a small open model to turn plain-English requests into Work Organizer tool calls, measured it against Claude on held-out examples, and served it locally with Ollama.

Work through it in order. Each lesson has:

- **Concepts**: what to understand
- **Code**: examples to type out yourself (don't copy-paste; typing builds memory)
- **Common mistakes**: errors beginners hit
- **Exercises**: do them before moving on
- **Check yourself**: you should be able to answer these without looking

The maths is taught **with numpy code, not proofs**. If you can read a Python loop, you can follow every formula here. Formulas are written in plain text, like `y = w * x + b`.

Total time: roughly **8–12 weeks at 1–2 hours a day**. Parts A–C are the foundation. If you only want to run and fine-tune models you can skim them, but Part F makes far more sense if you don't.

---

## Table of Contents

- [Part 0: Setting Up](#part-0-setting-up)
- [Part A: The Math You Actually Need](#part-a-the-math-you-actually-need)
  - [Lesson 1: Vectors and the Dot Product](#lesson-1-vectors-and-the-dot-product)
  - [Lesson 2: Matrices and Matrix Multiplication](#lesson-2-matrices-and-matrix-multiplication)
  - [Lesson 3: Derivatives and the Chain Rule](#lesson-3-derivatives-and-the-chain-rule)
  - [Lesson 4: Gradients and Gradient Descent](#lesson-4-gradients-and-gradient-descent)
  - [Lesson 5: Probability, Softmax and Cross-Entropy](#lesson-5-probability-softmax-and-cross-entropy)
- [Part B: Data and Classic Machine Learning](#part-b-data-and-classic-machine-learning)
  - [Lesson 6: NumPy Essentials](#lesson-6-numpy-essentials)
  - [Lesson 7: pandas Essentials](#lesson-7-pandas-essentials)
  - [Lesson 8: Your First Model with scikit-learn](#lesson-8-your-first-model-with-scikit-learn)
  - [Lesson 9: Classification: A Task-Priority Classifier](#lesson-9-classification-a-task-priority-classifier)
  - [Lesson 10: Overfitting and Metrics](#lesson-10-overfitting-and-metrics)
- [Part C: Neural Networks](#part-c-neural-networks)
  - [Lesson 11: A Neural Network From Scratch: the Forward Pass](#lesson-11-a-neural-network-from-scratch-the-forward-pass)
  - [Lesson 12: Backpropagation From Scratch](#lesson-12-backpropagation-from-scratch)
  - [Lesson 13: PyTorch Tensors and Autograd](#lesson-13-pytorch-tensors-and-autograd)
  - [Lesson 14: Training in PyTorch](#lesson-14-training-in-pytorch)
- [Part D: How Language Models Work](#part-d-how-language-models-work)
  - [Lesson 15: Tokenization](#lesson-15-tokenization)
  - [Lesson 16: Embeddings](#lesson-16-embeddings)
  - [Lesson 17: Attention and the Transformer](#lesson-17-attention-and-the-transformer)
  - [Lesson 18: Next-Token Prediction and How Models Are Trained](#lesson-18-next-token-prediction-and-how-models-are-trained)
- [Part E: Working with Open Models](#part-e-working-with-open-models)
  - [Lesson 19: Hugging Face: Pipelines, Auto Classes and the Hub](#lesson-19-hugging-face-pipelines-auto-classes-and-the-hub)
  - [Lesson 20: Hugging Face Datasets](#lesson-20-hugging-face-datasets)
  - [Lesson 21: Running Models Locally: Ollama, llama.cpp and Quantization](#lesson-21-running-models-locally-ollama-llamacpp-and-quantization)
- [Part F: Fine-Tuning](#part-f-fine-tuning)
  - [Lesson 22: When Fine-Tuning Is Worth It](#lesson-22-when-fine-tuning-is-worth-it)
  - [Lesson 23: LoRA and QLoRA](#lesson-23-lora-and-qlora)
  - [Lesson 24: Fine-Tuning with peft and trl](#lesson-24-fine-tuning-with-peft-and-trl)
  - [Lesson 25: Evaluating a Fine-Tuned Model](#lesson-25-evaluating-a-fine-tuned-model)
  - [Lesson 26: Free GPUs and What Training Costs](#lesson-26-free-gpus-and-what-training-costs)
  - [Lesson 27: Ethics, Bias and Licensing](#lesson-27-ethics-bias-and-licensing)
- [Capstone Project: A Local Tool-Calling Model](#capstone-project-a-local-tool-calling-model)
- [Weekly Schedule](#weekly-schedule)
- [Final Checklist](#final-checklist)
- [Exercise Solutions](#exercise-solutions)
- [Recommended Resources](#recommended-resources)

---

## Part 0: Setting Up

### 0.1 A separate project and virtual environment

ML packages are large (PyTorch alone is several GB with GPU support) and pin each other's versions tightly. Keep them **out of your assistant's environment**.

In a new `ml-study` folder, create and activate a virtual environment exactly as in Section 1:
```bash
python -m venv .venv
```
```bash
source .venv/bin/activate
```
(On Windows PowerShell: `.venv\Scripts\Activate.ps1`.)

### 0.2 Install the packages

```bash
pip install numpy pandas scikit-learn matplotlib jupyter
```
```bash
pip install torch
```
```bash
pip install transformers datasets accelerate peft trl
```

**GPU note.** With an NVIDIA GPU, `pip install torch` usually installs a CUDA build; if not, use the selector at pytorch.org. On Apple Silicon Macs the normal install supports the **MPS** (Metal) backend. No GPU? Everything up to Part E runs on a CPU, and for Part F you'll use a free cloud GPU (Lesson 26).

```python
import torch

print(torch.__version__)
print("CUDA (NVIDIA):", torch.cuda.is_available())
print("MPS (Apple):  ", torch.backends.mps.is_available())
```

**Notebooks vs scripts.** Explore in Jupyter (`jupyter lab`) or Google Colab, but move anything you'll rerun — training, evaluation — into `.py` scripts. Notebooks run out of order are a classic source of "it worked yesterday" bugs.

---

## Part A: The Math You Actually Need

You need five ideas: **vectors, matrix multiplication, derivatives, gradients, and probabilities**. All five fit in this part.

### Lesson 1: Vectors and the Dot Product

**Concepts**
- A **vector** is a list of numbers. In ML everything becomes a vector: a task (hours, days until due), a word (an embedding, Lesson 16), an image.
- The **dot product** multiplies two vectors element by element and adds the results: `a · b = a1*b1 + a2*b2 + a3*b3`. It's the most common operation in all of deep learning.
- A dot product is large when two vectors "point the same way". **Cosine similarity** divides by the vectors' lengths to give a score from -1 (opposite) to 1 (same direction) — exactly how your RAG search found relevant documents.

**Code**
```python
import numpy as np

a = np.array([1.0, 2.0, 3.0])
b = np.array([4.0, 5.0, 6.0])

print(a + b)          # [5. 7. 9.]    element-wise
print(a * b)          # [ 4. 10. 18.] element-wise multiply (NOT the dot product)
print(a @ b)          # 32.0 = 1*4 + 2*5 + 3*6   (same as np.dot(a, b))
print(np.linalg.norm(a))   # length: sqrt(1 + 4 + 9) = 3.7416...

def cosine_similarity(u: np.ndarray, v: np.ndarray) -> float:
    return float(u @ v / (np.linalg.norm(u) * np.linalg.norm(v)))

# Toy "meaning" vectors: [work-ness, urgency, fun]
email_boss = np.array([0.9, 0.8, 0.1])
write_report = np.array([0.95, 0.6, 0.0])
go_to_beach = np.array([0.0, 0.1, 0.95])
print(cosine_similarity(email_boss, write_report))  # ~0.98 — similar
print(cosine_similarity(email_boss, go_to_beach))   # ~0.15 — unrelated

# A weighted sum IS a dot product: score = 0.5*urgency + 0.3*importance - 0.2*effort
weights = np.array([0.5, 0.3, -0.2])
features = np.array([0.9, 0.7, 0.4])
print(weights @ features)   # 0.58
```
Machine learning is, at heart, *finding good weights automatically* instead of guessing them.

**Common mistakes**
- Using `a * b` when you mean the dot product. `*` is element-wise; `@` is the dot product.
- Using Python lists: `[1, 2] * 2` gives `[1, 2, 1, 2]`. Convert with `np.array(...)` first.

**Exercises**
1. Compute the dot product of `[2, -1, 0.5]` and `[4, 3, 2]` by hand, then check with numpy.
2. Write `cosine_similarity` using only a `for` loop and `math.sqrt`.

**Check yourself**
- What does a dot product of 0 between two vectors mean?
- Why is a weighted sum the same thing as a dot product?

---

### Lesson 2: Matrices and Matrix Multiplication

**Concepts**
- A **matrix** is a 2-D grid of numbers with a **shape** `(rows, columns)`. 100 tasks with 3 features each is a `(100, 3)` matrix: one row per task.
- **Matrix multiplication** `A @ B` is "lots of dot products at once": each result entry is the dot product of a row of `A` with a column of `B`.
- **The shape rule:** `(n, k) @ (k, m) -> (n, m)`. The inner numbers must match.
- A neural-network layer is just `outputs = inputs @ W + b`. Training means finding a good `W`.
- `@` is no magic: it's three nested loops (rows × columns × the shared dimension) running in fast C code.

**Code**
```python
import numpy as np

X = np.array([
    [0.9, 0.7, 0.4],   # task 1: urgency, importance, effort
    [0.2, 0.9, 0.8],   # task 2
    [0.5, 0.1, 0.1],   # task 3
])
w = np.array([0.5, 0.3, -0.2])
print(X @ w)          # [0.58 0.21 0.26] — one score per task, all at once

A, B = np.ones((4, 3)), np.ones((3, 2))
print((A @ B).shape)  # (4, 2);  A @ A -> ValueError: inner dimensions 3 and 4 don't match
print(A.T.shape)      # (3, 4): transpose swaps rows and columns

# A "layer": 3 inputs -> 2 outputs
W = np.array([[0.1, -0.3],
              [0.4,  0.2],
              [-0.5, 0.6]])        # shape (3, 2)
b = np.array([0.01, -0.02])       # shape (2,) — "broadcast" (added) to every row
print((X @ W + b).shape)          # (3, 2)

```

**Common mistakes**
- Mixing up shape `(3,)` (a 1-D vector) and `(3, 1)` (a column matrix); they broadcast differently. Print `.shape` constantly.
- Expecting `A @ B == B @ A`. Matrix multiplication is **not** commutative.

**Exercises**
1. Predict the shape of `np.ones((8, 5)) @ np.ones((5, 16)) @ np.ones((16, 1))`, then check.
2. Multiply `[[1, 2], [3, 4]]` by itself by hand, then check with `@`.

**Check yourself**
- A batch of 32 inputs with 768 features goes through a layer that outputs 3072 features. What shape is `W`?

---

### Lesson 3: Derivatives and the Chain Rule

**Concepts**
- A **derivative** answers: *if I nudge the input a tiny bit, how much does the output change, and in which direction?* For `f(x) = x ** 2` it's `2 * x`.
- You can always **estimate** a derivative numerically: `(f(x + h) - f(x - h)) / (2 * h)` with a tiny `h`. Slow, but perfect for checking your work.
- The **chain rule**: if `y` depends on `u` and `u` depends on `x`, then `dy/dx = dy/du * du/dx`. Effects multiply along a chain. Backpropagation (Lesson 12) is just the chain rule applied over and over.
- With several inputs (`loss(w, b)`), a **partial derivative** varies one input while holding the others fixed.

**Derivatives you'll meet** (just recognise them):

| Function | Derivative |
|---|---|
| `a * x` | `a` |
| `x ** n` | `n * x ** (n - 1)` |
| `exp(x)` / `log(x)` | `exp(x)` / `1 / x` |
| `relu(x) = max(0, x)` | `1` if `x > 0` else `0` |
| `sigmoid(x) = 1 / (1 + exp(-x))` | `sigmoid(x) * (1 - sigmoid(x))` |

**The chain rule on an ML example.** A one-weight model predicts `pred = w * x`; its squared error is `loss = (pred - y) ** 2`:
```
d loss / d pred = 2 * (pred - y)
d pred / d w    = x
d loss / d w    = 2 * (pred - y) * x        (chain rule: multiply)
```

**Code**
```python
def numerical_derivative(func, x, h=1e-5):
    return (func(x + h) - func(x - h)) / (2 * h)

print(numerical_derivative(lambda x: x ** 2, 3.0))   # ~6.0  (matches 2 * x)

x, y = 2.0, 10.0    # one training example: input 2 should give 10
w = 3.0             # current guess

def loss_for(w):
    return (w * x - y) ** 2

analytic = 2 * (w * x - y) * x                  # 2 * (6 - 10) * 2 = -16.0
print(analytic, numerical_derivative(loss_for, w))   # -16.0  ~-16.0
```
The derivative is **negative**: increasing `w` will *reduce* the loss. That single fact is how every model learns.

**Common mistakes**
- A huge `h` (inaccurate) or a ridiculously tiny one like `1e-15` (floating-point noise). `1e-5` is a good default.
- Forgetting a link in the chain. Write each dependency on its own line, as above.

**Exercises**
1. Numerically check that the derivative of `sigmoid` at `x = 0` is `0.25`.
2. For `pred = w * x + b` and `loss = (pred - y) ** 2`, write the derivatives with respect to `w` and `b`. Check both numerically with `x=2, y=10, w=3, b=1`.

**Check yourself**
- In one sentence, what does a derivative tell you?
- State the chain rule in your own words.

---

### Lesson 4: Gradients and Gradient Descent

**Concepts**
- The **gradient** is the list of all partial derivatives, one per parameter. For an LLM it has *billions* of entries.
- The gradient points in the direction that **increases** the loss fastest, so step the **opposite** way: `parameter = parameter - learning_rate * gradient`. Repeat. That's **gradient descent**.
- The **learning rate** is the step size. Too small: painfully slow. Too large: the loss explodes to `nan`.
- A **loss function** is one number saying how wrong the model is: **mean squared error** for numbers, **cross-entropy** (Lesson 5) for categories.
- Real training uses **stochastic gradient descent**: compute the gradient on a small random **batch** (e.g. 32 examples), step, repeat. One pass over all the data is an **epoch**.

**Code: fit a line with gradient descent**
```python
import numpy as np

rng = np.random.default_rng(42)
x = rng.uniform(0, 10, 100)
y = 3 * x + 2 + rng.normal(0, 1, 100)   # the "true" rule is y = 3x + 2, plus noise

w, b = 0.0, 0.0
learning_rate = 0.01

for step in range(2001):
    pred = w * x + b
    error = pred - y
    loss = np.mean(error ** 2)

    dw = 2 * np.mean(error * x)          # chain rule (Lesson 3), averaged over examples
    db = 2 * np.mean(error)

    w -= learning_rate * dw              # step downhill
    b -= learning_rate * db

    if step % 400 == 0:
        print(f"step {step:4d}  loss {loss:8.3f}  w {w:.3f}  b {b:.3f}")
# Ends near w ≈ 3, b ≈ 2: the model "discovered" the rule from data
```
**Break it on purpose:** try `learning_rate = 0.0001` (very slow) and `0.05` (loss shoots to `inf`/`nan` — each step overshoots the valley).

**Common mistakes**
- Not shuffling between epochs — the model can learn the *order* of the data.
- Features on wildly different scales (hours 0–8 vs days 0–365): one learning rate can't suit both. **Scale your features** (Lesson 9).

**Exercises**
1. Plot the loss curve (`plt.plot(losses)`) for learning rates 0.001, 0.01 and 0.03.
2. Extend to two features: `y = 2*x1 - 1*x2 + 0.5`. Use `X @ w + b`; the gradient of `w` is `2 * X.T @ error / n`.

**Check yourself**
- Why subtract the gradient rather than add it?
- What's the difference between a step and an epoch?

---

### Lesson 5: Probability, Softmax and Cross-Entropy

These three ideas are how a language model picks its next word, and how it's trained.

**Concepts**
- A **probability distribution** is a list of non-negative numbers summing to 1: "next word: `Monday` 0.6, `Friday` 0.3, `banana` 0.1".
- Models output raw scores called **logits**. **Softmax** turns them into probabilities: `softmax(z)_i = exp(z_i) / sum(exp(z))`.
- **Cross-entropy loss** measures surprise at the right answer: `loss = -log(p_correct)`. `p = 0.9` gives 0.105; `p = 0.01` gives 4.6. Training pushes `p_correct` up.
- **Temperature** divides logits before softmax: low (0.2) = sharper, more deterministic; high (1.5) = flatter, more random. It's the `temperature` setting from the API sections.
- Combined, softmax + cross-entropy has a beautifully simple gradient with respect to the logits: `probs - one_hot(correct)` — "raise the right answer's score, lower the others in proportion to how wrong they were".

**Code**
```python
import numpy as np

def softmax(z: np.ndarray) -> np.ndarray:
    z = z - np.max(z)          # subtract the max for numerical stability (result unchanged)
    e = np.exp(z)
    return e / e.sum()

logits = np.array([2.0, 1.0, 0.1])          # scores for ["Monday", "Friday", "banana"]
probs = softmax(logits)
print(probs.round(3), probs.sum())           # [0.659 0.242 0.099] 1.0
print(softmax(np.array([1000.0, 999.0])))    # works; without the max trick exp(1000) = inf

def cross_entropy(probs: np.ndarray, correct_index: int) -> float:
    return float(-np.log(probs[correct_index] + 1e-12))   # epsilon avoids log(0)

print(cross_entropy(probs, 0))   # ~0.42: correct answer was likely   -> low loss
print(cross_entropy(probs, 2))   # ~2.32: correct answer was unlikely -> high loss

for t in [0.2, 1.0, 2.0]:
    print(t, softmax(logits / t).round(3))
# 0.2 -> [0.993 0.007 0.   ]  nearly always "Monday"
# 2.0 -> [0.502 0.304 0.194]  much more random

rng = np.random.default_rng(0)
print(rng.choice(["Monday", "Friday", "banana"], size=10, p=probs))   # sampling

print(probs - np.array([1.0, 0.0, 0.0]))   # gradient wrt logits if "Monday" is correct
```

**Common mistakes**
- Writing softmax without subtracting the max — `nan` on large logits.
- Taking `log(0)`. Add an epsilon, or use a library loss that takes logits directly (PyTorch's `CrossEntropyLoss` does).

**Exercises**
1. Write `softmax` for a **batch**: input shape `(n, k)`, softmax along each row (`axis=1, keepdims=True`).
2. What is the cross-entropy loss if a model gives each of 50,000 vocabulary words equal probability? (Roughly an untrained LLM's starting loss.)
3. Check the `probs - one_hot` gradient numerically by nudging each logit (Lesson 3).

**Check yourself**
- What does softmax guarantee about its outputs?
- Why is `-log(p_correct)` a sensible loss? What does lowering the temperature do?

---

## Part B: Data and Classic Machine Learning

Every ML project follows the same workflow: **get data → split it → train → measure on unseen data → improve**. Learn it here with small, fast models; it's identical when you fine-tune an LLM in Part F.

### Lesson 6: NumPy Essentials

**Concepts**
- Arrays have a fixed **dtype** (`float32`, `int64`, `bool`…) and a **shape**.
- **Vectorise**: replace Python loops with whole-array operations — typically 10–100× faster.
- **Axis**: `axis=0` works down the rows (one result per column); `axis=1` across columns (one per row).
- **Broadcasting**: compare shapes from the right; dimensions are compatible if equal or one of them is 1.

**Code**
```python
import numpy as np

rng = np.random.default_rng(seed=0)          # always seed: reproducible results
a = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
print(a.shape, a.dtype)                      # (2, 3) float32
print(np.zeros((2, 3)), np.arange(0, 10, 2), np.linspace(0, 1, 5))
print(rng.normal(0, 1, size=(2, 2)), rng.integers(1, 4, size=5))

print(np.arange(12).reshape(3, 4))           # reshape; -1 means "work it out": reshape(-1, 2)
print(a[0, 1], a[:, 0], a[1])                # 2.0  [1. 4.]  [4. 5. 6.]

hours = np.array([0.5, 3.0, 8.0, 1.5, 6.0])
print(hours[hours > 2])                      # boolean mask -> [3. 8. 6.]
print((hours > 2).sum())                     # 3 — True counts as 1
print(np.where(hours > 2, "long", "short"))

print(a.sum(axis=0), a.sum(axis=1))          # [5. 7. 9.]  [ 6. 15.]
print(a.argmax(axis=1))                      # index of the max in each row

# Standardise features: mean 0, std 1 per column (you'll do this a lot)
X = rng.uniform(0, 100, size=(5, 3))
X_std = (X - X.mean(axis=0)) / X.std(axis=0) # (5, 3) - (3,) broadcasts across rows
print(X_std.mean(axis=0).round(6), X_std.std(axis=0))
```

**Common mistakes**
- `b = a` doesn't copy; use `a.copy()`.
- Integer arrays silently truncate: assigning `0.7` into an `int` array stores `0`.
- Surprise broadcasting: `(5,) + (5, 1)` gives a `(5, 5)` array, not an error. Print shapes.

**Exercises**
1. Create a `(6, 4)` random array and print the row with the largest sum.
2. Time `sum(v * v for v in x)` against `np.sum(x * x)` for a million random numbers.

**Check yourself**
- What does `axis=0` mean in `X.mean(axis=0)`?

---

### Lesson 7: pandas Essentials

**Concepts**
- A **DataFrame** is a table: named columns, each a numpy array underneath. Real ML data arrives as CSV/JSON and gets cleaned in pandas first.

**A synthetic task dataset.** Save this as `task_data.py`; Lessons 7–14 use it. The priority label depends (noisily) on the features — just like real data.

```python
# task_data.py
import numpy as np
import pandas as pd

VERBS = ["Email", "Call", "Prepare", "Review", "Fix", "Update", "Plan", "Book", "Draft", "Submit"]
OBJECTS = ["client report", "budget", "slides", "invoice", "team meeting",
           "login bug", "travel", "contract", "newsletter", "tax form"]

def make_tasks(n: int = 800, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "title": [f"{rng.choice(VERBS)} {rng.choice(OBJECTS)}" for _ in range(n)],
        "hours": rng.uniform(0.25, 8, n).round(2),
        "days_until_due": rng.integers(0, 30, n),
        "from_manager": rng.random(n) < 0.3,
        "blocking_others": rng.integers(0, 5, n),
    })
    # Time actually spent: people underestimate by ~30%, with noise
    df["actual_hours"] = (df["hours"] * 1.3 + rng.normal(0, 0.5, n)).clip(0.1).round(2)
    # Hidden "true" urgency rule + noise -> priority 1 (high), 2, 3 (low)
    score = (-0.15 * df["days_until_due"] + 1.5 * df["from_manager"]
             + 0.6 * df["blocking_others"] + rng.normal(0, 0.8, n))
    df["priority"] = np.select([score > 0.5, score > -1.5], [1, 2], default=3)
    # Make a few values missing, as in real life
    df.loc[rng.choice(n, 20, replace=False), "hours"] = np.nan
    return df
```

**Code**
```python
from task_data import make_tasks

df = make_tasks()
print(df.head())                                   # always LOOK first
df.info()                                          # columns, dtypes, missing values
print(df.describe())
print(df["priority"].value_counts().sort_index())  # class balance

urgent = df[df["priority"] == 1]
manager_urgent = df[(df["priority"] == 1) & (df["from_manager"])]   # & not 'and', with brackets
print(len(urgent), len(manager_urgent), df.loc[0, "title"], df.iloc[0, 0])

df["overrun"] = df["actual_hours"] - df["hours"]   # new columns are vectorised
df["verb"] = df["title"].str.split().str[0]
df["hours"] = df["hours"].fillna(df["hours"].median())   # one way to handle missing values

print(df.groupby("priority")[["days_until_due", "blocking_others"]].mean())
print(df.groupby("verb")["actual_hours"].agg(["mean", "count"]).sort_values("mean"))

df.to_csv("tasks.csv", index=False)

X = df[["hours", "days_until_due", "from_manager", "blocking_others"]].to_numpy(dtype=float)
y = df["priority"].to_numpy()
print(X.shape, y.shape)                            # (800, 4) (800,) — what models want
```
Your real Work Organizer tasks load the same way: `pd.read_json("data/tasks.json")`.

**Common mistakes**
- `df[df.a > 1 and df.b < 2]` → error. Use `&`, `|`, `~` with parentheses around each condition.
- Modifying a filtered view (`SettingWithCopyWarning`). Add `.copy()` after filtering if you'll change it.

**Exercises**
1. What percentage of priority-1 tasks come from a manager? Of priority-3 tasks? (Hint: `pd.crosstab`.)
2. Load your own `tasks.json` and count tasks per tag (hint: `df.explode("tags")`).

**Check yourself**
- What's the difference between `.loc` and `.iloc`? Why check `value_counts()` of the label before training?

---

### Lesson 8: Your First Model with scikit-learn

**Concepts**
- **Supervised learning** learns a mapping from **features** `X` to **labels** `y`. **Regression** predicts a number; **classification** predicts a category.
- **Train/test split**: hold back data the model never sees in training, and score on it. Otherwise you're grading a student with the exam they studied from.
- Every scikit-learn model has the same interface: `model.fit(X_train, y_train)`, then `model.predict(X_new)`.
- Always compare against a **baseline** (e.g. "always predict the average").

**Code: predict how long a task will *really* take**
```python
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from task_data import make_tasks

df = make_tasks().dropna()
X = df[["hours", "blocking_others"]]
y = df["actual_hours"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression().fit(X_train, y_train)
print("coefficients:", dict(zip(X.columns, model.coef_.round(3))))   # hours ≈ 1.3
print("intercept:", round(model.intercept_, 3))

pred = model.predict(X_test)
print("MAE:", round(mean_absolute_error(y_test, pred), 3), "hours")
baseline = [y_train.mean()] * len(y_test)
print("Baseline MAE:", round(mean_absolute_error(y_test, baseline), 3))   # much worse
```
`LinearRegression` is Lesson 4's `y = w * x + b` with one weight per feature — scikit-learn just solves for the weights directly. **MAE** is the average miss in the target's units; `model.score()` gives **R²** (1.0 = perfect, 0 = no better than predicting the mean).

**Common mistakes**
- Evaluating on the training data — it always looks great and tells you nothing.
- No `random_state`: the split changes every run and experiments aren't comparable.

**Exercises**
1. Add `days_until_due` as a feature. Does MAE improve? Why might it not?
2. Train with `test_size=0.05`. Why is a tiny test set a problem even if the score looks good?

**Check yourself**
- Why must the test set stay unseen? What's a baseline for?

---

### Lesson 9: Classification: A Task-Priority Classifier

**Concepts**
- **Logistic regression** is a linear model followed by softmax (Lesson 5). It outputs class probabilities.
- A **decision tree** learns a flowchart of yes/no questions ("days_until_due ≤ 16.5?"). Readable, no scaling needed, overfits easily.
- **Scale features** for linear models with `StandardScaler` (Lesson 6's standardisation).
- A **Pipeline** chains preprocessing and model, so the scaler is fit on training data only and can't be forgotten at prediction time.

**Code**
```python
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

from task_data import make_tasks

df = make_tasks().dropna()
FEATURES = ["hours", "days_until_due", "from_manager", "blocking_others"]
X, y = df[FEATURES].astype(float), df["priority"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)   # stratify keeps class proportions

logreg = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
print("LogReg accuracy:", round(logreg.score(X_test, y_test), 3))
print("probs:", logreg.predict_proba(X_test.iloc[[0]]).round(3), "classes:", logreg.classes_)
print(dict(zip(FEATURES, logreg[-1].coef_[0].round(2))))   # weights for the "priority 1" class
# days_until_due negative, from_manager & blocking_others positive — matches the hidden rule

tree = DecisionTreeClassifier(max_depth=3, random_state=42).fit(X_train, y_train)
print("Tree accuracy:", round(tree.score(X_test, y_test), 3))
print(export_text(tree, feature_names=FEATURES))           # the learned flowchart

print("Baseline:", round((y_test == y_train.mode()[0]).mean(), 3))   # always the commonest class

# Save it. joblib files are pickles: only ever load files you created yourself.
joblib.dump(logreg, "priority_model.joblib")
```
You could now expose `predict_priority(task)` as a tool in your assistant — a tiny, fast, free model doing one job well. (Text such as titles can become features too, with `TfidfVectorizer` inside a `ColumnTransformer`.)

**Common mistakes**
- Scaling *before* splitting, so test-set statistics leak into training. Pipelines prevent it.
- Ignoring class imbalance: if 90% of tasks are priority 3, "always 3" scores 90% and is useless.

**Exercises**
1. Try `RandomForestClassifier(n_estimators=200, random_state=42)`. Does it beat one tree?
2. Write `predict_priority(hours, days_until_due, from_manager, blocking_others) -> int` that loads the saved model.

**Check yourself**
- Why is logistic regression a classifier despite its name? What problem does a Pipeline solve?

---

### Lesson 10: Overfitting and Metrics

**Concepts**
- **Overfitting**: the model memorises training examples (noise included) instead of the general pattern — training score far above test score. **Underfitting**: both low.
- When you try many settings, choose them with a **validation set** or **cross-validation**. Touch the test set once, at the end.
- **Accuracy can lie.** For a class you care about (say "urgent"):
  - **Precision**: of the tasks the model *called* urgent, how many really were? (Low = false alarms.)
  - **Recall**: of the *truly* urgent tasks, how many did it catch? (Low = missed tasks.)
  - **F1** balances the two.
- **Data leakage**: information about the answer sneaks into the features (e.g. `completed_late` when predicting priority). Ask: "would I really have this at prediction time?"

**Code**
```python
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from task_data import make_tasks

df = make_tasks().dropna()
FEATURES = ["hours", "days_until_due", "from_manager", "blocking_others"]
X, y = df[FEATURES].astype(float), df["priority"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

for depth in [1, 2, 3, 5, 8, 12, None]:
    tree = DecisionTreeClassifier(max_depth=depth, random_state=42).fit(X_train, y_train)
    print(f"depth {str(depth):>4}  train {tree.score(X_train, y_train):.3f}  test {tree.score(X_test, y_test):.3f}")
# Train accuracy climbs to ~1.0, but test accuracy peaks around depth 5-8 and then
# falls: the deep trees are memorising noise

model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
pred = model.predict(X_test)
print(confusion_matrix(y_test, pred))       # rows = true class, columns = predicted
print(classification_report(y_test, pred, digits=3))
print("CV accuracy:", cross_val_score(model, X_train, y_train, cv=5).round(3))
```

**Precision and recall by hand**
```python
import numpy as np

true_urgent = np.array([1, 1, 1, 0, 0, 0, 0, 1, 0, 0], dtype=bool)
pred_urgent = np.array([1, 1, 0, 1, 0, 0, 0, 0, 0, 0], dtype=bool)
tp = (pred_urgent & true_urgent).sum()     # 2: called urgent, was urgent
fp = (pred_urgent & ~true_urgent).sum()    # 1: false alarm
fn = (~pred_urgent & true_urgent).sum()    # 2: missed
precision, recall = tp / (tp + fp), tp / (tp + fn)
print(precision, recall, 2 * precision * recall / (precision + recall))   # 0.667 0.5 0.571
```

| Situation | Care most about |
|---|---|
| Flagging urgent tasks (a miss is costly) | Recall |
| Auto-deleting "spam" tasks (a wrong delete is costly) | Precision |
| Tool-call model (capstone) | Exact match + per-field accuracy |

**Fighting overfitting:** more and more varied data; simpler models (`max_depth`; a lower LoRA rank later); regularisation (weight decay, dropout); stopping when validation loss rises; and an honest held-out test set — for LLMs, one with *new phrasings*.

**Common mistakes**
- Tuning hyperparameters on the test set. Reporting accuracy alone on imbalanced data.
- Duplicates in both train and test (common with generated data — deduplicate *before* splitting).

**Exercises**
1. Use `GridSearchCV` to choose `max_depth` and `min_samples_leaf` with 5-fold cross-validation, then evaluate once on the test set.
2. Compute precision and recall for priority 1 from the confusion matrix by hand; check against the report.

**Check yourself**
- Train 99%, test 70%: what's happening and what would you try?
- Explain precision and recall with the "urgent task" example.

---

## Part C: Neural Networks

A neural network is Lessons 1–5 stacked: matrix multiplications, a simple non-linear function between them, a loss, and gradient descent. Build one from scratch in numpy so nothing is magic, then rebuild it in PyTorch — the framework every open LLM is written in.

### Lesson 11: A Neural Network From Scratch: the Forward Pass

**Concepts**
- A **neuron** computes a weighted sum plus a bias, then applies an **activation function**: `activation(inputs @ w + b)`.
- A **layer** is many neurons side by side: `activation(X @ W + b)`, one column of `W` per neuron.
- **Why activations?** Stacked linear layers collapse into one linear layer, which can only draw straight boundaries. Non-linear activations let networks bend them into any shape.
- The **forward pass** runs inputs through every layer to get a prediction.

| Activation | Formula | Where you'll see it |
|---|---|---|
| ReLU | `max(0, x)` | Hidden layers (the default) |
| Sigmoid | `1 / (1 + exp(-x))` (0 to 1) | Binary probability output |
| Softmax | Lesson 5 | Multi-class output; an LLM's next token |
| GELU / SiLU | Smooth versions of ReLU | Inside transformers |

**Code**
```python
import numpy as np

rng = np.random.default_rng(0)

def relu(z):
    return np.maximum(0, z)

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

class Dense:
    """A fully connected layer: activation(X @ W + b)."""

    def __init__(self, n_in: int, n_out: int, activation=relu):
        self.W = rng.normal(0, np.sqrt(2 / n_in), size=(n_in, n_out))   # small random weights
        self.b = np.zeros(n_out)
        self.activation = activation

    def forward(self, X):
        return self.activation(X @ self.W + self.b)

# A dataset no straight line can separate: points inside a circle vs outside
X = rng.uniform(-2, 2, size=(400, 2))
y = (np.sum(X ** 2, axis=1) < 1.5).astype(float).reshape(-1, 1)

net = [Dense(2, 16), Dense(16, 16), Dense(16, 1, activation=sigmoid)]
out = X
for layer in net:
    out = layer.forward(out)
    print(out.shape)            # (400, 16) -> (400, 16) -> (400, 1)
print("untrained accuracy:", ((out > 0.5) == y).mean())   # ~chance: weights are random
```
A `Dense(n_in, n_out)` layer has `n_in * n_out + n_out` parameters: 337 here. A 0.5B-parameter LLM has ~1.5 million times as many, each learned the same way.

**Common mistakes**
- Initialising all weights to zero: every neuron computes the same thing forever.
- Forgetting the activation between layers (your deep network silently becomes linear).

**Exercises**
1. Write `count_parameters(net)` and check it returns 337.
2. Replace the hidden activations with `lambda z: z`. Why can the network now only draw a straight boundary?

**Check yourself**
- What does a single neuron compute? Why are non-linear activations essential?

---

### Lesson 12: Backpropagation From Scratch

**Concepts**
- **Backpropagation** computes the gradient of the loss for *every* weight with the chain rule, from the loss backwards through the layers. The forward pass saves each layer's input and pre-activation value for this.
- Backwards through `Z = X @ W + b`: `dW = X.T @ dZ`, `db = dZ.sum(axis=0)`, and `dX = dZ @ W.T` is passed to the previous layer.
- Through ReLU the gradient passes where the input was positive: `dZ = dA * (Z > 0)`.
- Sigmoid + binary cross-entropy has the same shortcut as softmax + cross-entropy: `dZ = (p - y) / n`.

**Code: a complete trainable 2-layer network**
```python
import numpy as np

rng = np.random.default_rng(0)
X = rng.uniform(-2, 2, size=(400, 2))
y = (np.sum(X ** 2, axis=1) < 1.5).astype(float).reshape(-1, 1)
n = len(X)

def sigmoid(z):
    return 1 / (1 + np.exp(-z))

hidden = 16
W1 = rng.normal(0, np.sqrt(2 / 2), size=(2, hidden))
b1 = np.zeros((1, hidden))
W2 = rng.normal(0, np.sqrt(1 / hidden), size=(hidden, 1))
b2 = np.zeros((1, 1))
learning_rate = 0.5

for step in range(3001):
    # ---- forward pass (save intermediate values) ----
    Z1 = X @ W1 + b1           # (400, 16)
    A1 = np.maximum(0, Z1)     # ReLU
    Z2 = A1 @ W2 + b2          # (400, 1)
    p = sigmoid(Z2)
    loss = -np.mean(y * np.log(p + 1e-9) + (1 - y) * np.log(1 - p + 1e-9))

    # ---- backward pass (chain rule, last layer first) ----
    dZ2 = (p - y) / n
    dW2 = A1.T @ dZ2
    db2 = dZ2.sum(axis=0, keepdims=True)
    dA1 = dZ2 @ W2.T           # gradient flowing back into layer 1
    dZ1 = dA1 * (Z1 > 0)       # through ReLU
    dW1 = X.T @ dZ1
    db1 = dZ1.sum(axis=0, keepdims=True)

    # ---- gradient descent ----
    W1 -= learning_rate * dW1
    b1 -= learning_rate * db1
    W2 -= learning_rate * dW2
    b2 -= learning_rate * db2

    if step % 500 == 0:
        print(f"step {step:4d}  loss {loss:.4f}  accuracy {((p > 0.5) == y).mean():.3f}")
# Accuracy climbs from ~0.5 to ~0.99
```

**Gradient checking.** Always verify hand-written backprop numerically: nudge one weight and compare.
```python
def full_loss(W1_):
    p_ = sigmoid(np.maximum(0, X @ W1_ + b1) @ W2 + b2)
    return -np.mean(y * np.log(p_ + 1e-9) + (1 - y) * np.log(1 - p_ + 1e-9))

Z1 = X @ W1 + b1
p = sigmoid(np.maximum(0, Z1) @ W2 + b2)
dW1 = X.T @ ((((p - y) / n) @ W2.T) * (Z1 > 0))      # analytic, at the current weights

h = 1e-5
W1_plus, W1_minus = W1.copy(), W1.copy()
W1_plus[0, 3] += h
W1_minus[0, 3] -= h
print(dW1[0, 3], (full_loss(W1_plus) - full_loss(W1_minus)) / (2 * h))   # should agree closely
```
PyTorch does exactly this — record the forward pass, apply the chain rule backwards — automatically, for any model.

**Common mistakes**
- Shape errors. Rule: a gradient has the **same shape** as the thing it's the gradient of.
- Forgetting to divide by `n`, or a learning rate so high the loss becomes `nan`.

**Exercises**
1. Replace ReLU with tanh (derivative `1 - tanh(z) ** 2`). Which trains faster here?
2. Turn it into a 3-class priority classifier (Lesson 9 data, standardised): softmax output, `dZ2 = (probs - one_hot) / n`.

**Check yourself**
- Why does backprop go backwards? What is gradient checking for?

---

### Lesson 13: PyTorch Tensors and Autograd

**Concepts**
- A **tensor** is PyTorch's numpy array with two superpowers: it can live on a **GPU**, and it can **track operations** to compute gradients automatically (**autograd**).
- Mark parameters with `requires_grad=True`, compute a loss, call `loss.backward()`: every parameter's `.grad` is filled in. Gradients **accumulate**, so zero them before the next step.
- **Devices**: `"cuda"` (NVIDIA), `"mps"` (Apple Silicon), `"cpu"`. A model and its data must be on the same device.

**Code**
```python
import torch

a = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
print(a.shape, a.dtype, a @ a, a.sum(dim=0))   # like numpy; dim= instead of axis=
print(torch.randn(2, 3), a.unsqueeze(0).shape)

# Autograd: Lesson 3's example, done automatically
x, y = torch.tensor(2.0), torch.tensor(10.0)
w = torch.tensor(3.0, requires_grad=True)
loss = (w * x - y) ** 2
loss.backward()
print(w.grad)                  # tensor(-16.) — same as our hand calculation
w.grad.zero_()                 # reset before the next backward()

with torch.no_grad():          # no tracking: faster, less memory (evaluation, inference)
    print(w * x)

def pick_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")

device = pick_device()
big = torch.randn(1000, 1000, device=device)
result = big @ big                         # runs on the GPU if you have one
print(device, result.cpu().numpy().shape)  # move to CPU before converting to numpy
```

| dtype | Bytes per number | Use |
|---|---|---|
| `float32` | 4 | Default; small models |
| `float16` | 2 | Older GPUs (e.g. the T4); half the memory |
| `bfloat16` | 2 | Modern GPUs (A100, H100, RTX 30xx+); safer range than float16 |
| int8 / 4-bit | 1 / 0.5 | Quantised models for inference (Lesson 21) |

**Common mistakes**
- `Expected all tensors to be on the same device` → `.to(device)` both model and data.
- `.numpy()` on a GPU tensor or one requiring grad → use `.detach().cpu().numpy()`.

**Exercises**
1. Use autograd to check that the derivative of `torch.sigmoid` at 0 is 0.25.
2. Redo Lesson 4's line fit with tensors: `loss.backward()`, then update `w` and `b` inside `torch.no_grad()`, then zero the grads.

**Check yourself**
- What does `loss.backward()` do? Why wrap evaluation in `torch.no_grad()`?

---

### Lesson 14: Training in PyTorch

**Concepts**
- **`nn.Module`**: define layers in `__init__`, the computation in `forward`. PyTorch finds all parameters for you.
- **Losses**: `nn.MSELoss` (regression), `nn.BCEWithLogitsLoss` (binary), `nn.CrossEntropyLoss` (multi-class). The last two take raw **logits** — don't apply sigmoid/softmax yourself.
- **Optimizers** apply the update rule. **AdamW** adapts the step size per parameter; it's the default for transformers.
- **`Dataset` + `DataLoader`** handle batching and shuffling.
- **The training loop** is always: forward → loss → `zero_grad` → `backward` → `step`.

**Code**
```python
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset, random_split

device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
torch.manual_seed(0)

X = torch.rand(1000, 2) * 4 - 2                      # the circles problem again
y = ((X ** 2).sum(dim=1) < 1.5).float().unsqueeze(1)
train_ds, val_ds = random_split(TensorDataset(X, y), [800, 200], generator=torch.Generator().manual_seed(0))
train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=200)

class MLP(nn.Module):
    def __init__(self, hidden: int = 16):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, 1),          # a raw logit; the loss applies sigmoid internally
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

model = MLP().to(device)
loss_fn = nn.BCEWithLogitsLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-2)

for epoch in range(1, 31):
    model.train()                              # training mode (matters for dropout etc.)
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        loss = loss_fn(model(xb), yb)          # 1. forward  2. loss
        optimizer.zero_grad()                  # 3. clear old gradients
        loss.backward()                        # 4. backprop
        optimizer.step()                       # 5. update weights

    model.eval()
    with torch.no_grad():
        correct = sum(((model(xb.to(device)) > 0).float() == yb.to(device)).sum().item()
                      for xb, yb in val_loader)
    if epoch % 5 == 0:
        print(f"epoch {epoch:2d}  last batch loss {loss.item():.4f}  val acc {correct / len(val_ds):.3f}")

torch.save(model.state_dict(), "mlp.pt")
reloaded = MLP()
reloaded.load_state_dict(torch.load("mlp.pt", map_location="cpu", weights_only=True))
```

**A custom `Dataset`** for your own data:
```python
import torch
from torch.utils.data import Dataset

from task_data import make_tasks

class TaskDataset(Dataset):
    FEATURES = ["hours", "days_until_due", "from_manager", "blocking_others"]

    def __init__(self, df):
        X = df[self.FEATURES].astype(float).to_numpy()
        # (A shortcut for the demo: in a real project compute mean/std on the training split only)
        self.X = torch.tensor((X - X.mean(axis=0)) / X.std(axis=0), dtype=torch.float32)
        self.y = torch.tensor(df["priority"].to_numpy() - 1)   # classes 0, 1, 2

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, i):
        return self.X[i], self.y[i]

ds = TaskDataset(make_tasks().dropna())
print(ds[0], len(ds))
```
**Big models change nothing conceptually.** Part F's trainer runs this exact loop plus conveniences: mixed precision, gradient accumulation (several small batches per `step()`), learning-rate schedules, checkpoints and logging.

**Common mistakes**
- Applying sigmoid/softmax in `forward` *and* using a with-logits loss (applied twice).
- `CrossEntropyLoss` needs integer class indices starting at 0 (dtype `long`), not 1/2/3 or one-hot.

**Exercises**
1. Train a 3-class priority classifier on `TaskDataset` with `nn.CrossEntropyLoss`. Compare with Lesson 9.
2. Add **early stopping**: stop when validation accuracy hasn't improved for 5 epochs; keep the best weights.

**Check yourself**
- List the five lines of the training loop in order. Why does `CrossEntropyLoss` take logits?

---

## Part D: How Language Models Work

An LLM is a neural network whose input is a sequence of tokens and whose output, at every position, is a softmax over the vocabulary predicting the *next* token. One forward pass:

```
"Email the client"                 text
  -> [token ids]                   tokenizer          (Lesson 15)
  -> one vector per token          embedding lookup   (Lesson 16)
  -> N x transformer blocks        attention + MLP    (Lesson 17)
  -> logits over the vocabulary    final linear layer
  -> softmax at the last position  next-token probabilities (Lesson 18)
```

### Lesson 15: Tokenization

**Concepts**
- A **tokenizer** splits text into **tokens** (words, word pieces, characters) and maps each to an ID in a fixed **vocabulary** (typically 32k–260k entries).
- Most use **BPE (byte-pair encoding)**: start from bytes and repeatedly merge the most frequent adjacent pair. Common words become one token; rare words split into pieces; nothing is ever "unknown".
- English rule of thumb: **1 token ≈ 4 characters ≈ 0.75 words**. Code, numbers and other languages use more. API prices and context limits are in tokens.
- **Chat templates** wrap each message in special tokens (`<|im_start|>user ... <|im_end|>`). Each chat model was trained with one specific template; the wrong one quietly ruins its output.

**Code: BPE in 20 lines**
```python
from collections import Counter

def most_common_pair(tokens: list[str]) -> tuple[str, str]:
    return Counter(zip(tokens, tokens[1:])).most_common(1)[0][0]

def merge(tokens: list[str], pair: tuple[str, str]) -> list[str]:
    out, i = [], 0
    while i < len(tokens):
        if i < len(tokens) - 1 and (tokens[i], tokens[i + 1]) == pair:
            out.append(tokens[i] + tokens[i + 1])
            i += 2
        else:
            out.append(tokens[i])
            i += 1
    return out

tokens = list("the task list, the tasks, the test task")
for step in range(8):
    pair = most_common_pair(tokens)
    tokens = merge(tokens, pair)
    print(f"merge {step}: {pair!r:14} -> {len(tokens)} tokens")
print(tokens)
# Frequent pairs merge first: ' t', 'he', 'as'+'k' -> 'ask', then 'he t'+'ask' -> 'he task'.
# Common chunks of text become single tokens; rare ones stay as pieces.
```

**Code: a real tokenizer and chat template**
```python
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")   # downloads a few MB once

text = "Remind me to email the client tomorrow at 9am."
ids = tok.encode(text)
print(ids, [tok.decode([i]) for i in ids])
print(len(text), "chars ->", len(ids), "tokens")
print(tok.tokenize("unbelievably"), tok.tokenize("2026-11-04"))

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What's on my list today?"},
]
print(tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
# <|im_start|>system
# You are a helpful assistant.<|im_end|>
# <|im_start|>user
# What's on my list today?<|im_end|>
# <|im_start|>assistant
```
Tokenization explains odd LLM behaviour: counting letters in "strawberry" is hard when the model sees a few tokens, not letters, and long-number arithmetic suffers when digits are chunked unevenly.

**Common mistakes**
- Using one model's tokenizer with another model. Load both from the same model ID.
- Building chat prompts with string concatenation. Use `apply_chat_template`.

**Exercises**
1. Tokenize the same paragraph in English and another language you know. Compare token counts.
2. Extend the BPE code to record its merges, then write `encode(text, merges)` that applies them in order to new text.

**Check yourself**
- Why split rare words into pieces instead of using an "unknown" token? What's a chat template?

---

### Lesson 16: Embeddings

**Concepts**
- An **embedding** is a learned vector for a token. The embedding layer is just a `(vocab_size, d_model)` matrix; looking up token 42 means taking row 42.
- Training arranges the vectors so tokens used in similar ways end up **close together** (high cosine similarity, Lesson 1).
- Inside the transformer each token's vector is updated with information from the others, so by the last layer it represents the token *in context* ("bank" by a river vs "bank" with money).
- **Sentence embeddings** — one vector per text — power semantic search and RAG.

**Code**
```python
import torch
import torch.nn.functional as F
from torch import nn
from transformers import AutoModel, AutoTokenizer

emb = nn.Embedding(10, 4)                        # vocabulary of 10, vectors of size 4
print(torch.equal(emb(torch.tensor([3]))[0], emb.weight[3]))   # True — literally row 3

name = "sentence-transformers/all-MiniLM-L6-v2"   # small (90 MB), Apache-2.0
tok = AutoTokenizer.from_pretrained(name)
model = AutoModel.from_pretrained(name)

sentences = [
    "Email the client about the invoice",
    "Send the customer a message regarding payment",
    "Book a dentist appointment",
    "Schedule a check-up with the doctor",
]
batch = tok(sentences, padding=True, truncation=True, return_tensors="pt")
with torch.no_grad():
    hidden = model(**batch).last_hidden_state          # (4 sentences, tokens, 384)

mask = batch["attention_mask"].unsqueeze(-1).float()   # ignore padding when averaging
vectors = F.normalize((hidden * mask).sum(dim=1) / mask.sum(dim=1), dim=1)
print((vectors @ vectors.T).round(decimals=2))
# Pairs 0&1 and 2&3 score high even though they share few words
```

**Common mistakes**
- Comparing embeddings from two different models — their spaces are unrelated.
- Averaging over padding tokens (always use the attention mask).

**Exercises**
1. Build a tiny "semantic task search": embed your real task titles and rank them against a query like "money stuff".

**Check yourself**
- What is an embedding layer, mechanically? Why do similar words end up close together?

---

### Lesson 17: Attention and the Transformer

**Concepts**
- **The problem:** to continue "Remind me to email **her** about **it**", the model must link "her" and "it" to earlier words. Each token needs to *look at* other tokens and pull in what's relevant.
- **Self-attention** gives every token three vectors, each its embedding times a learned matrix:
  - **Query (Q)**: "what am I looking for?"
  - **Key (K)**: "what do I contain?"
  - **Value (V)**: "what do I pass on if chosen?"
- Each query is dot-producted with every key (similarity!), scaled by `sqrt(d)`, softmaxed into weights summing to 1, and used to average the values:
  ```
  Attention(Q, K, V) = softmax(Q @ K.T / sqrt(d)) @ V
  ```
- A **causal mask** stops tokens looking at the future: future scores are set to `-inf` before softmax, so their weight is 0.
- **Multi-head attention** runs several smaller attentions in parallel, each free to learn a different relationship. **Position** is mixed in separately (modern models use RoPE), because attention alone ignores word order.

**Code: attention in numpy**
```python
import numpy as np

rng = np.random.default_rng(0)

def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)

def attention(Q, K, V, causal=False):
    d = Q.shape[-1]
    scores = Q @ K.T / np.sqrt(d)                     # (seq, seq): every query vs every key
    if causal:
        future = np.triu(np.ones(scores.shape, dtype=bool), k=1)
        scores = np.where(future, -np.inf, scores)    # block looking ahead
    weights = softmax(scores, axis=-1)                # each row sums to 1
    return weights @ V, weights

tokens = ["email", "the", "client", "tomorrow"]
X = rng.normal(size=(4, 8))                           # 4 tokens, 8-dim embeddings
Wq, Wk, Wv = (rng.normal(size=(8, 4)) for _ in range(3))   # learned in a real model
Q, K, V = X @ Wq, X @ Wk, X @ Wv

out, weights = attention(Q, K, V, causal=True)
print(out.shape)                                      # (4, 4): one updated vector per token
for name, row in zip(tokens, weights):
    print(f"{name:>9} attends to", dict(zip(tokens, row.round(2).tolist())))
# Upper triangle is 0: "email" sees only itself; "tomorrow" sees all four
```
PyTorch's fast built-in gives the same result: `torch.nn.functional.scaled_dot_product_attention(q, k, v, is_causal=True)`.

**A transformer block** — Qwen2.5-0.5B stacks 24 of these:
```
x = x + MultiHeadAttention(Norm(x))   # tokens exchange information
x = x + MLP(Norm(x))                  # each token "thinks" on its own
```
The `x + ...` **residual connections** let each block add a refinement rather than replace `x`, which makes deep stacks trainable. **Norm** keeps numbers in a stable range. In PyTorch:
```python
import torch
import torch.nn.functional as F
from torch import nn

class Block(nn.Module):
    def __init__(self, d_model: int = 64, n_heads: int = 4):
        super().__init__()
        self.n_heads = n_heads
        self.norm1 = nn.LayerNorm(d_model)
        self.qkv = nn.Linear(d_model, 3 * d_model)
        self.proj = nn.Linear(d_model, d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.mlp = nn.Sequential(nn.Linear(d_model, 4 * d_model), nn.GELU(), nn.Linear(4 * d_model, d_model))

    def forward(self, x: torch.Tensor) -> torch.Tensor:      # x: (batch, seq, d_model)
        B, T, D = x.shape
        q, k, v = self.qkv(self.norm1(x)).split(D, dim=-1)
        # split into heads: (batch, heads, seq, d_head)
        q, k, v = (t.view(B, T, self.n_heads, D // self.n_heads).transpose(1, 2) for t in (q, k, v))
        att = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = x + self.proj(att.transpose(1, 2).reshape(B, T, D))   # merge heads; residual
        return x + self.mlp(self.norm2(x))                         # residual

block = Block()
print(block(torch.randn(2, 10, 64)).shape)       # torch.Size([2, 10, 64]) — same shape out
```
A full GPT-style model is: embedding → N blocks → final norm → linear layer to vocabulary size. The magic is the scale of data and training, not complicated code. And because the score matrix is `seq × seq`, doubling the context makes attention roughly 4× the work — one reason long contexts cost more.

**Common mistakes**
- Dropping the `sqrt(d)` scaling: softmax becomes nearly one-hot and gradients vanish.
- Treating attention weights as an "explanation" of the model. They're one internal signal among many.

**Exercises**
1. Set `Q[3] = K[0] * 5` and rerun. Check that "tomorrow" now attends almost entirely to "email".
2. Count the parameters of `Block(d_model=896, n_heads=14)` and multiply by 24. How close to 0.5B do you get?

**Check yourself**
- In one sentence each: what are queries, keys and values? What does the causal mask do?

---

### Lesson 18: Next-Token Prediction and How Models Are Trained

**Concepts**
- An LLM is trained on one task: **predict the next token**, with cross-entropy loss (Lesson 5) at every position of trillions of tokens.
- **Generation** is a loop: run the model, get probabilities for the next token, pick one (greedy, or sample with temperature/top-p), append, repeat until an end token.
- The model has no memory between calls; a "conversation" is the full history re-sent each time, as you did with the API.

| Stage | Data | What it teaches |
|---|---|---|
| **Pretraining** | Trillions of tokens of web, books, code | Language, facts, patterns. Produces a *base model* that continues text but doesn't follow instructions |
| **Instruction tuning (SFT)** | Curated (prompt, ideal response) conversations | Following instructions, chat format, tool calling — you'll do this in miniature in Part F |
| **Preference tuning (RLHF, DPO…)** | Responses ranked by humans or AI | Helpfulness, honesty, harmlessness, style |

So `Qwen2.5-0.5B` is a base model (it continues text) while `Qwen2.5-0.5B-Instruct` has been instruction- and preference-tuned (it answers). You almost always want `-Instruct` / `-Chat` / `-it` versions. And models **hallucinate** because the objective rewards *plausible* next tokens, not *true* ones; tuning and tool use reduce this but don't remove it.

**Code: the next-token distribution, and your own generation loop**
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

name = "Qwen/Qwen2.5-0.5B"                           # a BASE model (~1 GB download)
tok = AutoTokenizer.from_pretrained(name)
model = AutoModelForCausalLM.from_pretrained(name).eval()

inputs = tok("My most urgent task this week is to finish the", return_tensors="pt")
with torch.no_grad():
    logits = model(**inputs).logits                  # (1, seq_len, vocab_size)
probs = torch.softmax(logits[0, -1], dim=-1)         # distribution after the LAST token
top = torch.topk(probs, 5)
for p, i in zip(top.values, top.indices):
    print(f"{tok.decode(int(i))!r:>14}  {p.item():.3f}")

def generate(prompt: str, max_new_tokens: int = 20, temperature: float = 0.8) -> str:
    ids = tok(prompt, return_tensors="pt")["input_ids"]
    for _ in range(max_new_tokens):
        with torch.no_grad():
            next_logits = model(input_ids=ids).logits[:, -1, :]
        if temperature == 0:
            next_id = next_logits.argmax(dim=-1, keepdim=True)                    # greedy
        else:
            next_id = torch.multinomial(torch.softmax(next_logits / temperature, dim=-1), 1)
        ids = torch.cat([ids, next_id], dim=1)
        if next_id.item() == tok.eos_token_id:
            break
    return tok.decode(ids[0], skip_special_tokens=True)

print(generate("Three habits for a productive workday are", temperature=0))

```
Real libraries add a **KV cache** (keeping earlier tokens' keys and values) so they don't recompute the whole sequence each step — why `model.generate()` is far faster than this loop. Passing `labels=input_ids` to the model returns the average next-token cross-entropy, the number pretraining minimises; `exp(loss)` is the **perplexity**.

**Common mistakes**
- Chatting with a base model and wondering why it rambles or continues your question.
- Comparing loss/perplexity across models with different tokenizers.

**Exercises**
1. Add **top-k** sampling to `generate`: keep only the k highest logits (the rest become `-inf`) before softmax.
2. Compare `model(**batch, labels=batch["input_ids"]).loss` for a sentence and the same words shuffled. Explain the difference.

**Check yourself**
- What single task is pretraining? What do instruction tuning and preference tuning each add?

---

## Part E: Working with Open Models

**Open-weight models** (Qwen, Llama, Gemma, Mistral, Phi, SmolLM…) can be downloaded and run on your own hardware.

| | Hosted API (Claude etc.) | Open model on your hardware |
|---|---|---|
| Quality | Best available | Good to very good; small models are clearly weaker |
| Cost | Pay per token | Hardware and electricity; no per-token fee |
| Privacy / offline | Data goes to a provider / no | Data stays on your machine / yes |
| Customisation | Prompts, tools, RAG | All of those **plus** fine-tuning the weights |
| Maintenance | The provider's problem; improves for free | Yours |

### Lesson 19: Hugging Face: Pipelines, Auto Classes and the Hub

**Concepts**
- **The Hugging Face Hub** hosts hundreds of thousands of models and datasets, named `organisation/name` (e.g. `Qwen/Qwen2.5-0.5B-Instruct`). Each has a **model card**: purpose, training, **licence**, limitations. Read it first.
- `transformers` offers **`pipeline(...)`** (one line, good defaults) and **`AutoTokenizer` / `AutoModel...`** (full control; used for fine-tuning).
- Downloads are cached (by default under `~/.cache/huggingface`); the second load is instant.

**Code: pipelines**
```python
from transformers import pipeline

# Chat with a small instruct model
chat = pipeline("text-generation", model="Qwen/Qwen2.5-0.5B-Instruct")
messages = [
    {"role": "system", "content": "You are a concise productivity assistant."},
    {"role": "user", "content": "Give me three tips for planning my week."},
]
out = chat(messages, max_new_tokens=150)
print(out[0]["generated_text"][-1]["content"])    # the new assistant message
```

**Code: Auto classes (what pipelines do internally)**
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
model_id = "Qwen/Qwen2.5-0.5B-Instruct"
tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, dtype="auto").to(device)
# (Older transformers versions call the dtype argument torch_dtype.)

messages = [{"role": "user", "content": "Turn this into a short task title: I really need to call the bank about my card"}]
prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tok(prompt, return_tensors="pt", add_special_tokens=False).to(device)   # template has them already

with torch.no_grad():
    output_ids = model.generate(**inputs, max_new_tokens=40, do_sample=False)   # greedy

new_tokens = output_ids[0][inputs["input_ids"].shape[1]:]     # drop the prompt
print(tok.decode(new_tokens, skip_special_tokens=True))
print(model.num_parameters() / 1e6, "million parameters")
```

**Gated models** (Llama, Gemma) need you to accept the licence on the website and log in with an access token (Settings → Access Tokens). With current `huggingface_hub` the CLI is `hf` (older versions: `huggingface-cli login`):
```bash
hf auth login
```

**Choosing a model:** filter by task, check the **licence**, the **parameter count** (does it fit? Lesson 21), that it's an **instruct** version, and the date — newer small models often beat older big ones.

**Common mistakes**
- `trust_remote_code=True` runs Python from the model's repo. Only with sources you trust.
- Decoding prompt + answer together and thinking the model repeated your question. Slice off the prompt.

**Exercises**
1. Use `pipeline("zero-shot-classification", model="facebook/bart-large-mnli")` with `candidate_labels=["work", "home", "finance", "health"]` to label 20 of your real tasks. How many are right?
2. Read three model cards; note licence, parameter count, training data and stated limitations.

**Check yourself**
- When would you use `pipeline` vs the Auto classes? Why `do_sample=False` for JSON?

---

### Lesson 20: Hugging Face Datasets

**Concepts**
- `datasets` loads data from the Hub or local files (JSON Lines, CSV, Parquet) into a fast `Dataset` table. `.map()` transforms rows, `.filter()` drops them, `.train_test_split()` splits.
- **JSON Lines** (`.jsonl`, one JSON object per line) is the standard fine-tuning format.

**Code**
```python
import json
from pathlib import Path

from datasets import Dataset, load_dataset

rows = [
    {"text": "Email the client", "label": "work"},
    {"text": "Buy groceries", "label": "home"},
    {"text": "Pay the electricity bill", "label": "finance"},
    {"text": "Prepare slides for Monday", "label": "work"},
]
Path("data").mkdir(exist_ok=True)
with open("data/tasks.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")

ds = load_dataset("json", data_files="data/tasks.jsonl", split="train")   # or Dataset.from_list(rows)
print(ds, ds[0])
work_only = ds.filter(lambda r: r["label"] == "work")
with_len = ds.map(lambda r: {"n_chars": len(r["text"])})
splits = ds.train_test_split(test_size=0.25, seed=42)
print(work_only["text"], with_len["n_chars"], splits["train"].num_rows)

```

**Fine-tuning data formats** understood by `trl` (Lesson 24):

| Format | Each row | Use |
|---|---|---|
| Language modelling | `{"text": "..."}` | Continued pretraining on raw text |
| Conversational | `{"messages": [{"role": ..., "content": ...}, ...]}` | Chat fine-tuning |
| Prompt–completion | `{"prompt": [messages...], "completion": [{"role": "assistant", ...}]}` | Train on the answer only — the capstone's format |

**Common mistakes**
- A column whose type varies between rows (string here, dict there). Arrow needs consistent types; serialise irregular objects to JSON strings.

**Exercises**
1. Turn your real Work Organizer tasks into a `Dataset` and split it 80/20 with a seed.

**Check yourself**
- Which format trains only on the assistant's answer?

---

### Lesson 21: Running Models Locally: Ollama, llama.cpp and Quantization

**Concepts**
- To *use* models on a laptop you rarely call `transformers` directly:
  - **llama.cpp**: a fast C++ inference engine for CPUs, Apple Silicon and GPUs, using the **GGUF** file format.
  - **Ollama**: a friendly app built on llama.cpp — one command to download and run a model, plus a local HTTP API at `http://localhost:11434`.
- **Quantization** stores weights in fewer bits (8, 5, 4…) instead of 16. A 4-bit model is about **4× smaller and faster** for a small quality loss — what makes 7–8B models practical on a laptop.
- **Memory rule of thumb:** `RAM ≈ parameters × bits per weight / 8 + 1–2 GB` for context and runtime.

**Quantization in numpy**
```python
import numpy as np

rng = np.random.default_rng(0)
w = rng.normal(0, 0.02, size=4096).astype(np.float32)   # one row of a weight matrix

scale = np.abs(w).max() / 127                            # 8-bit: map [-max, max] onto [-127, 127]
w8 = np.round(w / scale).astype(np.int8).astype(np.float32) * scale
print("int8 error:", np.abs(w - w8).mean())

scale4 = np.abs(w).max() / 7                             # 4-bit: only 16 levels, [-8, 7]
w4 = np.clip(np.round(w / scale4), -8, 7) * scale4
print("4-bit error:", np.abs(w - w4).mean())

# Real formats quantize small BLOCKS (e.g. 32 weights), each with its own scale,
# so one outlier doesn't wreck everyone else's precision
blocks = w.reshape(-1, 32)
scales = np.abs(blocks).max(axis=1, keepdims=True) / 7
print("4-bit blocked error:", np.abs(blocks - np.clip(np.round(blocks / scales), -8, 7) * scales).mean())
```

| GGUF type | ≈ bits/weight | Quality |
|---|---|---|
| `F16` / `BF16` | 16 | Original |
| `Q8_0` | 8.5 | Practically lossless — fine for small models |
| `Q6_K` / `Q5_K_M` | 6.6 / 5.7 | Excellent / very good |
| `Q4_K_M` | 4.8 | Good — the popular laptop default |
| `Q3_K_M`, `Q2_K` | 3.9, 3.4 | Noticeably worse; last resort |

**Hardware requirements (inference at `Q4_K_M`, modest context)**

| Model size | Examples | RAM / VRAM | Runs well on |
|---|---|---|---|
| 0.5B–1.5B | Qwen2.5-0.5B/1.5B, SmolLM2-1.7B, Llama 3.2 1B | 1–2 GB | Any laptop |
| 3B–4B | Llama 3.2 3B, Qwen2.5-3B, Phi-4-mini | 3–4 GB | Any modern laptop |
| 7B–9B | Qwen2.5-7B, Llama 3.1 8B, Gemma 2 9B | 5–7 GB | 16 GB Mac; GPU with 8 GB+ |
| 12B–14B | Qwen2.5-14B, Gemma 3 12B | 9–11 GB | 16–32 GB Mac; 12–16 GB GPU |
| 27B–32B | Qwen2.5-32B, Gemma 3 27B | 18–22 GB | 32 GB+ Mac; 24 GB GPU |
| 70B | Llama 3.3 70B | 40–48 GB | 64 GB+ Mac; two 24 GB GPUs |

On Apple Silicon the GPU shares system RAM, so a 32 GB Mac runs models a 12 GB gaming GPU can't (more slowly). CPU-only, expect a few tokens per second at 7B. Speed is limited mostly by **memory bandwidth**; long contexts add memory on top.

**Ollama.** Install from ollama.com, or on Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```
```bash
ollama pull qwen2.5:1.5b
```
```bash
ollama run qwen2.5:1.5b
```
(`/bye` exits; `ollama list` shows downloaded models.) Call it from Python:
```python
import requests

response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "qwen2.5:1.5b",
        "messages": [{"role": "user", "content": "Suggest a title for a task about renewing my passport."}],
        "stream": False,
        "options": {"temperature": 0},
    },
    timeout=120,
)
response.raise_for_status()
print(response.json()["message"]["content"])
```
Ollama also serves an **OpenAI-compatible** endpoint at `http://localhost:11434/v1`, accepts a `tools` list in `/api/chat` for tool-capable models such as `qwen2.5`, and has an official Python package (`pip install ollama`).

**llama.cpp directly** (Homebrew shown; see its README for other platforms):
```bash
brew install llama.cpp
```
```bash
llama-cli -hf bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M
```
```bash
llama-server -hf bartowski/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M --port 8080
```
The server gives you a web UI and an OpenAI-compatible API. Use Ollama for convenience, llama.cpp for full control (exact quantization, GPU offload). You'll also hear of **LM Studio** (desktop GUI), **vLLM** / **SGLang** (high-throughput GPU servers) and **MLX** (fast on Macs).

**Common mistakes**
- Pulling a model too big for your RAM: the machine swaps to disk and crawls. Check the table.
- Exposing Ollama beyond `localhost` without authentication in front of it.

**Exercises**
1. Send five Work Organizer requests to `qwen2.5:0.5b`, `qwen2.5:1.5b` and (if it fits) `qwen2.5:7b`. Compare speed (`ollama run --verbose` prints tokens/second) and quality.
2. Estimate the RAM a 14B model needs at `Q8_0` and at `Q4_K_M`.

**Check yourself**
- What do you trade for quantization's smaller size? How do Ollama and llama.cpp relate?

---

## Part F: Fine-Tuning

**Fine-tuning** continues training a pretrained model on your own examples so it gets better at one specific job. It's the most powerful customisation you have — and the most overused.

### Lesson 22: When Fine-Tuning Is Worth It

**Concepts**
- Try, in order, and stop when one is good enough: **prompting → few-shot examples → RAG/tools → fine-tuning**.
- Fine-tuning teaches **behaviour and format** well (always emit this JSON, use our labels, our tone). It's a **poor way to add knowledge** — facts change, and the model blends and misremembers them. Use RAG for knowledge.
- The classic reason to fine-tune a *small* model: match a big model **on one narrow task**, cheaper, faster, privately and offline.

| Problem | Try first |
|---|---|
| "It doesn't know our documents" | RAG |
| "Wrong output format" / "wrong tool chosen" | Better prompt, tool descriptions, structured outputs, few-shot examples |
| "Must run offline / on-device / free" | Small open model + fine-tuning |
| "Millions of identical calls; huge bill" | Fine-tune a small model on the big model's outputs (*distillation*) |
| "Our prompt is mostly examples" | Fine-tuning bakes them into the weights |
| "General quality isn't good enough" | A bigger model — fine-tuning won't make a small model generally smarter |

**Costs people forget:** collecting and cleaning data (by far the biggest), evaluation, retraining when requirements change, hosting — and missing out on the provider's free model upgrades.

**Exercises**
1. For each weakness of your assistant, pick the tool from the table you'd try first, and say why.

**Check yourself**
- Why is fine-tuning a poor way to teach new facts? Name two good reasons to fine-tune a small model.

---

### Lesson 23: LoRA and QLoRA

**Concepts**
- **Full fine-tuning** updates every weight: roughly 16 bytes per parameter with AdamW and mixed precision (~24 GB for a 1.5B model), plus a full model copy per fine-tune.
- **LoRA** freezes the original weights and learns a small *update* for chosen weight matrices: two thin matrices `B` (`d × r`) and `A` (`r × k`) with a small **rank** `r` (8–64):
  ```
  W_effective = W + (alpha / r) * B @ A
  ```
  `B` starts at zero, so training starts from exactly the original model. You train ~1–2% of the parameters, need far less memory, and the **adapter** is megabytes, not gigabytes. Adapters can be swapped at runtime or **merged** into the base weights.
- **QLoRA** loads the frozen base model in **4-bit** and trains LoRA adapters on top in 16-bit, so a 7–8B model fine-tunes on one 16 GB GPU. Needs an NVIDIA GPU (`bitsandbytes`).

**Code: the idea in numpy, then with `peft`**
```python
import numpy as np

rng = np.random.default_rng(0)
d, k, r, alpha = 1024, 1024, 8, 16
W = rng.normal(0, 0.02, size=(d, k))      # frozen pretrained weight
A = rng.normal(0, 0.01, size=(r, k))      # trainable
B = np.zeros((d, r))                      # trainable, starts at zero
x = rng.normal(size=(1, k))
print(np.allclose(x @ (W + (alpha / r) * B @ A).T, x @ W.T))   # True: unchanged at the start
print("full:", d * k, " LoRA:", A.size + B.size)                # 1,048,576 vs 16,384 (1.6%)
```
```python
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
config = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                    target_modules="all-linear", task_type="CAUSAL_LM")
peft_model = get_peft_model(model, config)
peft_model.print_trainable_parameters()   # roughly 9M trainable of ~500M (under 2%)
```

| `LoraConfig` | Typical | Meaning |
|---|---|---|
| `r` | 8–32 | Rank: more capacity, more overfitting risk on small data |
| `lora_alpha` | `r` to `2 * r` | Scale of the update |
| `lora_dropout` | 0–0.1 | Regularisation |
| `target_modules` | `"all-linear"` | Which layers get adapters; all linear layers works best |

**QLoRA loading** (NVIDIA only; `pip install bitsandbytes`):
```python
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",            # 4-bit format designed for normally distributed weights
    bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
    bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct", quantization_config=bnb_config, device_map="auto")
print(model.get_memory_footprint() / 1e9, "GB")   # ~5 GB instead of ~15 GB
```
Pass this model and a `LoraConfig` to the trainer exactly as in the next lesson. The capstone's 0.5B model fits easily with plain LoRA.

| Model | Full fine-tune | LoRA (16-bit base) | QLoRA (4-bit base) |
|---|---|---|---|
| 0.5B | ~8 GB | ~3 GB | ~2 GB |
| 1.5B | ~24 GB | ~6 GB | ~4 GB |
| 7–8B | ~120 GB | ~20 GB | ~8–10 GB |

(Rough; depends heavily on sequence length and batch size.)

**Common mistakes**
- Rank too high on a few hundred examples — the adapter memorises them. Start with 8–16.
- Merging an adapter into a 4-bit model. Load the base model unquantized, then merge.

**Exercises**
1. Compute the LoRA parameter count for `r = 4, 16, 64` on a `4096 × 4096` matrix, as a percentage of the full matrix.

**Check yourself**
- Why does LoRA start with `B` = 0? What does QLoRA add?

---

### Lesson 24: Fine-Tuning with peft and trl

**Concepts**
- **SFT (supervised fine-tuning)** trains on (prompt, ideal response) pairs with Lesson 18's next-token loss.
- `trl`'s **`SFTTrainer`** wraps Part C's loop: applies the chat template, tokenizes, adds LoRA if given a `peft_config`, and handles batching, mixed precision, evaluation and checkpoints.
- With prompt–completion data, the loss is computed **on the completion only**: the model learns to *answer* your system prompt, not to write it.
- **Data quality beats quantity.** 300 clean, consistent, varied examples beat 3,000 sloppy ones; every inconsistency gets learned faithfully.

**Preparing a dataset**
1. Fix the exact output format first. Every example must follow it perfectly.
2. Cover every tool and argument, the edge cases, and "none of the above".
3. Vary phrasing, length, typos and word order — small models over-learn surface patterns.
4. Use the **same system prompt** at training and inference time.
5. Deduplicate, then split train/validation/test; keep some *phrasings* only in the test set.
6. Read 50 random examples by eye before training. You will find bugs.

Examples can come from real logs (with consent), by hand, from templates, or **generated by a stronger model** — check that provider's terms on training other models with its outputs.

**One training example** (one line in the `.jsonl` file):
```json
{"prompt": [{"role": "system", "content": "You convert a user's message into exactly ONE Work Organizer tool call.\nToday is 2026-11-04 (Wednesday). ..."}, {"role": "user", "content": "remind me to call the dentist tomorrow, it's urgent"}], "completion": [{"role": "assistant", "content": "{\"tool\": \"add_task\", \"arguments\": {\"title\": \"Call the dentist\", \"priority\": 1, \"due\": \"2026-11-05\", \"tags\": []}}"}]}
```

**The core training code** (the capstone's `train.py` is the complete, GPU-aware version):
```python
from datasets import load_dataset
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

ds = load_dataset("json", data_files={"train": "data/train.jsonl", "validation": "data/val.jsonl"})
trainer = SFTTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",          # a model ID or an already-loaded model
    train_dataset=ds["train"],
    eval_dataset=ds["validation"],
    peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear", task_type="CAUSAL_LM"),
    args=SFTConfig(output_dir="outputs/demo", num_train_epochs=3, per_device_train_batch_size=8,
                   learning_rate=2e-4, eval_strategy="epoch", logging_steps=10, report_to="none"),
)
trainer.train()
trainer.save_model("outputs/demo")              # saves just the LoRA adapter
```

| `SFTConfig` | Start with (LoRA, a few hundred examples) | Notes |
|---|---|---|
| `num_train_epochs` | 2–4 | More on tiny data = memorisation; watch `eval_loss` |
| `learning_rate` | `1e-4`–`2e-4` | LoRA tolerates higher rates than full fine-tuning (`1e-5`–`2e-5`) |
| `per_device_train_batch_size` / `gradient_accumulation_steps` | 8 / 2 | Effective batch = product; lower the first if out of memory |
| `lr_scheduler_type`, `warmup_steps` | `"cosine"`, ~5–10% of steps | Gentle start, smooth decay |
| `max_length` | Longest example + margin | Longer examples are truncated |
| `bf16` / `fp16` | `bf16=True` on modern GPUs; `fp16=True` on a T4 | Mixed precision: faster, less memory |

**Reading the log:** `loss` should fall then flatten. `eval_loss` should fall too; if it **rises** while `loss` keeps falling, you're overfitting — fewer epochs, lower rank, or more varied data. `mean_token_accuracy` is nice to watch but no substitute for a real evaluation.

The saved adapter loads with `peft.AutoPeftModelForCausalLM.from_pretrained(...)`; calling `.merge_and_unload()` on it bakes LoRA into the weights and returns a normal standalone model (the capstone's `merge.py`).

**Common mistakes**
- Different prompts at training and inference (missing date line, different system prompt or chat template).
- Judging by a handful of outputs. Small models can look perfect on 5 examples and fail on 20% of the rest.
- Out of GPU memory: lower the batch size and raise gradient accumulation, shorten `max_length`, or use QLoRA.

**Exercises**
1. Train for 1, 3 and 8 epochs and compare training and validation loss. Which overfits?

**Check yourself**
- What does completion-only loss do, and why? What does `merge_and_unload()` produce?

---

### Lesson 25: Evaluating a Fine-Tuned Model

**Concepts**
- **Loss is not the goal.** The goal is "the assistant does the right thing". Measure that on a **held-out test set** the model never trained on.
- Structured outputs can be scored exactly and automatically:
  - **Valid JSON rate** — could we parse it?
  - **Tool accuracy** — right tool?
  - **Exact match** — right tool *and* every argument (after normalising capitalisation, tag order, etc.)?
  - **Per-field accuracy** — which arguments go wrong: titles, dates, priorities?
- **Compare against baselines**: the untrained base model with the same prompt, and the hosted model you use today. Keep a fine-tune only if it wins on something you care about (accuracy, cost, speed, privacy).
- **Error analysis**: read the failures and group them ("relative dates", "missing tags"). The groups tell you what data to add.
- **Catastrophic forgetting**: narrow fine-tuning can make a model worse at everything else. Fine for a single-purpose model — just don't chat with it.
- For open-ended text with no exact answer, use human ratings or an **LLM-as-judge** with a clear rubric (and spot-check the judge).

The capstone's `evaluate.py` implements all four scores in about 20 lines: parse the JSON, *normalise* both sides (lower-case titles, sort tags), then compare tools, whole calls, and each field.

**Evaluation hygiene**
- Greedy decoding (`do_sample=False` / temperature 0) for repeatable results.
- Every model gets the exact same test set and prompt.
- Report the test-set size: on 80 examples, a few points' difference between models is often noise.
- Never add test examples to training "to fix them". Add *similar new* examples; leave the test set alone.

**Exercises**
1. Add a confusion table to the capstone evaluator: when the gold tool is `delete_task`, what does the model predict?

**Check yourself**
- Why isn't a falling training loss proof that fine-tuning worked? What is catastrophic forgetting?

---

### Lesson 26: Free GPUs and What Training Costs

| Free option | GPU | Limits (they change; check current terms) |
|---|---|---|
| **Google Colab** | NVIDIA T4, 16 GB | Sessions of a few hours; idle disconnects; GPU not always available. `fp16` only, no `bf16` |
| **Kaggle Notebooks** | T4 ×2 or P100 | About 30 GPU-hours a week; phone verification |
| **Your Apple Silicon Mac** | MPS | LoRA on 0.5B–1.5B models works; slower than CUDA |

**Colab workflow:** New notebook → Runtime → Change runtime type → **T4 GPU** → upload your project or `git clone` it → `!pip install ...` → `!python train.py` → **download the adapter or save it to Google Drive before the session ends** (the VM is wiped).

| Paid option (approximate, late 2026 — shop around) | Rough cost |
|---|---|
| Colab Pro | ~$10/month for a bundle of compute units |
| Rented L4 / RTX 4090 (24 GB) — RunPod, Lambda, Vast.ai… | ~$0.40–0.80 per hour |
| Rented A100 80 GB / H100 80 GB | ~$1–2 / ~$2–4 per hour |
| Managed fine-tuning APIs (upload JSONL, get a model) | Per training token; small jobs cost a few dollars |

**Estimating a run**
```
total tokens = examples × average tokens per example × epochs
time         ≈ total tokens ÷ throughput (tokens per second)
```
Capstone: 480 × ~300 × 3 ≈ 430,000 tokens. A T4 doing LoRA on 0.5B manages a few thousand tokens per second: **roughly 5–15 minutes — free on Colab, well under $1 rented.** A 7B QLoRA run on the same data might take 30–60 minutes.

**Inference cost:** for a personal assistant making a few hundred calls a day, a hosted API is usually cheaper than buying hardware. Local wins on privacy, offline use and very high volume.

**Common mistakes**
- Losing a Colab session's outputs. Save checkpoints to Drive or a private Hub repo.
- Leaving a rented GPU running overnight. Use auto-shutdown or a reminder.

**Exercises**
1. Estimate time and cost for 2,000 examples × 500 tokens × 3 epochs at 3,000 tokens/second on a $0.60/hour GPU.

**Check yourself**
- Which precision setting does a T4 need? How do you estimate a run's duration?

---

### Lesson 27: Ethics, Bias and Licensing

**Concepts**
- **Models learn what's in the data, biases included.** If one team's requests were historically marked low priority, a priority model learns to deprioritise that team — nobody has to intend it.
- **Training data has owners**: it may be copyrighted, personal, or covered by terms of service.
- **Model weights have licences.** "Open weights" doesn't mean "do anything".
- **Fine-tuning can weaken safety behaviour**, and a local model has none of a provider's monitoring.
- **Models memorise.** Fine-tune on private emails and the model may reproduce names and phone numbers.

**Code: watch bias get learned**
```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

rng = np.random.default_rng(0)
n = 2000
df = pd.DataFrame({"days_until_due": rng.integers(0, 30, n), "team_b": rng.random(n) < 0.5})
truly_urgent = df["days_until_due"] < 5
# Biased historical labels: half of Team B's urgent requests were marked "not urgent"
df["labelled_urgent"] = truly_urgent & ~(df["team_b"] & (rng.random(n) < 0.5))

model = LogisticRegression().fit(df[["days_until_due", "team_b"]], df["labelled_urgent"])
print(dict(zip(["days_until_due", "team_b"], model.coef_[0].round(2))))   # team_b clearly negative

same_deadline = pd.DataFrame({"days_until_due": [2, 2], "team_b": [False, True]})
print(model.predict_proba(same_deadline)[:, 1].round(2))   # same task, lower urgency for Team B
```
Defences: check metrics per group, audit sensitive features *and their proxies*, fix labels at the source, keep a human in the loop for consequential decisions.

| Licence | Examples | Commercial use | Watch out for |
|---|---|---|---|
| Apache 2.0 | Qwen2.5 (most sizes), Mistral 7B, SmolLM2, OLMo | Yes | Keep the notice |
| MIT | Phi-3 / Phi-4 | Yes | Keep the notice |
| Llama Community Licence | Llama 3.x | Yes, with conditions | Acceptable-use policy, naming rules, very-large-user cap |
| Gemma Terms of Use | Gemma | Yes, with conditions | Prohibited-use policy passes down to your users |
| Non-commercial (e.g. CC BY-NC) | Various | No | Can't ship in a product |

Sizes within one family can have different licences, and fine-tunes generally inherit the base model's conditions. For data, ask: do I have the right to train on it? Does it contain personal data (GDPR etc.)? Did the people involved consent? Was it generated by a model whose terms restrict this? Is the dataset's own licence compatible?

**Honest reporting:** state test-set size, how it was built, what you compared against and where the model fails. Beating a frontier model on *your* 80 synthetic examples isn't beating it in general.

**Exercises**
1. Retrain the bias demo without `team_b`. Does the bias vanish? What if another feature correlated with team?
2. Write a one-paragraph data statement for the capstone dataset: source, size, labelling, known gaps.

**Check yourself**
- How can a model become biased when nobody intended it? Is "open weights" the same as "free for any use"?

---

## Capstone Project: A Local Tool-Calling Model

Fine-tune a small open model to turn natural-language requests into Work Organizer tool-call JSON, measure it honestly against the base model and against Claude on held-out examples, then serve it on your own machine with Ollama. The job is deliberately narrow — exactly where small fine-tuned models shine. A 0.5B model can't plan your week, but it can learn to turn "remind me to call the dentist tomorrow, it's urgent" into:
```json
{"tool": "add_task", "arguments": {"title": "Call the dentist", "priority": 1, "due": "2026-11-05", "tags": []}}
```

### Requirements

**Level 1 — it works**
- Generate ~600 examples split into train (480), validation (60) and test (80)
- Evaluate the **untrained** `Qwen/Qwen2.5-0.5B-Instruct` (Apache 2.0) on the test set: your baseline
- Fine-tune it with LoRA on Colab, Kaggle or your own GPU/Mac, and clearly beat the baseline

**Level 2 — a fair comparison**
- Evaluate your hosted Claude model with the identical prompt and test set; fill in the results table
- Group the fine-tuned model's failures, add targeted training data, retrain, re-evaluate — **without touching the test set**

**Level 3 — running on your machine**
- Merge the adapter, convert to GGUF, serve it with Ollama, and confirm it scores the same
- Wire it into your Work Organizer as an offline request parser with a fallback to Claude
- README with a data statement (Lesson 27), the results table, known failure modes and the base model's licence

### Suggested structure
```
wo_finetune/
├── tools.py            # tool descriptions + the system prompt (shared by everything)
├── make_dataset.py     # writes data/train.jsonl, data/val.jsonl, data/test.jsonl
├── train.py            # LoRA fine-tuning with trl's SFTTrainer
├── merge.py            # adapter + base -> standalone model
├── evaluate.py         # scores hf / ollama / claude backends on data/test.jsonl
├── local_router.py     # use the local model from the Work Organizer
├── Modelfile           # Ollama recipe
├── data/
└── outputs/            # adapters, merged model, GGUF, predictions (gitignore this)
```

### Step 1: The contract (`tools.py`)

Data generation, training, evaluation and serving all use this one system prompt. Today's date is part of it, so the model learns to resolve "tomorrow" and "Friday".

```python
# tools.py — the contract between the user, the model and your Work Organizer
from datetime import date

TOOLS_DESCRIPTION = """\
- add_task(title: str, priority: 1 | 2 | 3, due: "YYYY-MM-DD" or null, tags: list of str)
    priority: 1 = high/urgent, 2 = medium, 3 = low (the default)
- list_tasks(include_done: bool, tag: str or null, overdue_only: bool)
- complete_task(task_id: str)
- delete_task(task_id: str)
- none()   use this when the message is not a request about tasks"""

def system_prompt(today: date) -> str:
    return (
        "You convert a user's message into exactly ONE Work Organizer tool call.\n"
        f"Today is {today.isoformat()} ({today.strftime('%A')}).\n\n"
        f"Tools:\n{TOOLS_DESCRIPTION}\n\n"
        "Always include every argument of the chosen tool, using the defaults when the "
        "user doesn't say. Reply with JSON only, no other text:\n"
        '{"tool": "<name>", "arguments": {...}}'
    )

def build_messages(today: date, user_text: str) -> list[dict]:
    return [
        {"role": "system", "content": system_prompt(today)},
        {"role": "user", "content": user_text},
    ]
```

### Step 2: The dataset (`make_dataset.py`) — fill in the TODOs

Real logs would be ideal; here you generate varied examples from templates. Two good habits are built in: some phrasings are **reserved for the test set** (so you measure generalisation, not memorisation), and no example is ever repeated across splits.

```python
# make_dataset.py — generate train/val/test JSONL files of (request -> tool call)
import json
import random
from datetime import date, timedelta
from pathlib import Path

from tools import build_messages

SIZES = {"train": 480, "val": 60, "test": 80}
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
TAGS = ["work", "home", "finance", "health", "errands"]
TASKS = [  # (title the model should write, how a user might say it)
    ("Call the dentist", "call the dentist"),
    ("Email Sarah about the budget", "email sarah about the budget"),
    ("Renew passport", "renew my passport"),
    ("Pay the electricity bill", "pay the electricity bill"),
    ("Review Tom's pull request", "review tom's pull request"),
    ("Fix the login bug", "fix the login bug"),
    # TODO: add 20+ more, ideally your own real tasks — variety matters more than volume
]
# Phrasings for train/val, plus TEST_ONLY phrasings that never appear in training,
# so the test set measures generalisation to new wording, not memorisation.
ADD = ["add {t}", "remind me to {t}", "I need to {t}", "new task: {t}", "todo: {t}",
       "can you add a task to {t}", "don't let me forget to {t}"]
ADD_TEST_ONLY = ["please make a note that I have to {t}", "I should {t} at some point"]
PRIORITY_PHRASES = {1: [", it's urgent", " asap", " (high priority)"],
                    2: [" (medium priority)", ", normal priority"],
                    3: ["", "", " (low priority)", ", no rush"]}

def pick(rng: random.Random, phrasings: list[str], test_only: list[str], split: str) -> str:
    """In the test split, use a held-out phrasing half of the time."""
    if split == "test" and rng.random() < 0.5:
        return rng.choice(test_only)
    return rng.choice(phrasings)

def due_phrase(rng: random.Random, today: date) -> tuple[str, date | None]:
    kind = rng.choice(["none", "none", "today", "tomorrow", "weekday", "in_days", "explicit"])
    if kind == "today":
        return " today", today
    if kind == "tomorrow":
        return " tomorrow", today + timedelta(days=1)
    if kind == "weekday":                       # "friday" means the NEXT Friday, never today
        name = rng.choice(WEEKDAYS)
        days_ahead = (WEEKDAYS.index(name) - today.weekday()) % 7 or 7
        return f" by {name}", today + timedelta(days=days_ahead)
    if kind == "in_days":
        n = rng.randint(2, 10)
        return f" in {n} days", today + timedelta(days=n)
    if kind == "explicit":
        d = today + timedelta(days=rng.randint(1, 60))
        return f" by {d.strftime('%B')} {d.day}", d
    return "", None

def make_add(rng: random.Random, today: date, split: str) -> tuple[str, dict]:
    title, spoken = rng.choice(TASKS)
    priority = rng.choice([1, 2, 3, 3])
    due_text, due = due_phrase(rng, today)
    tags = rng.sample(TAGS, k=rng.choice([0, 0, 1, 2]))
    tag_text = " " + " ".join("#" + t for t in tags) if tags else ""
    extras = [due_text, rng.choice(PRIORITY_PHRASES[priority]), tag_text]
    rng.shuffle(extras)                         # vary the word order
    text = pick(rng, ADD, ADD_TEST_ONLY, split).format(t=spoken) + "".join(extras)
    return text, {"tool": "add_task", "arguments": {
        "title": title, "priority": priority, "due": due.isoformat() if due else None, "tags": tags}}

def make_other(rng: random.Random, today: date, split: str) -> tuple[str, dict]:
    # TODO: return (text, call) for the other tools, in the style of make_add:
    #   list_tasks    — plain ("show my tasks"), one tag ("show my work tasks"), overdue
    #                   ("anything overdue?"), include_done ("list all tasks, even completed ones");
    #                   ALWAYS include all three arguments: include_done, tag, overdue_only
    #   complete_task / delete_task — with a random 8-character id: f"{rng.getrandbits(32):08x}"
    #   none          — small talk and off-topic questions ("thanks!", "who wrote Hamlet?")
    # Give each some test-only phrasings too.
    ...

def make_example(rng: random.Random, split: str) -> dict:
    today = date(2026, 1, 1) + timedelta(days=rng.randrange(365))
    make = make_add if rng.random() < 0.5 else make_other
    text, call = make(rng, today, split)
    if rng.random() < 0.3:
        text = text[0].upper() + text[1:]       # light noise: don't rely on perfect casing
    return {"prompt": build_messages(today, text),
            "completion": [{"role": "assistant", "content": json.dumps(call)}]}

def main() -> None:
    rng = random.Random(42)
    Path("data").mkdir(exist_ok=True)
    seen: set[str] = set()
    for split, size in SIZES.items():
        rows = []
        while len(rows) < size:
            row = make_example(rng, split)
            key = row["prompt"][0]["content"] + row["prompt"][1]["content"]
            if key not in seen:                 # never repeat an example, especially across splits
                seen.add(key)
                rows.append(row)
        with open(f"data/{split}.jsonl", "w", encoding="utf-8") as f:
            f.writelines(json.dumps(row) + "\n" for row in rows)
        print(f"{split}: {len(rows)} examples")

if __name__ == "__main__":
    main()
```
```bash
python make_dataset.py
```
Then **read** 20 examples (`head -n 20 data/train.jsonl`) before doing anything else. To improve the data, add your own real task titles, typos ("remind me ot..."), "next week" / "end of the month" dates, or ask Claude to paraphrase 100 requests while you keep the labels.

### Step 3: The evaluator (`evaluate.py`)

Write the evaluator **before** training so you can score baselines first.

```python
# evaluate.py — score a model's tool calls on the held-out test set
import argparse
import json
import os
import time
from pathlib import Path

ADD_FIELDS = ["title", "priority", "due", "tags"]

def parse_call(text: str) -> dict | None:
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or "tool" not in obj or not isinstance(obj.get("arguments"), dict):
        return None
    return obj

def normalize(call: dict) -> dict:
    args = dict(call["arguments"])
    if isinstance(args.get("title"), str):
        args["title"] = args["title"].strip().rstrip(".").lower()
    if isinstance(args.get("tags"), list):
        args["tags"] = sorted(str(t).lower() for t in args["tags"])
    return {"tool": call["tool"], "arguments": args}

def score(golds: list[dict], pred_texts: list[str]) -> dict:
    n = len(golds)
    parsed = [parse_call(t) for t in pred_texts]
    results = {
        "n": n,
        "valid_json": sum(p is not None for p in parsed) / n,
        "tool_accuracy": sum(p is not None and p["tool"] == g["tool"] for p, g in zip(parsed, golds)) / n,
        "exact_match": sum(p is not None and normalize(p) == normalize(g) for p, g in zip(parsed, golds)) / n,
    }
    adds = [(p, g) for p, g in zip(parsed, golds) if g["tool"] == "add_task"]
    for field in ADD_FIELDS:
        correct = sum(p is not None and p["tool"] == "add_task"
                      and normalize(p)["arguments"].get(field) == normalize(g)["arguments"][field]
                      for p, g in adds)
        results[f"add_task.{field}"] = correct / max(len(adds), 1)
    return {k: round(v, 3) for k, v in results.items()}

def hf_predictor(model_path: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if torch.cuda.is_available():
        device, dtype = "cuda", torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    elif torch.backends.mps.is_available():
        device, dtype = "mps", torch.float16
    else:
        device, dtype = "cpu", torch.float32
    tok = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path, dtype=dtype).to(device).eval()

    def predict(messages: list[dict]) -> str:
        prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tok(prompt, return_tensors="pt", add_special_tokens=False).to(device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=128, do_sample=False,
                                 pad_token_id=tok.pad_token_id or tok.eos_token_id)
        return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    return predict

def ollama_predictor(model_name: str):
    import requests

    def predict(messages: list[dict]) -> str:
        r = requests.post("http://localhost:11434/api/chat", timeout=120, json={
            "model": model_name, "messages": messages, "stream": False, "options": {"temperature": 0}})
        r.raise_for_status()
        return r.json()["message"]["content"]

    return predict

def claude_predictor(model_name: str):
    import anthropic

    client = anthropic.Anthropic()                 # reads ANTHROPIC_API_KEY, like your assistant

    def predict(messages: list[dict]) -> str:
        response = client.messages.create(
            model=model_name,
            max_tokens=4096,
            system=messages[0]["content"],         # the same system prompt the small model gets
            messages=messages[1:],
        )
        if response.stop_reason == "refusal":
            return ""
        return "".join(block.text for block in response.content if block.type == "text")

    return predict

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["hf", "ollama", "claude"], required=True)
    parser.add_argument("--model", help="HF model id or path / Ollama model name / Claude model id")
    parser.add_argument("--data", default="data/test.jsonl")
    args = parser.parse_args()

    if args.backend == "hf":
        predict = hf_predictor(args.model or "Qwen/Qwen2.5-0.5B-Instruct")
    elif args.backend == "ollama":
        predict = ollama_predictor(args.model or "wo-tools")
    else:
        predict = claude_predictor(args.model or os.getenv("CLAUDE_MODEL", "claude-opus-5-5"))

    with open(args.data, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    golds = [json.loads(r["completion"][0]["content"]) for r in rows]

    start = time.perf_counter()
    preds = [predict(r["prompt"]) for r in rows]
    results = score(golds, preds)
    results["seconds_per_request"] = round((time.perf_counter() - start) / len(rows), 3)
    for key, value in results.items():
        print(f"{key:>22}: {value}")

    # Keep every prediction for error analysis
    out = Path("outputs") / f"preds-{args.backend}-{Path(args.model or 'default').name}.jsonl"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for row, gold, pred in zip(rows, golds, preds):
            f.write(json.dumps({"request": row["prompt"][1]["content"], "gold": gold, "pred": pred}) + "\n")
    print("Predictions saved to", out)

if __name__ == "__main__":
    main()
```
```bash
python evaluate.py --backend hf --model Qwen/Qwen2.5-0.5B-Instruct
```
```bash
python evaluate.py --backend claude
```
The Claude run reads `ANTHROPIC_API_KEY` from your environment, like your assistant does (`pip install anthropic` if needed). Set `CLAUDE_MODEL` to your Section 8 assistant's model, or pass `--model`. 80 short requests cost cents.

### Step 4: Fine-tune (`train.py`)

```python
# train.py — LoRA fine-tune a small instruct model on data/train.jsonl
import os

import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

BASE_MODEL = os.getenv("BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs/wo-lora")

def main() -> None:
    data = load_dataset("json", data_files={"train": "data/train.jsonl",
                                            "validation": "data/val.jsonl"})

    on_cuda = torch.cuda.is_available()
    use_bf16 = on_cuda and torch.cuda.is_bf16_supported()
    use_fp16 = on_cuda and not use_bf16          # e.g. a free Colab T4
    load_dtype = torch.bfloat16 if use_bf16 else torch.float32   # fp16 is applied by the trainer

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, dtype=load_dtype)

    peft_config = LoraConfig(
        r=16,                        # TODO: experiment with 8 and 32
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules="all-linear",
        task_type="CAUSAL_LM",
    )

    args = SFTConfig(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,          # TODO: compare 2, 3 and 5 epochs using eval_loss
        per_device_train_batch_size=8,
        gradient_accumulation_steps=2,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_steps=10,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        max_length=1024,             # our examples are ~300 tokens
        bf16=use_bf16,
        fp16=use_fp16,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=data["train"],
        eval_dataset=data["validation"],
        processing_class=tokenizer,
        peft_config=peft_config,
    )
    trainer.model.print_trainable_parameters()

    # Sanity check: only the assistant's JSON should be trained on (labels != -100)
    example = trainer.train_dataset[0]
    trained_ids = [t for t, label in zip(example["input_ids"], example["labels"]) if label != -100]
    print("Trained-on text of example 0:", repr(tokenizer.decode(trained_ids)))

    trainer.train()
    trainer.save_model(OUTPUT_DIR)       # the LoRA adapter only (tens of MB)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("Saved adapter to", OUTPUT_DIR)

if __name__ == "__main__":
    main()
```
On Colab (Runtime → Change runtime type → T4 GPU), upload the project or clone your repo, then run (prefix with `!` in a notebook cell):
```bash
pip install -q transformers datasets peft trl accelerate
```
```bash
python train.py
```
Expect roughly 5–15 minutes on a T4 (longer on a Mac, much longer on a CPU). `loss` and `eval_loss` should both fall, and the "Trained-on text" line must show **only** the assistant's JSON — proof the prompt is masked out. Download `outputs/wo-lora` (it's small) or copy it to Google Drive.

### Step 5: Merge, evaluate, analyse errors

```python
# merge.py — bake the LoRA adapter into the base weights -> a normal standalone model
import os

import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

ADAPTER_DIR = os.getenv("OUTPUT_DIR", "outputs/wo-lora")
MERGED_DIR = os.getenv("MERGED_DIR", "outputs/wo-merged")

model = AutoPeftModelForCausalLM.from_pretrained(ADAPTER_DIR, dtype=torch.float16)
merged = model.merge_and_unload()
merged.save_pretrained(MERGED_DIR)
AutoTokenizer.from_pretrained(ADAPTER_DIR).save_pretrained(MERGED_DIR)
print("Merged model saved to", MERGED_DIR)
```
```bash
python merge.py
```
```bash
python evaluate.py --backend hf --model outputs/wo-merged
```
Open `outputs/preds-hf-wo-merged.jsonl` and read every miss. Typical groups for a 0.5B model: **date arithmetic** (weekdays, "in 9 days"), titles with extra words ("Call the dentist tomorrow"), missed tags, and the held-out phrasings. Add varied data for the weakest group, or try a bigger base model:
```bash
BASE_MODEL=Qwen/Qwen2.5-1.5B-Instruct python train.py
```
An often better design: have the model output the date *phrase* ("friday") and compute the date in Python. Don't make a neural network do what three lines of ordinary code do perfectly.

### Step 6: Serve it with Ollama

Convert the merged model to GGUF with llama.cpp's converter, in a **separate virtual environment** (its requirements pin their own versions):
```bash
git clone https://github.com/ggml-org/llama.cpp
```
```bash
pip install -r llama.cpp/requirements.txt
```
```bash
python llama.cpp/convert_hf_to_gguf.py outputs/wo-merged --outfile outputs/wo-tools-q8_0.gguf --outtype q8_0
```
`Q8_0` is practically lossless and ~0.5 GB here. (For big models, convert with `--outtype f16`, then shrink to `Q4_K_M` with llama.cpp's `llama-quantize`.) Now a `Modelfile`, whose `TEMPLATE` reproduces Qwen's chat format so Ollama builds exactly the prompt the model was trained on:
```
FROM ./outputs/wo-tools-q8_0.gguf

TEMPLATE """{{- range .Messages }}<|im_start|>{{ .Role }}
{{ .Content }}<|im_end|>
{{ end }}<|im_start|>assistant
"""

PARAMETER temperature 0
PARAMETER stop "<|im_end|>"
PARAMETER num_ctx 2048
```
```bash
ollama create wo-tools -f Modelfile
```
```bash
python evaluate.py --backend ollama --model wo-tools
```
Scores should closely match Step 5. If they're much worse, the template doesn't match training: compare it with what `tok.apply_chat_template(...)` produces.

### Step 7: Use it from the Work Organizer

Local for the common case (fast, free, private); Claude for everything else.
```python
# local_router.py
import json
from datetime import date

import requests

from tools import build_messages

VALID_TOOLS = {"add_task", "list_tasks", "complete_task", "delete_task", "none"}

def parse_locally(user_text: str) -> dict | None:
    """Ask the local fine-tuned model for a tool call. Returns None if it's unusable."""
    try:
        r = requests.post("http://localhost:11434/api/chat", timeout=30, json={
            "model": "wo-tools", "messages": build_messages(date.today(), user_text), "stream": False})
        r.raise_for_status()
        call = json.loads(r.json()["message"]["content"])
    except (requests.RequestException, json.JSONDecodeError, KeyError):
        return None
    if not isinstance(call, dict) or call.get("tool") not in VALID_TOOLS:
        return None
    return call

def handle(user_text: str) -> str:
    call = parse_locally(user_text)
    if call is None or call["tool"] == "none":
        return "fallback"   # TODO: hand the message to your Section 8 Claude assistant
    # TODO: validate call["arguments"] with your Pydantic models, then dispatch exactly as your
    # assistant does with Claude's tool calls:  result = TOOLS[call["tool"]](**arguments)
    return f"would run {call['tool']} with {call['arguments']}"
```

### Results table (fill this in)

| Model | Valid JSON | Tool acc. | Exact match | `due` acc. | Sec / request | Cost / 1,000 requests | Offline |
|---|---|---|---|---|---|---|---|
| Qwen2.5-0.5B-Instruct (base) | | | | | | $0 | Yes |
| + LoRA fine-tune | | | | | | $0 | Yes |
| Same via Ollama (Q8_0) | | | | | | $0 | Yes |
| Claude (your assistant's model) | | | | | | | No |

What you'll most likely find: the base model often breaks the format or fills in wrong arguments; the fine-tune is dramatically better at format and tool choice and very fast, but trails Claude on dates and unusual phrasings — and Claude needed **zero** training examples. That's the real trade-off, and now you can measure it instead of guessing.

---

## Weekly Schedule

| Week | Lessons | Mini-project |
|---|---|---|
| 1 | Part 0, Lessons 1–3 | Dot products and numerical derivatives, by hand and in numpy |
| 2 | Lessons 4–5 | Gradient-descent line fit; temperature sampler |
| 3 | Lessons 6–8 | Explore the task dataset; hours-overrun regressor |
| 4 | Lessons 9–10 | Task-priority classifier with honest metrics |
| 5 | Lessons 11–12 | Neural network from scratch, gradient-checked |
| 6 | Lessons 13–14 | Same in PyTorch; priority net with early stopping |
| 7 | Lessons 15–17 | Toy BPE; semantic task search; attention by hand |
| 8 | Lessons 18–20 | Your own generation loop; JSONL datasets |
| 9 | Lessons 21–23 | Ollama and llama.cpp on your machine; LoRA maths |
| 10 | Lessons 24–27 | First fine-tune on Colab; read three model licences |
| 11–12 | Capstone Levels 1–3 | Local tool-calling model vs Claude, served by Ollama |

**Daily routine (1–2 hours):** 20 min reading → 40 min typing examples → 30 min exercises → 5 min notes on what confused you. On training days, start the run first and read while it trains.

---

## Final Checklist

You've finished this section when you can do all of this **without looking things up**:

**Maths and classic ML**
- [ ] Compute dot products and matrix products in numpy and predict result shapes
- [ ] Apply the chain rule, check a derivative numerically, and fit a line with gradient descent
- [ ] Implement a stable softmax and cross-entropy, and explain temperature
- [ ] Clean and summarise data with pandas; train scikit-learn models against a baseline
- [ ] Spot overfitting and choose between accuracy, precision, recall and F1

**Neural networks and LLMs**
- [ ] Write forward and backward passes for a 2-layer network in numpy and gradient-check them
- [ ] Write an `nn.Module`, a `DataLoader` and the PyTorch training loop on CUDA/MPS/CPU
- [ ] Explain tokenization, embeddings, attention and next-token prediction in plain words
- [ ] Implement causal attention; explain pretraining vs instruction tuning vs preference tuning
- [ ] Load a Hub model, apply its chat template and generate text

**Local models and fine-tuning**
- [ ] Run models with Ollama and llama.cpp, call them from Python, and estimate their memory needs
- [ ] Decide between prompting, RAG and fine-tuning for a given problem
- [ ] Build a JSONL dataset with a genuinely held-out test set
- [ ] Fine-tune with LoRA (`peft` + `trl`), merge the adapter and convert it to GGUF
- [ ] Evaluate models fairly on one test set, analyse errors, and check licences and data provenance

---

## Exercise Solutions

Try every exercise yourself first. Look here only after a real attempt (at least 20 minutes).

**Lesson 3, Exercise 2**
```
pred          = w * x + b           = 3 * 2 + 1         = 7
d loss / d w  = 2 * (pred - y) * x  = 2 * (7 - 10) * 2  = -12
d loss / d b  = 2 * (pred - y)      = 2 * (7 - 10)      = -6
```
```python
def numerical_derivative(func, x, h=1e-5):
    return (func(x + h) - func(x - h)) / (2 * h)

x, y, w, b = 2.0, 10.0, 3.0, 1.0
print(numerical_derivative(lambda w_: (w_ * x + b - y) ** 2, w))   # ~-12
print(numerical_derivative(lambda b_: (w * x + b_ - y) ** 2, b))   # ~-6
```

**Lesson 5, Exercises 1–2**
```python
import numpy as np

def softmax_rows(Z: np.ndarray) -> np.ndarray:
    Z = Z - Z.max(axis=1, keepdims=True)
    E = np.exp(Z)
    return E / E.sum(axis=1, keepdims=True)

print(softmax_rows(np.array([[2.0, 1.0, 0.1], [0.0, 0.0, 0.0]])).round(3))
# [[0.659 0.242 0.099]
#  [0.333 0.333 0.333]]
print(np.log(50_000))   # Exercise 2: -log(1/50000) ≈ 10.8. Trained LLMs get down to ~2 or below.
```

**Lesson 10, Exercise 1**
```python
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.tree import DecisionTreeClassifier

from task_data import make_tasks

df = make_tasks().dropna()
FEATURES = ["hours", "days_until_due", "from_manager", "blocking_others"]
X, y = df[FEATURES].astype(float), df["priority"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

search = GridSearchCV(DecisionTreeClassifier(random_state=42),
                      {"max_depth": [2, 3, 4, 5, 6, 8, 10], "min_samples_leaf": [1, 5, 10, 20]}, cv=5)
search.fit(X_train, y_train)                         # tuning uses ONLY training data
print(search.best_params_, round(search.best_score_, 3))
print("test accuracy, reported once:", round(search.score(X_test, y_test), 3))
```

**Lesson 14, Exercises 1–2** (outline)
Use `nn.Sequential(nn.Linear(4, 32), nn.ReLU(), nn.Linear(32, 3))` with `nn.CrossEntropyLoss()` and the Lesson 14 loop. After each epoch compute validation accuracy with `model(xb).argmax(dim=1) == yb`; if it beat the best so far, save `copy.deepcopy(model.state_dict())` and reset a counter, otherwise increment it and `break` at 5. Finally `model.load_state_dict(best_state)`. Expect ~0.8 — about the same as logistic regression: with 4 features and a nearly linear rule, the simplest model that works wins.

**Lesson 17, Exercise 2**
```python
block = Block(d_model=896, n_heads=14)
per_block = sum(p.numel() for p in block.parameters())
print(per_block, per_block * 24)   # ~9.6M per block, ~231M for 24 blocks
# Add the 151,936 x 896 embedding table (~136M) ≈ 368M. The real model has ~494M because
# Qwen's MLP is wider (4,864) and "gated" (three matrices instead of two).
```

**Lesson 18, Exercise 1** (top-k)
```python
import torch

def top_k_filter(logits: torch.Tensor, k: int) -> torch.Tensor:
    cutoff = torch.topk(logits, k).values[..., -1, None]      # the k-th largest logit
    return logits.masked_fill(logits < cutoff, float("-inf"))

print(torch.softmax(top_k_filter(torch.tensor([[1.0, 3.0, 2.0, 0.5]]), k=2), dim=-1))
# tensor([[0.0000, 0.7311, 0.2689, 0.0000]])
# In generate():  torch.softmax(top_k_filter(next_logits, 50) / temperature, dim=-1)
```

**Lesson 21, Exercise 2; Lesson 23, Exercise 1; Lesson 26, Exercise 1**
```
14B at Q8_0:    14e9 x 8.5 / 8 ≈ 14.9 GB (+1-2 GB) ≈ 16-17 GB
14B at Q4_K_M:  14e9 x 4.8 / 8 ≈ 8.4 GB  (+1-2 GB) ≈ 10 GB

LoRA on 4096 x 4096 (16,777,216 weights): r x (4096 + 4096)
  r=4: 32,768 (0.20%)   r=16: 131,072 (0.78%)   r=64: 524,288 (3.12%)

2,000 x 500 x 3 = 3,000,000 tokens / 3,000 per s = 1,000 s ≈ 17 min ≈ 0.28 h x $0.60 ≈ $0.17
```

---

## Recommended Resources

| Resource | Type | Best for |
|---|---|---|
| 3Blue1Brown — *Neural Networks* and *Essence of Linear Algebra* (YouTube) | Video | Visual intuition for Parts A and C |
| Andrej Karpathy — *Neural Networks: Zero to Hero* (YouTube, free) | Video course | Backprop from scratch up to building GPT |
| fast.ai — *Practical Deep Learning for Coders* (free) | Course | Practical, top-down deep learning |
| Hugging Face LLM Course (huggingface.co/learn) | Course | Transformers, datasets, fine-tuning |
| *Hands-On Machine Learning* (Aurélien Géron) | Book | Classic ML and deep learning in depth |
| *Build a Large Language Model (From Scratch)* (Sebastian Raschka) | Book | Every piece of a GPT, in PyTorch |
| Jay Alammar — *The Illustrated Transformer* | Article | Attention, visually |
| scikit-learn User Guide; PyTorch Tutorials | Docs | Models and metrics; tensors and training loops |
| TRL, PEFT and Ollama docs; the llama.cpp README | Docs | `SFTTrainer`, LoRA, Modelfiles, GGUF |

**Next:** this was the final, optional section of the course. Take your capstone measurements back to your Section 8 assistant: keep Claude for open-ended reasoning and multi-step tool use, consider small local models for narrow, high-volume or private jobs, and evaluate every change against a held-out test set.
