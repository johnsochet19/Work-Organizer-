"""Autodidact: a research agent that builds its own knowledge base and its own toolset
from free web sources and APIs."""
from .agent import Agent
from .brain import Brain
from .net import Net

__all__ = ["Agent", "Brain", "Net"]
