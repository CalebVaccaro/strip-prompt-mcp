#!/usr/bin/env python3
"""
Compression benchmark across representative input scenarios.
Measures word and character reduction percentage for each scenario
and reports an average — used to validate README cost savings claims.

Run: python test_compression.py
"""

import sys
from compressor import compress

SCENARIOS = [
    {
        "name": "Short casual prompt",
        "text": "Hey, can you please help me understand why the authentication service is failing intermittently?",
    },
    {
        "name": "Developer freeform question",
        "text": (
            "I am trying to figure out the best approach for handling the WebRTC fallback in our "
            "mobile controller. We currently have a UDP path that works well but we need to ensure "
            "that when UDP is not available the WebRTC DataChannel is able to take over seamlessly "
            "without the user experiencing any noticeable disruption. How should we approach this?"
        ),
    },
    {
        "name": "Jira bug report",
        "text": (
            "Summary: User authentication fails intermittently on mobile devices\n\n"
            "Description:\n"
            "We are seeing intermittent authentication failures on mobile devices specifically when "
            "users attempt to log in through the mobile app. The issue appears to be related to the "
            "token refresh mechanism that is currently in place for handling expired sessions.\n\n"
            "Steps to reproduce:\n"
            "1. Log in to the mobile application using valid credentials\n"
            "2. Leave the application idle for approximately 30 minutes\n"
            "3. Attempt to perform any action that requires authentication\n"
            "4. Observe that the user is not redirected to the login screen but instead receives a generic error message\n\n"
            "Expected behavior:\n"
            "The application should automatically refresh the authentication token in the background "
            "and allow the user to continue their session without interruption. If the token cannot "
            "be refreshed then the user should be redirected to the login screen with a clear message "
            "explaining why they need to log in again.\n\n"
            "Actual behavior:\n"
            "The user receives a generic error message that does not explain the issue. The application "
            "does not attempt to refresh the token and does not redirect the user to the login screen. "
            "This results in a broken state where the user must manually close and reopen the "
            "application to resolve the issue.\n\n"
            "Additional context:\n"
            "This issue has been reported by multiple users across both iOS and Android platforms. "
            "It does not appear to affect desktop or web users. The issue was first reported after "
            "the deployment of version 2.4.1 which included changes to the session management system."
        ),
    },
    {
        "name": "Jira feature request",
        "text": (
            "Summary: Add dark mode support to the settings screen\n\n"
            "As part of our ongoing initiative to improve the overall user experience of the application, "
            "we would like to explore opportunities to add a dark mode option to the settings screen. "
            "This is something that has been requested by a significant number of users through the "
            "feedback portal and we believe it would be beneficial to prioritize this improvement in "
            "the upcoming sprint. The implementation should respect the system-level preference where "
            "possible and also allow users to manually override it through the application settings. "
            "It is important to note that this should not introduce any regressions in the existing "
            "light mode experience."
        ),
    },
    {
        "name": "Jira task / technical ticket",
        "text": (
            "Summary: Refactor session management module to use repository pattern\n\n"
            "The current implementation of the session management module is tightly coupled to the "
            "underlying database layer which has resulted in significant difficulties when attempting "
            "to write unit tests. We are required to refactor this module in order to introduce a "
            "repository abstraction that will allow us to mock the data layer in tests. This work "
            "should also include updating the existing integration tests to ensure that they continue "
            "to pass after the refactor is complete. Please provide a detailed breakdown of the "
            "changes that will be needed across the affected files."
        ),
    },
    {
        "name": "Agile / PM style story",
        "text": (
            "As a user I want to be able to reset my password from the login screen so that I can "
            "regain access to my account if I have forgotten my credentials. The reset flow should "
            "send a time-limited link to the email address associated with my account and that link "
            "should expire after 24 hours. It is important to ensure that the link can only be used "
            "once and that the user is informed if they attempt to use an expired or already consumed link."
        ),
    },
    {
        "name": "Customer support request",
        "text": (
            "Hello, I am reaching out because I have been having a lot of trouble with my account "
            "over the past few days. Basically, I am unable to log in and when I try to reset my "
            "password I never receive the reset email even though I have checked my spam folder "
            "multiple times. I have tried using both my work email and my personal email address "
            "and neither of them seems to be working. Could you please help me understand what is "
            "happening and potentially escalate this to someone who can investigate further?"
        ),
    },
    {
        "name": "Technical documentation excerpt",
        "text": (
            "The authentication service is responsible for validating incoming requests and issuing "
            "short-lived access tokens to authenticated clients. It is built on top of the standard "
            "OAuth 2.0 authorization code flow and relies on a shared secret that is rotated on a "
            "quarterly basis. All tokens are signed using RS256 and have a default expiry of 15 "
            "minutes. Clients are expected to use the refresh token endpoint in order to obtain a "
            "new access token before the current one expires. It should be noted that refresh tokens "
            "are single-use and a new refresh token is issued alongside each new access token."
        ),
    },
    {
        "name": "Meeting notes / async update",
        "text": (
            "Just wanted to provide a quick update on where things stand with the migration work. "
            "We have completed the initial schema changes and those are currently being reviewed by "
            "the backend team. We are hoping to have that review finished by end of day Thursday so "
            "that we can move on to the data backfill scripts. There are still a few open questions "
            "around how we want to handle the rollback strategy and we are planning to discuss that "
            "in the architecture sync tomorrow. With that said we are still on track for the end of "
            "sprint milestone assuming the review does not surface any major issues."
        ),
    },
    {
        "name": "Slack-style developer message",
        "text": (
            "Hey team, just a heads up that the staging environment is going to be unavailable for "
            "approximately two hours this afternoon while we apply the database migration. Please "
            "make sure that you have pushed any work in progress before 2pm so that you are not "
            "blocked. If you need access to a test environment during that window please let me know "
            "and I can potentially set something up for you. Thanks everyone for your patience."
        ),
    },
]


def word_count(text: str) -> int:
    return len(text.split())


def char_count(text: str) -> int:
    return len(text)


def run():
    results = []
    col_w = 36

    print(f"\n{'Scenario':<{col_w}} {'Words':>10} {'→':>3} {'Words':>10}  {'Word %':>7}  {'Char %':>7}")
    print(f"{'':{'─'}<{col_w}} {'(orig)':>10} {'':>3} {'(comp)':>10}  {'reduc.':>7}  {'reduc.':>7}")

    for s in SCENARIOS:
        orig = s["text"]
        comp = compress(orig)
        ow, cw = word_count(orig), word_count(comp)
        oc, cc = char_count(orig), char_count(comp)
        word_pct = (ow - cw) / ow * 100 if ow else 0
        char_pct = (oc - cc) / oc * 100 if oc else 0
        results.append({"name": s["name"], "word_pct": word_pct, "char_pct": char_pct})
        label = s["name"][:col_w]
        print(f"{label:<{col_w}} {ow:>10} {'→':>3} {cw:>10}  {word_pct:>6.1f}%  {char_pct:>6.1f}%")

    avg_word = sum(r["word_pct"] for r in results) / len(results)
    avg_char = sum(r["char_pct"] for r in results) / len(results)

    print(f"\n{'─' * (col_w + 46)}")
    print(f"{'Average across all scenarios':<{col_w}} {'':>24}  {avg_word:>6.1f}%  {avg_char:>6.1f}%")
    print(f"\nScenario count : {len(results)}")
    print(f"Avg word reduction : {avg_word:.1f}%")
    print(f"Avg char reduction : {avg_char:.1f}%")
    print()


if __name__ == "__main__":
    run()
