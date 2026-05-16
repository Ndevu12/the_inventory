"""Django test runner that clears thread-local tenant context between tests."""

from __future__ import annotations

import logging
import unittest

from django.test.runner import DebugSQLTextTestResult, DiscoverRunner as DjangoDiscoverRunner

from tenants.context import clear_current_tenant

logger = logging.getLogger(__name__)


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
    """Runs the stock suite but resets tenant thread-locals for isolation.
    
    Also automatically excludes seeder tests unless explicitly requested.
    Seeder tests are included only when:
    - test_labels contains 'seeders' (e.g., 'tests.seeders', 'tests.seeders.test_base_seeder')
    """

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

    def build_suite(self, test_labels=None, **kwargs):
        """Build test suite, excluding seeder tests unless explicitly requested.
        
        Seeder tests are excluded by default. They are only included when:
        - test_labels contains a label with 'seeders' in it
        
        Args:
            test_labels: List of test labels to run (e.g., ['tests.api', 'tests.seeders'])
            **kwargs: Additional arguments passed to parent
            
        Returns:
            unittest.TestSuite: Filtered test suite
        """
        # If no test labels provided, default to discovering from 'tests' package
        if not test_labels:
            test_labels = ['tests']
        
        # Check if seeders are explicitly requested
        seeders_explicitly_requested = self._seeders_explicitly_requested(test_labels)
        
        # Build the full suite
        suite = super().build_suite(test_labels=test_labels, **kwargs)
        
        # If seeders NOT explicitly requested, filter them out
        if not seeders_explicitly_requested:
            initial_count = suite.countTestCases()
            suite = self._filter_out_seeders(suite)
            filtered_count = suite.countTestCases()
            excluded_count = initial_count - filtered_count
            
            if excluded_count > 0:
                logger.info(
                    f"Excluded {excluded_count} seeder test(s) from test suite. "
                    f"To run seeder tests, use: python manage.py test tests.seeders"
                )
        else:
            logger.info("Running seeder tests (explicitly requested)")
        
        return suite

    def _seeders_explicitly_requested(self, test_labels):
        """Check if seeder tests are explicitly requested via test_labels.
        
        Args:
            test_labels: List of test labels
            
        Returns:
            bool: True if any label contains 'seeders'
        """
        if not test_labels:
            return False
        
        for label in test_labels:
            if 'seeders' in label:
                return True
        
        return False

    def _filter_out_seeders(self, suite):
        """Recursively remove seeder tests from the test suite.
        
        Removes any test whose module path starts with 'tests.seeders'.
        
        Args:
            suite: unittest.TestSuite to filter
            
        Returns:
            unittest.TestSuite: Filtered suite without seeder tests
        """
        filtered_suite = unittest.TestSuite()
        
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                # Recursively filter nested suites
                nested_filtered = self._filter_out_seeders(test)
                if nested_filtered.countTestCases() > 0:
                    filtered_suite.addTest(nested_filtered)
            else:
                # Check individual test
                test_module = test.__class__.__module__
                if not test_module.startswith('tests.seeders'):
                    filtered_suite.addTest(test)
        
        return filtered_suite
