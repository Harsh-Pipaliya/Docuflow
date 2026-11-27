# Walk through the demonstration

1. Run scripts/setup.ps1 and visit http://127.0.0.1:8080. Sign in as demo. Capture the dashboard.
2. Run the sample generator. Open Upload and select samples/generated/valid.pdf. Follow View document. Capture its four history entries and SHA-256.
3. Select unsupported.txt, then oversized.pdf. Capture each failed upload message. Verify the document count stays the same.
4. Upload corrupt.pdf. Open its detail page and show the failure code. Select Reprocess and find both attempts in the timeline.
5. Run scripts/run-all-tests.ps1. Show evidence/after/replay.json and the content-free redacted log. Repeat the download check and show Delete confirmation.
6. Open Integrations and explain the simulated processor hosting. Open a private browser window and visit the dashboard to verify the sign-in redirect.
