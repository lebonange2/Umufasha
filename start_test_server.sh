#!/bin/bash
export USE_MOCK_LLM=true
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
