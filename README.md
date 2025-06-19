# a2a_agent

## Environment Setup

This project uses [uv](https://github.com/astral-sh/uv) as the Python package manager.

### 1. Create the virtual environment

```
uv venv .venv
```

### 2. Activate the environment

- On macOS/Linux:
  ```
  source .venv/bin/activate
  ```
- On Windows:
  ```
  .venv\Scripts\activate
  ```

### 3. Install dependencies

```
uv pip install -r requirements.txt  # or use pyproject.toml if specified
```

For a naive base environment, no dependencies are required by default.
