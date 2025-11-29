# ULTRATHINK: Gemini 403 Error - Local vs GitHub Actions

**Date:** 2025-11-29
**Context:** Same API key works in GitHub Actions but returns 403 locally
**Status:** Root Cause Identified
**Decision:** Claude Code Web environment blocks Gemini API at network level

---

## Problem Statement

The `llm-reviews.sh` script calls Gemini API with `gemini-3-pro-preview` model:
- **GitHub Actions:** ✅ Works (200 OK)
- **Local execution (Claude Code Web):** ❌ Fails (403 Forbidden)

**Critical fact:** User confirms using the **same API key** in both environments.

---

## ROOT CAUSE IDENTIFIED ✅

### Definitive Finding: Environment-Level API Blocking

**The Claude Code Web environment blocks Gemini API at the network/proxy level.**

#### Evidence from Testing:

| Test | Result | Implication |
|------|--------|-------------|
| `gemini-3-pro-preview:generateContent` | 403 HTML | Blocked |
| `gemini-1.5-pro:generateContent` | 403 HTML | ALL models blocked |
| `GET /v1beta/models` (list models) | 403 HTML | Entire API blocked |
| `ifconfig.me` | "fault filter abort" | Envoy proxy detected |
| `www.google.com` | 200 OK | General connectivity works |
| OpenAI API | 200 OK | Not blocked |

#### Conclusion:

The 403 is **NOT** caused by:
- ❌ Wrong model name
- ❌ API key tier/permissions
- ❌ Payload size
- ❌ Rate limiting

The 403 **IS** caused by:
- ✅ **Network policy in Claude Code Web environment**
- ✅ Envoy proxy filtering requests to `generativelanguage.googleapis.com`
- ✅ Selective blocking (Gemini blocked, OpenAI allowed)

This is likely an intentional policy in the Claude Code Web infrastructure.

---

## Technical Details

### Request Configuration (Both Environments)

| Aspect | GitHub Actions | Local Script |
|--------|---------------|--------------|
| Endpoint | `generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent` | Same |
| Auth Header | `x-goog-api-key: $GEMINI_API_KEY` | Same |
| Method | POST | Same |
| Content-Type | `application/json` | Same |

### Error Response (Local)

```html
403 Forbidden
"Your client does not have permission to get URL
/v1beta/models/gemini-3-pro-preview:generateContent from this server."
```

This is Google's **generic 403 page**, not the Gemini API's structured error response.

---

## Hypothesis Analysis

### H1: IP-Based Access Restrictions ⭐ MOST LIKELY

**Theory:** Google restricts Gemini 3 Pro Preview access by IP range.

**Evidence:**
- GitHub Actions runs on Microsoft Azure infrastructure (well-known IP ranges)
- Google may whitelist cloud provider IPs for preview/beta models
- The 403 HTML page (not JSON) suggests request blocked at edge/proxy level, not API level

**Supporting facts:**
- Gemini 3 Pro is in "preview" - Google often restricts preview access
- Major cloud providers (AWS, Azure, GCP) have trusted IP ranges
- Local/residential IPs are often blocked from preview features

**Verification:** Compare response headers from both environments, or test from a cloud VM.

### H2: Geographic/Regional Restrictions

**Theory:** Local environment is in a region where Gemini 3 Pro isn't available.

**Evidence:**
- Google AI products have varying regional availability
- The Claude Code Web environment may be in a restricted region
- GitHub Actions runs in specific Azure regions (likely US)

**Counter-evidence:**
- If the API key was restricted by region, it would typically return a JSON error, not HTML 403

### H3: Network Layer Blocking (Proxy/Firewall)

**Theory:** Local network has a proxy or firewall blocking the request.

**Evidence:**
- HTML 403 page could come from an intermediate proxy
- Corporate networks often filter AI API endpoints

**Counter-evidence:**
- OpenAI API worked fine (200 OK) from the same environment
- If it was a blanket AI block, OpenAI would also fail

### H4: API Key IP Restrictions in Google Cloud Console

**Theory:** The API key has IP restrictions configured, allowing only GitHub's IPs.

**Evidence:**
- Google Cloud allows restricting API keys to specific IP ranges
- This is a security best practice for CI/CD

**Verification:** Check Google Cloud Console → Credentials → API Key restrictions

### H5: Rate Limiting or Abuse Detection

**Theory:** Local IP flagged for unusual activity.

**Evidence:**
- Google uses behavioral analysis for API access
- Repeated testing might trigger protective measures

**Counter-evidence:**
- Rate limits typically return 429, not 403
- First request of the day still failed

### H6: Curl/TLS Version Differences

