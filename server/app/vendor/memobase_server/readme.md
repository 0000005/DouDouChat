# Memobase SDK (Vendored)

> **⚠️ WARNING: Vendored Code**
> This directory acts as the core engine of the DouDouChat memory system. It has been adapted from the standalone Memobase project to run as an embedded SDK.

## Overview

Previously a standalone FastAPI service, this module (`memobase_server`) is now integrated directly into the `DouDouChat` main server process to provide:
- **Dual-Track Memory**: Long-term profile + Event-based episodes.
- **Embedded Execution**: Runs within the same process as the main app, managed by `server/app/main.py` lifespan.
- **Unified config**: Uses the main application's configuration system explicitly.

## Key Integration Changes

To support the SDK model, several core files have been modified from their original versions:

1.  **`env.py`**: 
    - Dependency on local `config.yaml` has been removed.
    - Added `reinitialize_config(dict)` to allow configuration injection from `app.core.config`.
    
2.  **`connectors.py`**: 
    - Removed auto-Connect on import side effects.
    - Added explicit `init_db(url)` function to support lazy loading and connection pooling management by the main app.
    
3.  **`controllers/buffer_background.py`**:
    - Exposed `start_memobase_worker` as an async coroutine for the main app to schedule as a background task.

## Usage

**Do not import controllers directly** from this package in the main application logic if possible. Instead, use the **Bridge Service**:

- **Location**: `server/app/services/memo/bridge.py`
- **Class**: `MemoService`

The `MemoService` handles:
- Promise unwrapping (converting SDK internal `Promise` objects to native Python exceptions/data).
- Project ID management (injecting `Space ID`).
- Type safety and simplified APIs.

## Directory Structure

```text
memobase_server/
├── controllers/       # Business logic (User, Profile, Event, Blob)
├── models/           # SQLAlchemy & Pydantic models
├── llms/             # LLM & Embedding integration (OpenAI compatible)
├── prompts/          # Prompt templates for memory extraction
├── utils/            # Helper functions
└── ...
```

## Configuration

This module **does not** read `config.yaml` or `.env` files directly. 
Configuration is passed during startup via `app.services.memo.initialize_memo_sdk()`, utilizing `server/app/core/config.py`.

Refer to `server/docs/memobase/sdk_integration_plan.md` for the full integration architecture.
