// Package api also provides lightweight anti-cheat: score submissions must be
// signed with an HMAC-SHA256 over the canonical fields using a shared secret,
// so a client can't POST arbitrary scores without the key.
package api

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strconv"
)

// Sign returns the hex HMAC for a submission.
func Sign(secret, player, game string, points int64) string {
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write([]byte(canonical(player, game, points)))
	return hex.EncodeToString(mac.Sum(nil))
}

// Verify checks a provided signature in constant time.
func Verify(secret, player, game string, points int64, sig string) bool {
	want := Sign(secret, player, game, points)
	got, err := hex.DecodeString(sig)
	if err != nil {
		return false
	}
	wantBytes, _ := hex.DecodeString(want)
	return hmac.Equal(wantBytes, got)
}

func canonical(player, game string, points int64) string {
	return fmt.Sprintf("%s:%s:%s", player, game, strconv.FormatInt(points, 10))
}
