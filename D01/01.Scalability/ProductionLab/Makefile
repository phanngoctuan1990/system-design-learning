.PHONY: test test-core test-models test-adapters clean

# Run core business logic tests
test-core:
	python3 -m unittest tests.unit.test_core_only -v

# Run domain models tests  
test-models:
	python3 -m unittest tests.unit.test_models -v

# Run adapter tests
test-adapters:
	python3 -m unittest tests.unit.test_memory_adapter -v

# Run all available tests
test: test-models test-adapters test-core
	@echo "All tests completed!"

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
