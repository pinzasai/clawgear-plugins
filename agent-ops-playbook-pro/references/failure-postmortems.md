# Failure Post-Mortems

Real incidents from production agent deployments. Each one caused a different failure mode.
Each one created a rule that now lives in AGENTS.md.

---

## Incident 1: Credentials Lost After Session

**What happened:** An npm publish token and a key decision (open source the project) were communicated in a session and acknowledged by the agent. The next morning, neither was in MEMORY.md or any project file. Reconstructing required digging through git log and re-asking the user.

**Root cause:** The agent said "noted" and treated it as a mental note. Write-through to MEMORY.md was skipped. The nightly heartbeat ran but didn't know to write what it never saw.

**Time lost:** ~2 hours of reconstruction + user frustration

**Rule created:**
> Write to MEMORY.md in the same turn credentials or decisions are received. Not "at the end of the session." Not "in the next heartbeat." Now.

**Specific trigger:** Any time a user says "remember," "use this token," "we decided," or "the password is" — stop, write to file, then continue.

---

## Incident 2: Total Exec Lockout (1 Hour)

**What happened:** An exec host config was changed to `host: node` to test node-level execution. No paired nodes were configured. Result: every exec call returned "denied" — no shell access, no debugging capability, no way to check the config that caused the problem.

**Root cause:** `host: node` with no paired nodes = total exec deny. The config change that caused the lockout couldn't be fixed without exec access. Circular dependency.

**Time lost:** ~1 hour of manual config debugging by the user

**Rule created:**
> Never set `tools.exec.host` to `node` without a confirmed paired node. Use `sandbox` as the safe default. If you're unsure whether a node is paired, assume it isn't.

**Recovery:** Had to manually edit openclaw.json via text editor to restore `host: sandbox`.

---

## Incident 3: Provider Account Shutdown

**What happened:** The primary Google account (Gmail, Calendar, Drive) was disabled by Google overnight. All OAuth tokens stopped working. The Shodan account activation email was in the now-dead Gmail inbox. Calendar integration died. MCP server became non-functional.

**Root cause:** Single-provider dependency for critical infrastructure. No fallback email. No backup OAuth provider.

**Time lost:** Half a day rebuilding around ProtonMail as the new primary email

**Rule created:**
> Don't depend on one provider for critical infrastructure. Always have a fallback email. Credentials and recovery options should not flow through the same account they protect.

**Specific lesson:** Set up backup email immediately when creating any account, before you need it.

---

## Incident 4: Memory Drift Across 3 Projects

**What happened:** After a full day of active work across three projects, the nightly heartbeat found that TASKS.md and MEMORY.md for all three projects were stale. Daily notes had the work logged correctly, but project files hadn't been updated. Status was being reported from stale files.

**Root cause:** The nightly heartbeat was being treated as the *primary* memory write mechanism instead of a safety net. During the day, write-throughs were skipped in favor of "the heartbeat will catch it."

**Time lost:** ~30 minutes of nightly reconciliation, plus incorrect status reports during the day

**Rule created:**
> The nightly heartbeat audit is a SAFETY NET — it catches write-throughs that slipped through. It is NOT the primary write mechanism. If the nightly audit is doing most of the memory writing, the real-time write-through system is broken.

**Enforcement:** The memory sync validator (`scripts/memory-sync.sh`) now runs every heartbeat (not just nightly) and blocks commits when project files are stale.

---

## Pattern: What All Four Have in Common

Every failure happened through a different path:
- Incident 1: Agent skipped a write-through
- Incident 2: Config change with unintended side effects
- Incident 3: External dependency failure
- Incident 4: Nightly batch replacing real-time updates

The common thread: **the system had no enforcement layer.** Rules existed but nothing checked them.

The fix in every case was adding machine enforcement:
- Write-through: sync validator runs every heartbeat
- Exec config: documented safe defaults with explicit warnings
- Provider dependency: documented recovery paths and backup accounts
- Batch vs real-time: pre-commit hook blocks stale commits

**Lesson:** Don't rely on the agent remembering the rules. Build checks that catch failures before they compound.
