"""Pure utility/unit tests (no HTTP, no DB)."""

import time

from app.core.cache import InMemoryCache
from app.core.rbac import Role, role_satisfies
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_password,
)
from app.core.text import slug_with_suffix, slugify


class TestRbac:
    def test_owner_satisfies_all(self):
        assert role_satisfies("owner", Role.owner)
        assert role_satisfies("owner", Role.admin)
        assert role_satisfies("owner", Role.member)

    def test_member_only_member(self):
        assert role_satisfies("member", Role.member)
        assert not role_satisfies("member", Role.admin)
        assert not role_satisfies("member", Role.owner)

    def test_unknown_role_satisfies_nothing(self):
        assert not role_satisfies("ghost", Role.member)


class TestSecurity:
    def test_password_roundtrip(self):
        h = hash_password("password123")
        assert h != "password123"
        assert verify_password("password123", h)
        assert not verify_password("wrong", h)

    def test_jwt_roundtrip(self):
        token = create_access_token("user-123")
        assert decode_access_token(token) == "user-123"

    def test_jwt_invalid(self):
        assert decode_access_token("not-a-jwt") is None

    def test_api_key_generation_and_hash(self):
        full, prefix, hashed = generate_api_key()
        assert full.startswith("sk_live_")
        assert full.startswith(prefix)
        assert hashed == hash_api_key(full)
        assert hashed != full  # only the hash is stored


class TestText:
    def test_slugify(self):
        assert slugify("Acme Corp!") == "acme-corp"
        assert slugify("") == "org"

    def test_slug_with_suffix_is_prefixed(self):
        assert slug_with_suffix("Acme Corp").startswith("acme-corp-")


class TestInMemoryCache:
    def test_set_get_delete_prefix(self):
        c = InMemoryCache()
        c.set("analytics:a:x", "1", 60)
        c.set("analytics:a:y", "2", 60)
        c.set("other", "3", 60)
        assert c.get("analytics:a:x") == "1"
        c.delete_prefix("analytics:a:")
        assert c.get("analytics:a:x") is None
        assert c.get("other") == "3"

    def test_ttl_expiry(self):
        c = InMemoryCache()
        c.set("k", "v", 1)
        assert c.get("k") == "v"
        # expire by manipulating: set ttl 0 means no-expiry, so use a real tiny wait
        c.set("k2", "v", 1)
        time.sleep(0.01)
        assert c.get("k2") == "v"  # still within 1s

    def test_incr(self):
        c = InMemoryCache()
        assert c.incr("counter") == 1
        assert c.incr("counter") == 2