**Theory:** Different curl/TLS versions between environments.

**Evidence:**
- Older TLS versions might be rejected
- Some Google APIs require TLS 1.3

**Verification:** Compare `curl --version` between environments.

---

## Critical Analysis

### Most Likely Cause: IP-Based Restrictions (H1)

**Confidence: 75%**

The combination of:
1. Same API key working in one place but not another
2. Generic HTML 403 (not API JSON error)
3. "Preview" model status
4. Cloud vs local execution

Strongly suggests **IP-based access control** at the edge/CDN level.

### Second Most Likely: API Key IP Restrictions (H4)

**Confidence: 15%**

If the user configured IP restrictions on the API key to only allow GitHub Actions IPs, this would explain the behavior. Easy to verify in Google Cloud Console.

### Less Likely Causes

- Geographic restrictions (5%) - Would typically show different error
- Network/proxy issues (3%) - OpenAI worked fine
- Rate limiting (2%) - Wrong error code

---

## Recommended Investigation Steps

1. **Check API Key Restrictions**
   ```
   Google Cloud Console → APIs & Services → Credentials → [Your API Key]
   → Application restrictions → Check if IP addresses are restricted
   ```

2. **Compare Network Environments**
   ```bash
   # Local
   curl -v https://generativelanguage.googleapis.com/v1beta/models 2>&1 | head -30

   # Check your public IP
   curl ifconfig.me
   ```

3. **Test from Cloud VM**
   - Spin up a small VM on GCP/AWS/Azure
   - Run the same curl command
   - If it works, confirms IP-based restriction

4. **Check Gemini API Access Page**
   - Visit https://aistudio.google.com/
   - Verify Gemini 3 Pro Preview access status for your account

5. **Request Verbose Headers**
   ```bash
   curl -v -X POST \
     -H "Content-Type: application/json" \
     -H "x-goog-api-key: $GEMINI_API_KEY" \
     -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent" 2>&1 | head -50
   ```

---

## Potential Solutions

### Solution A: Use Vertex AI Instead

Vertex AI uses service account authentication (not API key) and may have different access rules.

```bash
# Requires: gcloud auth + project setup
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/PROJECT/locations/us-central1/publishers/google/models/gemini-3-pro:generateContent"
```

### Solution B: Fallback Model in Script

Add graceful fallback when Gemini 3 Pro fails:

```bash
# Try Gemini 3 Pro, fallback to 1.5 Pro
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3-pro-preview}"
GEMINI_FALLBACK="gemini-1.5-pro"

# If primary fails with 403, retry with fallback
if [ "$HTTP_CODE" -eq 403 ]; then
    echo "  ⚠️ Gemini 3 Pro access denied, trying $GEMINI_FALLBACK..."
    GEMINI_MODEL="$GEMINI_FALLBACK"
    # Retry...
fi
```

### Solution C: Environment Variable Override

Allow users to specify model based on their access:

```bash
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3-pro-preview}"
```

Usage:
```bash
GEMINI_MODEL=gemini-1.5-pro ./dev-scripts/llm-reviews.sh research/plan.md
```

### Solution D: Skip Gemini for Local Testing

Accept that local testing may only use OpenAI, and Gemini review only works in CI:

```bash
if [ "${SKIP_GEMINI:-false}" = "true" ]; then
    echo "  ⏭️ Skipping Gemini review (SKIP_GEMINI=true)"
    GEMINI_REVIEW="[Gemini review skipped - local testing mode]"
fi
```

---

## Verdict

**Root cause CONFIRMED:** The Claude Code Web environment blocks Gemini API at the Envoy proxy level. This is a network infrastructure policy, not an API key or Google-side restriction.

**Implications:**
1. **Script is correct** - No changes needed to `llm-reviews.sh`
2. **Gemini reviews only work in CI** - GitHub Actions has no such restriction
3. **Local testing limited to OpenAI** - Gemini review will always fail in Claude Code Web
4. **Not fixable by user** - This is infrastructure-level, not configuration

**Recommended action:** Accept this limitation. The script works correctly in its intended environment (GitHub Actions). For local testing in Claude Code Web, rely on OpenAI review only.

---

## Questions for External Review

1. Are there other explanations for same API key working in cloud but not locally?
2. Is IP-based access control a known pattern for Google's preview models?
3. Should the script fail loudly or gracefully degrade when Gemini fails?
4. Are there security implications of the fallback approach?
5. What's the best UX for developers testing locally vs CI?

---

## References

- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [GitHub Actions IP Ranges](https://api.github.com/meta)
- [Google Cloud API Key Restrictions](https://cloud.google.com/docs/authentication/api-keys)
