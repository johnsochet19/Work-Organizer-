"""End-to-end tests against a simulated web (no network needed).

Run:  python -m unittest discover -s tests   (from the autodidact/ folder)
"""
import json
import os
import sys
import tempfile
import unittest
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from autodidact import answer, discover, text  # noqa: E402
from autodidact.agent import Agent  # noqa: E402
from autodidact.brain import Brain  # noqa: E402
from autodidact.net import Net, Response  # noqa: E402

ARTICLES = {
    "Neural network": (
        "A neural network is a machine learning model inspired by the structure of the brain. "
        "Neural networks are trained with gradient descent and backpropagation. "
        "Deep learning uses neural networks with many layers. "
        "Convolutional neural networks are used for image recognition. "
        "Backpropagation computes the gradient of the loss function with respect to each weight. "
        "Gradient descent then updates the weights to reduce the loss function."),
    "Backpropagation": (
        "Backpropagation is an algorithm for computing the gradient of a loss function in a neural network. "
        "It applies the chain rule layer by layer, from the output back to the input. "
        "Backpropagation made training deep learning models practical. "
        "Gradient descent uses the gradient from backpropagation to update weights."),
    "Gradient descent": (
        "Gradient descent is an optimization algorithm that minimizes a loss function by moving against the gradient. "
        "Stochastic gradient descent uses small random batches of training data. "
        "The learning rate controls the step size of gradient descent. "
        "Gradient descent is the standard way to train a neural network."),
}

