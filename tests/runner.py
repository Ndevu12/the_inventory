"""Django test runner that clears thread-local tenant context between tests."""

from __future__ import annotations

import unittest

from django.test.runner import DebugSQLTextTestResult, DiscoverRunner as DjangoDiscoverRunner

from tenants.context import clear_current_tenant


class _ClearTenantTextTestResult(unittest.TextTestResult):
    def startTest(self, test):
        clear_current_tenant()
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        clear_current_tenant()


class _ClearTenantDebugSQLTextTestResult(DebugSQLTextTestResult):
    def startTest(self, test):
        clear_current_tenant()
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        clear_current_tenant()


class DiscoverRunner(DjangoDiscoverRunner):
    """Runs the stock suite but resets tenant thread-locals for isolation."""

    def get_resultclass(self):
        base = super().get_resultclass()
        if base is None:
            return _ClearTenantTextTestResult
        if base is DebugSQLTextTestResult:
            return _ClearTenantDebugSQLTextTestResult

        class Wrapped(base):  # type: ignore[misc,valid-type]
            def startTest(self, test):
                clear_current_tenant()
                super().startTest(test)

            def stopTest(self, test):
                super().stopTest(test)
                clear_current_tenant()

        return Wrapped
