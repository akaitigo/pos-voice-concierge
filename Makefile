.PHONY: build test lint format check quality clean
.PHONY: build-backend test-backend lint-backend format-backend
.PHONY: build-voice test-voice lint-voice format-voice
.PHONY: build-frontend test-frontend lint-frontend format-frontend

# === Backend (Kotlin/Quarkus) ===
build-backend:
	cd backend && ./gradlew build

test-backend:
	cd backend && ./gradlew test

lint-backend:
	cd backend && ./gradlew detekt

format-backend:
	@echo "Backend formatting handled by detekt rules"

# === Voice Engine (Python) ===
VOICE_VENV := voice-engine/.venv/bin

build-voice:
	@echo "No build step for Python"

test-voice:
	cd voice-engine && $(CURDIR)/$(VOICE_VENV)/pytest

lint-voice:
	cd voice-engine && $(CURDIR)/$(VOICE_VENV)/ruff check .

format-voice:
	cd voice-engine && $(CURDIR)/$(VOICE_VENV)/ruff format . && $(CURDIR)/$(VOICE_VENV)/ruff check --fix .

# === Frontend (TypeScript/React) ===
build-frontend:
	cd frontend && npx tsc

test-frontend:
	cd frontend && npx vitest run

lint-frontend:
	cd frontend && npx oxlint . && npx biome check .

format-frontend:
	cd frontend && npx biome format --write .

# === Aggregate ===
build: build-backend build-voice build-frontend

test: test-backend test-voice test-frontend

lint: lint-backend lint-voice lint-frontend

format: format-backend format-voice format-frontend

check: format lint test build
	@echo "All checks passed."

quality:
	@echo "=== Quality Gate ==="
	@test -f LICENSE || { echo "ERROR: LICENSE missing. Fix: add MIT LICENSE file"; exit 1; }
	@test ! -f CLAUDE.md || [ $$(wc -l < CLAUDE.md) -le 50 ] || { echo "ERROR: CLAUDE.md is $$(wc -l < CLAUDE.md) lines (max 50). Fix: remove build details, use pointers only"; exit 1; }
	@echo "OK: automated quality checks passed"

clean:
	cd backend && ./gradlew clean || true
	cd voice-engine && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd frontend && rm -rf dist/ coverage/ node_modules/.cache/ || true