ARXIV = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/1</id>
<title>Adaptive learning rate methods for deep learning</title>
<summary>We study adaptive learning rate methods such as Adam for training deep learning models.
Adaptive learning rate methods converge faster than plain stochastic gradient descent on large models.</summary>
</entry></feed>"""

DIRECTORY = """
### Science & Math
| API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [Glossary](https://glossary.example.org/api) | Definitions of machine learning and science terms | No | Yes | Yes |
| [Cats](https://cats.example.org) | Random cat pictures | No | Yes | Yes |
| [Paid](https://paid.example.org) | Machine learning definitions | `apiKey` | Yes | Yes |
"""


class FakeWeb:
    def __init__(self):
        self.calls = []

    def __call__(self, url, headers, timeout):
        self.calls.append(url)
        u = urllib.parse.urlsplit(url)
        qs = urllib.parse.parse_qs(u.query)
        J = lambda obj: Response(url, 200, json.dumps(obj), "application/json")
        if u.path == "/robots.txt":
            if u.netloc == "blocked.example.org":
                return Response(url, 200, "User-agent: *\nDisallow: /", "text/plain")
            return Response(url, 404, "")
        if u.netloc == "en.wikipedia.org":
            if qs.get("list") == ["search"]:
                term = qs["srsearch"][0].lower()
                hits = [{"title": t} for t in ARTICLES if any(w in t.lower() for w in term.split())]
                return J({"query": {"search": hits or [{"title": "Neural network"}]}})
            title = qs["titles"][0]
            return J({"query": {"pages": {"1": {"title": title, "extract": ARTICLES.get(title, "")}}}})
        if u.netloc == "export.arxiv.org":
            return Response(url, 200, ARXIV, "application/atom+xml")
        if u.netloc == "raw.githubusercontent.com":
            return Response(url, 200, DIRECTORY, "text/plain")
        if u.netloc == "glossary.example.org" and u.path == "/api/search":
            return J({"results": [{"term": "learning rate", "url": "https://glossary.example.org/lr",
                                   "definition": "The learning rate is a hyperparameter that sets the step "
                                                 "size of each gradient descent update during training."}]})
        if u.netloc == "cats.example.org":
            return J({"url": "https://cats.example.org/cat.jpg"})
        return Response(url, 404, "")


def make_agent(tmp, web=None):
    brain = Brain(os.path.join(tmp, "brain.db"))
    net = Net(cache_dir=None, min_interval=0, transport=web or FakeWeb())
    agent = Agent(brain, net, log=lambda *a: None)
    # keep the test to the two fake sources that have content
    for s in brain.sources():
        if s["name"] not in ("wikipedia", "arxiv"):
            brain.db.execute("UPDATE sources SET enabled=0 WHERE name=?", (s["name"],))
    brain.db.commit()
    return agent


class TextTests(unittest.TestCase):
    def test_keyphrases_find_repeated_multiword_terms(self):
        phrases = [p for p, _ in text.keyphrases(ARTICLES["Neural network"])]
        self.assertIn("gradient descent", phrases)
        self.assertIn("loss function", phrases)

    def test_html_to_text_drops_scripts_and_menus(self):
        title, body, links = text.html_to_text(
            "<html><title>T</title><script>evil()</script><nav>Home About</nav>"
            "<p>This is a real paragraph of content that is long enough to keep.</p><a href='/x'>x</a></html>")
        self.assertEqual(title, "T")
        self.assertIn("real paragraph", body)
        self.assertNotIn("evil", body)
        self.assertEqual(links, ["/x"])


class BrainTests(unittest.TestCase):
    def test_index_search_and_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Brain(os.path.join(tmp, "b.db"))
            for t, body in ARTICLES.items():
                b.add_doc(f"https://x/{t}", t, body, "test", "ml")
            self.assertEqual(b.add_doc("https://x/Backpropagation", "dup", ARTICLES["Backpropagation"], "t", "ml"), {})
            hits = b.search("chain rule")
            self.assertEqual(hits[0]["title"], "Backpropagation")
            self.assertIn("gradient descent", [r for r, _ in b.related("loss function", 20)])


class AgentTests(unittest.TestCase):
    def test_learns_spawns_followups_and_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = make_agent(tmp)
            agent.brain.set("mission", "neural network training")
            agent.brain.push_topic("neural network", 1.0, "test")
            res = agent.cycle()
            self.assertGreater(res["docs"], 0)
            self.assertTrue(res["spawned"], "should queue follow-up topics from what it read")
            agent.run(3)
            stats = agent.brain.stats()
            self.assertGreaterEqual(stats["topics_done"], 3)
            ans = answer.ask(agent.brain, "what does backpropagation compute?")
            self.assertIn("gradient", ans["answer"].lower())
            self.assertTrue(ans["sources"])
            md = answer.report(agent.brain)
            self.assertIn("Core concepts", md)

    def test_bandit_prefers_productive_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = make_agent(tmp)
            b = agent.brain
            b.db.execute("UPDATE sources SET pulls=10, reward=9 WHERE name='wikipedia'")
            b.db.execute("UPDATE sources SET pulls=10, reward=0.5 WHERE name='arxiv'")
            b.db.commit()
            self.assertEqual(agent.choose_sources(1)[0]["name"], "wikipedia")

    def test_self_tune_retires_useless_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = make_agent(tmp)
            agent.brain.db.execute("UPDATE sources SET pulls=8, reward=0 WHERE name='arxiv'")
            agent.brain.db.commit()
            agent.self_tune()
            self.assertNotIn("arxiv", [s["name"] for s in agent.brain.sources()])


class DiscoveryTests(unittest.TestCase):
    def test_directory_parsing_skips_keyed_apis(self):
        names = [a["name"] for a in discover.parse_directory(DIRECTORY)]
        self.assertEqual(names, ["Glossary", "Cats"])

    def test_infer_spec_on_unknown_json(self):
        data = {"meta": {"n": 1}, "results": [{"term": "x", "url": "https://a/b", "definition": "y" * 60}]}
        spec = discover.infer_spec("G", "https://g/?q={query}", data)
        self.assertEqual(spec["items_path"], "results")
        self.assertEqual(spec["text_fields"], ["definition"])
        self.assertEqual(spec["title_field"], "term")
        self.assertEqual(spec["url_field"], "url")

    def test_agent_teaches_itself_a_new_source_and_uses_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent = make_agent(tmp)
            agent.brain.add_doc("https://x/gd", "Gradient descent", ARTICLES["Gradient descent"], "t", "ml")
            added = agent.extend()
            self.assertEqual(added, ["Glossary"], "keeps the API that returns real text, drops the cat pictures")
            src = {s["name"]: s for s in agent.brain.sources()}["Glossary"]
            self.assertEqual(src["kind"], "learned")
            # it is now a first-class source the bandit will try
            agent.brain.push_topic("learning rate", 1.0, "test")
            agent.cycle()
            self.assertIn("Glossary", [s["name"] for s in agent.brain.sources() if s["pulls"] > 0])
            self.assertTrue(agent.brain.has_url("https://glossary.example.org/lr"),
                            "knowledge from the self-taught source landed in the brain")
            # never re-probes APIs it already tried
            self.assertEqual(agent.extend(), [])


class NetTests(unittest.TestCase):
    def test_robots_txt_is_respected(self):
        web = FakeWeb()
        net = Net(min_interval=0, transport=web)
        r = net.get("https://blocked.example.org/page")
        self.assertEqual(r.status, 999)
        self.assertNotIn("https://blocked.example.org/page", web.calls)


if __name__ == "__main__":
    unittest.main()
