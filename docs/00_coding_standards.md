# Coding Standards
## Pila Studio Management

> These rules apply to **all code** written in this project — backend, frontend, and tests.

---

## Algorithm Documentation Rule

**Every line of algorithm logic must have an inline comment explaining what it does, written as a tutorial for a starter developer.**

This means:
- Not just *what* the line does, but *why* it exists
- Assume the reader is learning — no logic is "too obvious" to explain
- Business rules especially must be explained in plain language

---

### Example — Session Deduction (Python)

```python
def deduct_session(customer_id: str, db: Session) -> SessionBalance:

    # Fetch the customer's current session record from the database
    # We lock the row (with_for_update) to prevent two requests from deducting at the same time
    balance = db.query(SessionBalance)\
                .filter(SessionBalance.customer_id == customer_id)\
                .with_for_update()\
                .first()

    # If no session record found, the customer doesn't exist or was never assigned sessions
    if not balance:
        raise ValueError("Customer session record not found")

    # Business rule: a customer cannot have a negative session balance
    # If they have 0 sessions left, we stop here and return an error
    if balance.remaining <= 0:
        raise ValueError("No remaining sessions to deduct")

    # Subtract 1 from the remaining session count
    # Each call to this function represents one class/session attended
    balance.remaining -= 1

    # Record the deduction in the transaction log for audit purposes
    # This is how admins can trace every session change (before/after)
    log_entry = SessionTransactionLog(
        customer_id=customer_id,          # who the session belongs to
        transaction_type="DEDUCT",        # what kind of change (deduct vs add vs adjust)
        before=balance.remaining + 1,     # the balance BEFORE this deduction
        amount=1,                         # how many sessions were removed
        after=balance.remaining,          # the balance AFTER this deduction
    )

    # Add the log entry to the database session (not committed yet)
    db.add(log_entry)

    # Save all changes to the database in one atomic transaction
    # If anything fails above, nothing is saved (all-or-nothing)
    db.commit()

    # Refresh the balance object so it reflects the newly saved state
    db.refresh(balance)

    # Return the updated balance so the API response can show the new remaining count
    return balance
```

---

### Example — Customer Code Generator (Python)

```python
def generate_customer_code(branch_prefix: str, source_code: str, db: Session) -> str:

    # Count how many customers already exist with this exact branch + source combination
    # This gives us the running number for the new customer's code
    existing_count = db.query(Customer).filter(
        Customer.branch_prefix == branch_prefix,   # e.g. "BPY" for Pattaya
        Customer.source_code == source_code        # e.g. "MKT" for social media leads
    ).count()

    # The next number is one more than the current count
    # Example: if 3 customers exist → next running number = 4
    next_number = existing_count + 1

    # Format the running number as a zero-padded 3-digit string
    # Example: 4 → "004", 10 → "010"
    padded_number = str(next_number).zfill(3)

    # Combine all parts to form the full customer code
    # Format: [BranchPrefix]-[SourceCode][RunningNumber]
    # Example: "BPY" + "-" + "MKT" + "004" → "BPY-MKT004"
    customer_code = f"{branch_prefix}-{source_code}{padded_number}"

    return customer_code
```

---

### Example — Role Guard Decorator (Python)

```python
def require_roles(*allowed_roles: str):
    """
    A decorator factory that blocks access if the current user's role
    is not in the list of allowed roles.
    Usage: @require_roles("owner", "admin")
    """

    def decorator(func):
        @wraps(func)  # preserve the original function's name and docstring
        def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):

            # Check if the user's role is in the list of roles that are allowed
            # Example: if allowed_roles = ("owner", "admin") and user.role = "master" → blocked
            if current_user.role not in allowed_roles:
                # Return a 403 Forbidden error — the user is authenticated but not authorized
                raise HTTPException(
                    status_code=403,
                    detail=f"Role '{current_user.role}' does not have access to this resource"
                )

            # If the role check passes, call the original route function
            return func(*args, current_user=current_user, **kwargs)

        return wrapper
    return decorator
```

---

### Example — Playwright FE Test (Python)

```python
def test_customer_dropdown_shows_name_not_uuid(page: Page):
    """
    Critical regression test: the old system showed raw UUIDs in customer dropdowns.
    This test ensures customers are always identified by name + code, never by UUID.
    """

    # Log in as an admin user so we can access the session deduct page
    login_as(page, role="admin")

    # Navigate to the session deduction page where the customer dropdown lives
    page.goto("/sessions/deduct")

    # Click the customer dropdown to open it
    page.click("[data-testid='customer-select']")

    # Get all the option texts from the dropdown list
    options = page.locator("[data-testid='customer-option']").all_text_contents()

    # Loop through every option and verify it does NOT look like a UUID
    # A UUID looks like: "550e8400-e29b-41d4-a716-446655440000"
    # We check by looking for the UUID pattern (8-4-4-4-12 hex characters with dashes)
    uuid_pattern = re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        re.IGNORECASE
    )

    for option_text in options:
        # Assert that this option text contains no UUID — it should show a name instead
        assert not uuid_pattern.search(option_text), (
            f"Dropdown option contains a raw UUID: '{option_text}'. "
            f"It should show the customer name and code instead."
        )
```

---

## Summary Rules

| Rule | Description |
|------|-------------|
| Every algorithm line | Has an inline `#` comment explaining what and why |
| Business rules | Explained in plain Thai or English, not just code terms |
| Guard clauses | Always explain what condition is being blocked and why |
| DB operations | Explain what is being queried/saved and the effect |
| Test assertions | Explain what bug this test is preventing |
| Magic numbers | Never use unexplained numbers — always name them with a constant or comment |
