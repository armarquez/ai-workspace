# Remediation solution design pattern

When designing a remediation solution in a design doc, structure the rollout to avoid breaking existing behavior. Always follow this sequence:

1. **Audit** — find and enumerate all existing violations (e.g., add logging to surface all service calls that would be affected)
2. **Stop the bleeding** — prevent new violations while preserving existing ones (e.g., allowlist known violations so enforcement only blocks net-new)
3. **Audit mode** — apply the new control in a non-blocking mode; capture data and populate/refine the allowlist without breaking anything
4. **Enforcement mode** — flip the control to enforce; existing allowlisted violations are still exempt
5. **Migrate violations** — work through the allowlist, moving each violation to the paved/secure path and removing it from the allowlist
6. **Remove escape hatches** — once the allowlist is empty, remove the allowlist mechanism and any other bypass paths including the stop-the-bleeding control

This pattern applies to any security control, policy enforcement, or breaking API change where existing callers must not be broken during rollout.
