import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from party import Room, Phase, RoomError, ScriptedJudge  # noqa: E402


def room_with_players(*names):
    r = Room(code="ABCD")
    for i, n in enumerate(names):
        r.join(f"p{i}", n)
    return r


class TestLobby(unittest.TestCase):
    def test_join_and_start(self):
        r = room_with_players("ann", "bob")
        self.assertEqual(len(r.players), 2)
        r.start_round()
        self.assertEqual(r.phase, Phase.ANSWERING)
        self.assertTrue(r.prompt)

    def test_cannot_start_with_one_player(self):
        r = room_with_players("ann")
        with self.assertRaises(RoomError):
            r.start_round()

    def test_cannot_join_mid_game(self):
        r = room_with_players("ann", "bob")
        r.start_round()
        with self.assertRaises(RoomError):
            r.join("p9", "latecomer")


class TestAnswering(unittest.TestCase):
    def setUp(self):
        self.r = room_with_players("ann", "bob")
        self.r.start_round()

    def test_submit_and_all_answered(self):
        self.r.submit("p0", "a boat named Sinky")
        self.assertFalse(self.r.all_answered())
        self.r.submit("p1", "the SS Drowny")
        self.assertTrue(self.r.all_answered())

    def test_no_double_answer(self):
        self.r.submit("p0", "first")
        with self.assertRaises(RoomError):
            self.r.submit("p0", "second")

    def test_reject_empty_answer(self):
        with self.assertRaises(RoomError):
            self.r.submit("p0", "   ")

    def test_cannot_submit_before_round(self):
        fresh = room_with_players("x", "y")
        with self.assertRaises(RoomError):
            fresh.submit("p0", "too early")


class TestJudging(unittest.TestCase):
    def test_reveal_awards_points_by_rank(self):
        r = room_with_players("ann", "bob", "cara")
        r.start_round()
        r.submit("p0", "ann's answer")
        r.submit("p1", "bob's answer")
        r.submit("p2", "cara's answer")
        results = r.reveal(ScriptedJudge(["bob", "ann", "cara"]))
        self.assertEqual(r.phase, Phase.REVEAL)
        # 3 players -> points start at 3: bob=3, ann=2, cara=1
        by_name = {row["name"]: row for row in results}
        self.assertEqual(by_name["bob"]["points"], 3)
        self.assertEqual(by_name["ann"]["points"], 2)
        self.assertEqual(by_name["cara"]["points"], 1)
        self.assertEqual(r.players["p1"].score, 3)

    def test_scores_accumulate_across_rounds(self):
        r = room_with_players("ann", "bob")
        for _ in range(2):
            r.start_round()
            r.submit("p0", "a"); r.submit("p1", "b")
            r.reveal(ScriptedJudge(["ann", "bob"]))
        # ann wins both: 3+3=6 (2 players -> points start at max(3,2)=3)
        self.assertEqual(r.players["p0"].score, 6)
        self.assertEqual(r.scoreboard()[0]["name"], "ann")

    def test_judge_omitting_a_name_still_ranks_everyone(self):
        r = room_with_players("ann", "bob")
        r.start_round()
        r.submit("p0", "a"); r.submit("p1", "b")
        results = r.reveal(ScriptedJudge(["ann"]))  # judge forgot bob
        names = {row["name"] for row in results}
        self.assertEqual(names, {"ann", "bob"})  # bob appended automatically


if __name__ == "__main__":
    unittest.main()
