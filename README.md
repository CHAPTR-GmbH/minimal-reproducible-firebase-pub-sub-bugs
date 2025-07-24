# Minimal Reproducible Test for Firebase Cloud Functions Emulator Issues

This is a minimal setup to reproduce specific behavior and issues with Cloud Functions and Pub/Sub topics on the Firebase emulator.

## Setup and Commands

### Prerequisites
- Docker and Docker Compose
- Make

### Running the Tests

1. **Start the environment:**
   ```bash
   make compose
   ```
   This will automatically detect your platform (Mac/Linux) and start all required services.

2. **Run the tests:**
   ```bash
   make test
   ```

## Expected Behavior and Issues

### First Run
- **First test will fail**: Pub/Sub seems to lose the first message for some reason when the emulator is just started
- **Second test will succeed**: The test that updates 100 products should work properly

### Second Run (Immediately)
- **Tests fail randomly**: The emulator appears to kill functions after 30 seconds regardless of configuration, breaking tests

### Second Run (After Functions Cool Down)
If you check the console and see that functions have ended like this:
```
firebase-1   | i  functions: Finished "europe-west4-products_sync_bulk" in 29054.191729ms
firebase-1   | i  functions: Finished "europe-west4-products_sync_bulk" in 29056.899779ms
firebase-1   | i  functions: Finished "europe-west4-products_sync_bulk" in 29055.842414ms
firebase-1   | i  functions: Finished "europe-west4-products_sync_bulk" in 29057.540609ms
firebase-1   | i  functions: Finished "europe-west4-products_sync_bulk" in 29058.24203ms
firebase-1   | i  functions: Finished "europe-west4-products_sync_bulk" in 29056.543984ms
firebase-1   | i  functions: Finished "europe-west4-products_sync_bulk" in 29051.259175ms
firebase-1   | i  functions: Finished "europe-west4-products_sync_bulk" in 29010.059986ms
```

Then running the tests again should result in both tests passing.

## Issues for Google Team Investigation

### 1. Random Connection Errors
In our full test suite, we sometimes see unexplained random errors such as:
- `firebase Connection in use: ('127.0.0.1', 8996)`
- `Error: socket hang up`
- `ERRCONNRESET`
- `function failed to load`

### 2. Function Instance Management
The `@pubsub_fn` decorator creates many instances on the emulator, despite being configured with:
```python
min_instances=1,
max_instances=1,
concurrency=1,
```

**Question**: Please verify this behavior against the expected implementation. Should the emulator respect these instance limits?

### 3. Function Timeout Behavior
Functions appear to be terminated after approximately 30 seconds regardless of the configured timeout, causing test failures when run consecutively.

## Structure
- `functions/python/` - Cloud Functions code
- `functions/python/app/tests/` - Test suite
- `docker-compose.yaml` - Service configuration
- `Makefile` - Build and test commands