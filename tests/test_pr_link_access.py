#!/usr/bin/env python3
"""
Test whether LLMs can access PR links directly.

This test demonstrates that API-based LLMs (OpenAI, Gemini) cannot
browse the web or access URLs - they can only process content sent
directly in the prompt.

Usage:
    OPENAI_API_KEY=xxx python tests/test_pr_link_access.py
"""

import os
import json
import sys

# Test configuration
TEST_PR_URL = "https://github.com/mehdic/bazinga/pull/129"
TEST_PR_TITLE = "Add OpenAI PR review pipeline (#129)"


def test_openai_pr_link_access():
    """Test if OpenAI can access and review a PR given only the link."""
    import requests

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("SKIP: OPENAI_API_KEY not set")
        return None

    print(f"\n{'='*60}")
    print("TEST: Can OpenAI access a GitHub PR link?")
    print(f"{'='*60}")
    print(f"PR URL: {TEST_PR_URL}")
    print(f"Expected PR Title: {TEST_PR_TITLE}")
    print()

    # Prompt that asks the model to access and review the PR
    prompt = f"""I need you to review a GitHub Pull Request.

Here is the PR link: {TEST_PR_URL}

Please:
1. Access the PR at the link above
2. Read the code changes (the diff)
3. Tell me the PR title
4. Provide a brief summary of what the PR does
5. List the files that were changed

If you cannot access the link, please say so clearly."""

    payload = {
        "model": "gpt-4o-mini",  # Using cheaper model for test
        "messages": [
            {"role": "system", "content": "You are a code reviewer. Be honest about your capabilities."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0
    }

    print("Sending request to OpenAI API...")

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        print(f"ERROR: API returned status {response.status_code}")
        print(response.text)
        return False

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    print("\n" + "-"*40)
    print("OpenAI Response:")
    print("-"*40)
    print(content)
    print("-"*40)

    # Analyze the response
    content_lower = content.lower()

    # Check if the model admits it cannot access the URL
    cannot_access_indicators = [
        "cannot access",
        "can't access",
        "unable to access",
        "don't have access",
        "cannot browse",
        "can't browse",
        "cannot visit",
        "can't visit",
        "no ability to access",
        "not able to access",
        "cannot retrieve",
        "can't retrieve",
        "cannot fetch",
        "can't fetch",
        "i don't have the ability",
        "i'm unable to",
        "i am unable to",
        "cannot directly access",
        "unable to browse",
        "cannot open",
        "can't open"
    ]

    admits_limitation = any(indicator in content_lower for indicator in cannot_access_indicators)

    # Check if it correctly identified the PR (it shouldn't be able to if it can't access)
    # The model might guess based on URL patterns, but shouldn't have actual content
    knows_pr_title = TEST_PR_TITLE.lower() in content_lower or "openai pr review" in content_lower

    print("\n" + "="*40)
    print("ANALYSIS:")
    print("="*40)
    print(f"Model admits it cannot access URL: {admits_limitation}")
    print(f"Model knows actual PR title: {knows_pr_title}")

    if admits_limitation:
        print("\n✅ CONFIRMED: OpenAI API cannot access PR links directly")
        print("   The model correctly states it cannot browse the web.")
        return True
    elif knows_pr_title:
        print("\n⚠️ UNEXPECTED: Model appears to know PR details")
        print("   This could be from training data or lucky guess.")
        return False
    else:
        print("\n⚠️ INCONCLUSIVE: Model response unclear")
        print("   May have hallucinated content without admitting limitation.")
        return False


def test_gemini_pr_link_access():
    """Test if Gemini can access and review a PR given only the link."""
    import requests

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("SKIP: GEMINI_API_KEY not set")
        return None

    print(f"\n{'='*60}")
    print("TEST: Can Gemini access a GitHub PR link?")
    print(f"{'='*60}")
    print(f"PR URL: {TEST_PR_URL}")
    print()

    prompt = f"""I need you to review a GitHub Pull Request.

Here is the PR link: {TEST_PR_URL}

Please:
1. Access the PR at the link above
2. Read the code changes (the diff)
3. Tell me the PR title
4. Provide a brief summary of what the PR does
5. List the files that were changed

If you cannot access the link, please say so clearly."""

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    print("Sending request to Gemini API...")

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        print(f"ERROR: API returned status {response.status_code}")
        print(response.text)
        return False

    result = response.json()

    try:
        content = result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        print("ERROR: Unexpected response format")
        print(json.dumps(result, indent=2))
        return False

    print("\n" + "-"*40)
    print("Gemini Response:")
    print("-"*40)
    print(content)
    print("-"*40)

    # Same analysis as OpenAI
    content_lower = content.lower()

    cannot_access_indicators = [
        "cannot access",
        "can't access",
        "unable to access",
        "don't have access",
        "cannot browse",
        "can't browse",
        "cannot visit",
        "can't visit",
        "no ability to access",
        "not able to access",
        "cannot retrieve",
        "can't retrieve",
        "cannot fetch",
        "can't fetch",
        "i don't have the ability",
        "i'm unable to",
        "i am unable to",
        "cannot directly access",
        "unable to browse",
        "cannot open",
        "can't open"
    ]

    admits_limitation = any(indicator in content_lower for indicator in cannot_access_indicators)
    knows_pr_title = TEST_PR_TITLE.lower() in content_lower or "openai pr review" in content_lower

    print("\n" + "="*40)
    print("ANALYSIS:")
    print("="*40)
    print(f"Model admits it cannot access URL: {admits_limitation}")
    print(f"Model knows actual PR title: {knows_pr_title}")

    if admits_limitation:
        print("\n✅ CONFIRMED: Gemini API cannot access PR links directly")
        return True
    elif knows_pr_title:
        print("\n⚠️ UNEXPECTED: Model appears to know PR details")
        return False
    else:
        print("\n⚠️ INCONCLUSIVE: Model response unclear")
        return False


def main():
    print("="*60)
    print("PR LINK ACCESS TEST")
    print("="*60)
    print()
    print("This test verifies that LLMs cannot access PR links directly.")
    print("The current pipeline approach (sending diff content) is correct")
    print("because models can only process content in the prompt.")
    print()

    results = {}

    # Test OpenAI
    openai_result = test_openai_pr_link_access()
    results["openai"] = openai_result

    # Test Gemini
    gemini_result = test_gemini_pr_link_access()
    results["gemini"] = gemini_result

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for provider, result in results.items():
        if result is None:
            status = "SKIPPED (no API key)"
        elif result:
            status = "✅ CONFIRMED cannot access URLs"
        else:
            status = "⚠️ INCONCLUSIVE"
        print(f"{provider.upper()}: {status}")

    print()
    print("CONCLUSION:")
    print("-"*40)
    print("LLMs accessed via API cannot browse the web or access URLs.")
    print("The current pipeline approach is CORRECT:")
    print("  1. Fetch diff content in GitHub Actions")
    print("  2. Send actual content to LLM in prompt")
    print("  3. LLM reviews the content it receives")
    print()
    print("Sending just a PR link would NOT work - models would either")
    print("admit they can't access it or hallucinate fake content.")

    # Return exit code based on results
    if all(r in (True, None) for r in results.values()):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
