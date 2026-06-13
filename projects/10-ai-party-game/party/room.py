"""Authoritative room/round state machine for an AI party game ("Quiplash"-style).

Each round: a prompt is posed, players submit one answer, an LLM judge ranks the
answers, and points are awarded. The room is the source of truth; the network
layer just reads/writes it. Pure and deterministic (LLM + prompt deck injected),
so the whole flow is unit-tested.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

DEFAULT_DECK = [
    "A terrible name for a boat",
    "The worst superpower to have",
    "What aliens think humans taste like",
    "A rejected ice-cream flavor",
    "The real reason the dinosaurs went extinct",
]


class Phase(str, Enum):
    LOBBY = "lobby"
    ANSWERING = "answering"
    REVEAL = "reveal"


class RoomError(Exception):
    pass


@dataclass
class Player:
    id: str
    name: str
    score: int = 0


@dataclass
class Room:
    code: str
    deck: list[str] = field(default_factory=lambda: list(DEFAULT_DECK))
    players: dict[str, Player] = field(default_factory=dict)
    phase: Phase = Phase.LOBBY
    prompt: str = ""
    answers: dict[str, str] = field(default_factory=dict)   # player_id -> answer
    ranking: list[str] = field(default_factory=list)        # player_ids, best first
    round: int = 0
    _rng: random.Random = field(default_factory=lambda: random.Random(0))

    # --- lobby ---------------------------------------------------------------

    def join(self, player_id: str, name: str) -> Player:
        if self.phase != Phase.LOBBY and player_id not in self.players:
            raise RoomError("game already in progress")
        p = Player(id=player_id, name=name)
        self.players[player_id] = p
        return p

    # --- round lifecycle -----------------------------------------------------

    def start_round(self) -> None:
        if len(self.players) < 2:
            raise RoomError("need at least 2 players")
        self.round += 1
        self.prompt = self._rng.choice(self.deck)
        self.answers = {}
        self.ranking = []
        self.phase = Phase.ANSWERING

    def submit(self, player_id: str, answer: str) -> None:
        if self.phase != Phase.ANSWERING:
            raise RoomError("not accepting answers right now")
        if player_id not in self.players:
            raise RoomError("unknown player")
        if player_id in self.answers:
            raise RoomError("already answered")
        text = answer.strip()
        if not text:
            raise RoomError("empty answer")
        self.answers[player_id] = text

    def all_answered(self) -> bool:
        return len(self.answers) == len(self.players) and len(self.players) > 0

    def reveal(self, judge) -> list[dict]:
        """Have the judge rank submitted answers and award points (3/2/1...)."""
        if self.phase != Phase.ANSWERING:
            raise RoomError("can only reveal during answering phase")
        if not self.answers:
            raise RoomError("no answers to judge")
        named = [(self.players[pid].name, ans, pid) for pid, ans in self.answers.items()]
        ordered_names = judge.rank(self.prompt, [(n, a) for n, a, _ in named])

        # Map judge's ordered names back to player ids; append any it omitted.
        name_to_pid = {n: pid for n, _, pid in named}
        self.ranking = []
        for n in ordered_names:
            if n in name_to_pid and name_to_pid[n] not in self.ranking:
                self.ranking.append(name_to_pid[n])
        for _, _, pid in named:
            if pid not in self.ranking:
                self.ranking.append(pid)

        points = max(3, len(self.ranking))
        results = []
        for rank, pid in enumerate(self.ranking):
            awarded = max(0, points - rank)
            self.players[pid].score += awarded
            results.append({"name": self.players[pid].name, "answer": self.answers[pid],
                            "rank": rank + 1, "points": awarded})
        self.phase = Phase.REVEAL
        return results

    def scoreboard(self) -> list[dict]:
        ranked = sorted(self.players.values(), key=lambda p: p.score, reverse=True)
        return [{"name": p.name, "score": p.score} for p in ranked]

    def snapshot(self) -> dict:
        return {
            "code": self.code,
            "phase": self.phase.value,
            "round": self.round,
            "prompt": self.prompt,
            "players": [{"name": p.name, "score": p.score, "answered": p.id in self.answers}
                         for p in self.players.values()],
            "answers_in": len(self.answers),
            "scoreboard": self.scoreboard(),
        }
