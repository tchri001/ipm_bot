# Copilot Session-End Trigger

When the user indicates the session is ending, run this wrap-up routine before final response.

## Trigger phrases
Treat these as a session-end trigger:
- "end session"
- "session wrap-up"
- "wrap up for today"
- "close out session"
- "cheers dude"
- "thanks for the help"
- "see ya"

## Required wrap-up actions
1. Update `PROJECT_CONTEXT.md` with any new architecture, function, logging, debugging, or workflow changes made in the current session.
2. Update `BOOTSTRAP_CHECKLIST.md` if startup or run steps changed.
3. Update persistent memory with a concise summary of new durable facts:
   - `/memories/repo/ipm_bot-context.md`
   - `/memories/user-preferences.md` only if user preferences changed.
4. In the final response, explicitly list what was updated.

## Constraints
- Do not add speculative behavior. Only record verified changes from this session.
- Keep summaries concise and factual.
