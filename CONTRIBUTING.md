# Working as a team

Start from main. Use git switch -c feature/short-description, enable the hook with git config core.hooksPath .githooks, and keep changes small. Run the local test script before pushing. Open a pull request to main and have a second team member check the test evidence. Preserve baseline-v0. Keep .env, demo passwords and custom files out of commits.

The workflow architect reviews state and event contracts. The cloud engineer owns Floci readiness; the API engineer owns sessions, validation and private downloads. The reliability engineer reviews parser and event handling. The test engineer owns fixtures, evidence and the demo. Rotate presenters so each person can explain the whole path.

The integrated revision includes parser traversal, state guard tests, API filtering, drag-and-drop behavior and demo tooling adapted from gauravv3107/Docuflow-SubMain at 512e4a75c50926486a277ebd0c2a8325468fecce. The tests and screenshots in this checkout were run against the combined application.
