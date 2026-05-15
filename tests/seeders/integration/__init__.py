"""Integration tests for the seeding system.

Integration tests validate the full seeding pipeline with real database constraints,
tenant scoping, and CLI integration. These tests use TransactionTestCase and are slower
than unit tests but verify real-world behavior.

Test organization:
- test_seeder_pipeline_integration.py: Full SeederManager pipeline
- test_seed_command_integration.py: CLI command with database state
- test_data_integrity.py: Constraint validation and data integrity
- test_base_seeder_integration.py: BaseSeeder with real model constraints
"""
