# Justfile for python-qrcode
# Modern development commands using uv

# Default recipe - show available commands
default:
	@just --list

# Run tests
# Usage:
#   just test                                  -> run all test matrices + coverage
#   just test quick                            -> quick test with current Python (no coverage)
#   just test [3.10|3.11|...]                  -> run specific python version (all variants)
#   just test [3.10|...] [pil|png|none]        -> run specific python and variant
test *ARGS='':
	#!/usr/bin/env bash
	set -euo pipefail

	ARGS=( {{ ARGS }} )

	if [ ${#ARGS[@]} -eq 0 ]; then
		# No args: run all
		echo "Running all test environments..."
		just _test-matrix
		just _coverage-report
	elif [ ${#ARGS[@]} -eq 1 ]; then
		ARG="${ARGS[0]}"
		if [ "$ARG" = "quick" ]; then
			 uv run --quiet --group dev pytest -q
		elif [[ "$ARG" =~ ^3\.[0-9]+$ ]]; then
			 # Run all variants for this python version
			 just _test-env "$ARG" pil
			 just _test-env "$ARG" png
			 just _test-env "$ARG" none
		else
			 echo "Unknown argument: $ARG"
			 exit 1
		fi
	elif [ ${#ARGS[@]} -eq 2 ]; then
		just _test-env "${ARGS[0]}" "${ARGS[1]}"
	else
		echo "Usage: just test [quick | PYTHON_VER | PYTHON_VER VARIANT]"
		exit 1
	fi

# Run all test environments (internal)
_test-matrix:
	#!/usr/bin/env bash
	set -e
	echo "Cleaning old coverage files..."
	rm -rf .coverage* htmlcov
	for py in 3.10 3.11 3.12 3.13 3.14; do
		just _test-env $py pil
		just _test-env $py png
		just _test-env $py none
	done

# Run a specific test environment (internal)
_test-env PYTHON VARIANT:
	@printf "Testing: Python %-5s - %-5s " "{{ PYTHON }}" "{{ VARIANT }}"
	@if [ "{{ VARIANT }}" = "pil" ]; then \
		uv run --quiet --python {{ PYTHON }} --extra pil --group dev coverage run -m pytest -q; \
	elif [ "{{ VARIANT }}" = "png" ]; then \
		uv run --quiet --python {{ PYTHON }} --extra png --group dev coverage run -m pytest -q; \
	elif [ "{{ VARIANT }}" = "none" ]; then \
		uv run --quiet --python {{ PYTHON }} --group dev coverage run -m pytest -q; \
	else \
		echo "Unknown variant: {{ VARIANT }}"; exit 1; \
	fi
	@echo "✓"

# Generate coverage report (internal)
_coverage-report:
	@uv run --quiet --group dev coverage combine --quiet .coverage* 2>/dev/null || true
	@echo ""
	@echo "Test coverage:"
	@uv run --quiet --group dev coverage report -m
	@uv run --quiet --group dev coverage html
	@echo "Coverage report saved to htmlcov/index.html"

# Run all checks (format, lint, tests)
check:
	@echo "Running all checks..."
	@echo "→ Formatting..."
	@uv run --quiet ruff format --check qrcode
	@echo "→ Linting..."
	@uv run --quiet ruff check qrcode
	@echo "→ Testing..."
	@just test
