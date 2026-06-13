package social

import "testing"

func mustRegister(t *testing.T, s *Store, name string) *User {
	t.Helper()
	u, err := s.Register(name, "pw-"+name)
	if err != nil {
		t.Fatalf("register %s: %v", name, err)
	}
	return u
}

func TestRegisterAndAuthenticate(t *testing.T) {
	s := NewStore()
	u := mustRegister(t, s, "ann")
	if _, err := s.Register("ann", "x"); err != ErrUserExists {
		t.Errorf("duplicate username should fail, got %v", err)
	}
	got, err := s.Authenticate("ann", "pw-ann")
	if err != nil || got.ID != u.ID {
		t.Fatalf("auth failed: %v", err)
	}
	if _, err := s.Authenticate("ann", "wrong"); err != ErrBadPassword {
		t.Errorf("bad password should fail, got %v", err)
	}
}

func TestPasswordIsHashedNotStored(t *testing.T) {
	s := NewStore()
	u := mustRegister(t, s, "ann")
	if u.hash == "pw-ann" || u.hash == "" {
		t.Error("password must be hashed")
	}
}

func TestPostValidation(t *testing.T) {
	s := NewStore()
	u := mustRegister(t, s, "ann")
	if _, err := s.CreatePost(u.ID, ""); err != ErrEmptyPost {
		t.Errorf("empty post should fail, got %v", err)
	}
	long := make([]byte, MaxPostLen+1)
	for i := range long {
		long[i] = 'a'
	}
	if _, err := s.CreatePost(u.ID, string(long)); err != ErrPostTooLong {
		t.Errorf("too-long post should fail, got %v", err)
	}
}

func TestFeedShowsFollowedAndSelfNewestFirst(t *testing.T) {
	s := NewStore()
	ann := mustRegister(t, s, "ann")
	bob := mustRegister(t, s, "bob")
	cara := mustRegister(t, s, "cara")

	s.CreatePost(bob.ID, "bob first")
	s.CreatePost(cara.ID, "cara hidden") // ann does not follow cara
	s.CreatePost(ann.ID, "ann own")
	s.CreatePost(bob.ID, "bob second")

	if err := s.Follow(ann.ID, bob.ID); err != nil {
		t.Fatal(err)
	}
	feed := s.Feed(ann.ID, 10)

	// Expect bob's two posts + ann's own, newest first; cara excluded.
	texts := []string{}
	for _, p := range feed {
		texts = append(texts, p.Text)
	}
	if len(feed) != 3 {
		t.Fatalf("want 3 feed posts, got %d (%v)", len(feed), texts)
	}
	if texts[0] != "bob second" {
		t.Errorf("feed should be newest-first, got %v", texts)
	}
	for _, p := range feed {
		if p.Author == "cara" {
			t.Error("feed must not include un-followed cara")
		}
	}
}

func TestCannotFollowSelf(t *testing.T) {
	s := NewStore()
	ann := mustRegister(t, s, "ann")
	if err := s.Follow(ann.ID, ann.ID); err == nil {
		t.Error("self-follow should error")
	}
}

func TestLikeToggles(t *testing.T) {
	s := NewStore()
	ann := mustRegister(t, s, "ann")
	bob := mustRegister(t, s, "bob")
	p, _ := s.CreatePost(bob.ID, "like me")

	liked, _ := s.Like(ann.ID, p.ID)
	if !liked || s.posts[p.ID].Likes != 1 {
		t.Fatalf("first like should set liked=true, count=1")
	}
	liked, _ = s.Like(ann.ID, p.ID)
	if liked || s.posts[p.ID].Likes != 0 {
		t.Fatalf("second like should unlike, count=0")
	}
}

func TestFeedReportsLikedByMe(t *testing.T) {
	s := NewStore()
	ann := mustRegister(t, s, "ann")
	p, _ := s.CreatePost(ann.ID, "self post")
	s.Like(ann.ID, p.ID)
	feed := s.Feed(ann.ID, 10)
	if !feed[0].LikedByMe {
		t.Error("feed should mark posts the viewer liked")
	}
}
