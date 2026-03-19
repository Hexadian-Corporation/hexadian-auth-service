---
description: This instruction file provides guidelines for documenting and managing bug fixing history.
---

<critical>MANDATORY POLICY: Any bug discovered during development MUST be fixed and documented here, even if it falls outside the scope of the current task or issue being worked on. Do not defer, ignore, or leave bugs for later — fix them immediately and add an entry below.</critical>

# Bug History — hexadian-auth-service

Document every bug found and fixed during development. Include root cause, fix applied, and lesson learned so they don't recur.

---

## BUG-001: RSI bio parser regex outdated after RSI HTML change

**Issue:** #7 | **Severity:** Critical

**Symptom:** `POST /auth/verify/confirm` always returns `{"verified": false}` even when the verification code is correctly placed in the user's RSI profile bio.

**Root cause:** The RSI website changed its HTML structure. The bio field used to be `<span class="value" id="bioval">` but changed to a `<div class="entry bio"><div class="value">` structure. The regex no longer matched.

**Fix:** Updated `_BIO_PATTERN` in `rsi_profile_fetcher_impl.py` to match the new HTML structure.

**Status:** ✅ Fixed.

**Lesson:** External HTML scraping is inherently fragile. When a scraper-based feature stops working, always fetch the live HTML and compare against the expected regex. Consider adding an integration test that hits the real endpoint periodically to detect HTML changes early.

---

## BUG-002: OAuth token exchange fails with offset-naive vs offset-aware datetime TypeError

**Severity:** Critical

**Symptom:** `POST /auth/token/exchange` returns HTTP 500. Login on the auth-portal succeeds and redirects back to the backoffice callback, but the code exchange fails with `TypeError: can't compare offset-naive and offset-aware datetimes`.

**Root cause:** PyMongo returns `datetime` objects without timezone info (naive UTC). `auth_service_impl.py` compares these against `datetime.now(tz=UTC)` (aware). Python raises `TypeError` on naive/aware comparisons.

**Fix:** Added `replace(tzinfo=UTC)` in `AuthCodePersistenceMapper.to_domain()` and `RefreshTokenPersistenceMapper.to_domain()` — whenever `expires_at` is loaded with no tzinfo, it is tagged as UTC.

**Lesson:** PyMongo always returns naive UTC datetimes. Any comparison with `datetime.now(tz=UTC)` will crash. Fix at the persistence mapper layer. Pattern: `doc["expires_at"].replace(tzinfo=UTC) if doc["expires_at"].tzinfo is None else doc["expires_at"]`.
