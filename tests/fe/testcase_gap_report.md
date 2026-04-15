# FE Testcase Gap Closure Report

## Scope
- Source of truth: `docs/02_fe_testcases_V_0_2.md`
- Coverage target: implement automated tests for all documented FE testcase IDs.

## Result Summary
- Documented FE testcase IDs are now represented in `tests/fe` by explicit test functions with matching `TC-*` titles.
- Existing implemented suites retained:
  - `tests/fe/test_auth.py`
  - `tests/fe/test_customer.py`
- New suites added:
  - `tests/fe/test_auth_additional.py`
  - `tests/fe/test_navigation.py`
  - `tests/fe/test_dashboard.py`
  - `tests/fe/test_order.py`
  - `tests/fe/test_customer_hour.py`
  - `tests/fe/test_package.py`
  - `tests/fe/test_user.py`
  - `tests/fe/test_permission.py`
  - `tests/fe/test_booking.py`
  - `tests/fe/test_settings.py`
  - `tests/fe/test_cross.py`
  - `tests/fe/test_security.py`
  - `tests/fe/test_persistence.py`
  - `tests/fe/test_error_handling.py`
  - `tests/fe/test_cross_browser.py`
  - `tests/fe/test_signature_print.py`
  - `tests/fe/test_payment.py`
  - `tests/fe/test_activity_log.py`
  - `tests/fe/test_branch.py`
  - `tests/fe/test_caretaker.py`
  - `tests/fe/test_help.py`

## Helper/Infrastructure Updates
- Extended `tests/fe/helpers/common_web.py`:
  - Added robust testid alias support in locator resolution.
  - Added table fallbacks for components without `data-testid` row/cell attrs.
  - Added page-level UUID assertion.
  - Added sidebar label assertions and tablet viewport helper.
  - Added route-access helper used by new suites.
- Added baseline matrix:
  - `tests/fe/testcase_coverage_matrix.md`

## Blocked / XFail Testcases
The following IDs are implemented as test stubs with `pytest.mark.xfail` due to current product or fixture constraints:

- Auth flows not implemented in FE routes:
  - `TC-AUTH-07`, `TC-AUTH-11`, `TC-AUTH-12`, `TC-AUTH-13`
- Booking advanced/external/policy flows requiring backend fixtures or missing UI:
  - `TC-BOOK-05` to `TC-BOOK-15`
- Permission and role-propagation mutation flows requiring multi-user fixture chains:
  - `TC-PERM-02`, `TC-PERM-03`
- Branch/Caretaker/Activity log scenarios requiring deterministic branch datasets:
  - `TC-BRANCH-02`, `TC-CARE-01`, `TC-CARE-03`, `TC-LOG-05`, `TC-LOG-06`, `TC-LOG-07`
- Persistence/error UX not currently implemented as documented:
  - `TC-PERSIST-01` to `TC-PERSIST-03`
  - `TC-ERR-01`, `TC-ERR-02`, `TC-ERR-04`, `TC-ERR-05`
- Signature print route/functionality not present in current FE router:
  - `TC-PRINT-01` to `TC-PRINT-06`
- Payment tests requiring deterministic seeded installment/order/email fixtures:
  - `TC-PAY-01`, `TC-PAY-03`, `TC-PAY-04`, `TC-PAY-05`
- Cross-browser matrix requires dedicated Playwright browser project runs:
  - `TC-BROWSER-01`, `TC-BROWSER-02`
- Misc domain-fixture dependent cases:
  - `TC-DASH-07`, `TC-USER-03`, `TC-CROSS-02`, `TC-CROSS-03`, `TC-CROSS-04`, `TC-CROSS-06`, `TC-HELP-04`

## Validation Run Status
- `python -m compileall tests/fe` completed successfully (syntax validation passed).
- Full FE suite execution is currently blocked in this environment:
  - `pytest` not installed (`No module named pytest`).

## Next Actions to Fully Green the Suite
1. Install FE test runtime dependencies (`pytest`, Playwright bindings).
2. Ensure FE app and BE API test environments are running with stable seed fixtures.
3. Convert each `xfail` testcase to fully asserted passing tests as matching routes/features land.
4. Execute `python -m pytest tests/fe -q` and publish pass/fail and flaky-case list.

