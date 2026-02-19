# Building an MCP Server: Step-by-Step Guide

This guide walks you through building a NASA APOD MCP server from scratch, one step at a time. We use **Cursor** as the primary client for testing and demo, with optional setup instructions for **Claude Code** and **Claude Desktop**.

---

## Table of Contents

- [Step 0: Setup](#step-0-setup)
- [Step 1: Minimal Server](#step-1-minimal-server)
- [Step 2: Add API Request Helper](#step-2-add-api-request-helper)
- [Step 3: First Tool - Today's Photo](#step-3-first-tool---todays-photo)
- [Step 4: Second Tool - Photo by Date](#step-4-second-tool---photo-by-date)
- [Step 5: Third Tool - Random Photo](#step-5-third-tool---random-photo)
- [Step 6: Add a Resource](#step-6-add-a-resource)
- [Step 7: Run and Test](#step-7-run-and-test)
  - [Connect to Cursor (Primary)](#option-a-cursor-ide-primary)
  - [Connect to Claude Code (Optional)](#option-b-claude-code-optional)
  - [Connect to Claude Desktop (Optional)](#option-c-claude-desktop-optional)
- [Step 8: Extensions](#step-8-extensions)

---

## Step 0: Setup

### Install Dependencies

```bash
# Using uv (recommended)
uv init nasa-mcp
cd nasa-mcp
uv add "mcp[cli]" httpx

# OR using pip
mkdir nasa-mcp
cd nasa-mcp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install "mcp[cli]" httpx
```

### Create Your Python File

```bash
touch nasa_server.py
```

---

## Step 1: Minimal Server

**Goal:** Create the absolute minimum MCP server that runs.

**Concepts:** Import FastMCP, initialize server, run it.

```python
"""
NASA APOD MCP Server - Step 1: Minimal Server
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nasa-apod")


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

**Test it:**
```bash
python nasa_server.py
```

You should see the server start and wait for input. Press `Ctrl+C` to stop.

**What's happening:**
- `FastMCP("nasa-apod")` creates a server named "nasa-apod"
- `mcp.run(transport="stdio")` starts the server using stdio transport
- The server waits for input from an MCP client (Cursor, Claude Code, Claude Desktop, etc.)

---

## Step 2: Add API Request Helper

**Goal:** Add a helper function to make NASA API requests.

**Concepts:** Async functions, HTTP requests, error handling.

```python
"""
NASA APOD MCP Server - Step 2: Add API Helper
"""

from mcp.server.fastmcp import FastMCP
import httpx
from typing import Optional

mcp = FastMCP("nasa-apod")

NASA_API_BASE = "https://api.nasa.gov/planetary/apod"
API_KEY = "DEMO_KEY"  # Free tier: 30 requests/hour


async def fetch_apod(date: Optional[str] = None) -> dict | None:
    """
    Fetch Astronomy Picture of the Day from NASA.
    
    Args:
        date: Optional date in YYYY-MM-DD format
        
    Returns:
        Dictionary with photo data, or None if request fails
    """
    params = {"api_key": API_KEY}
    
    if date:
        params["date"] = date
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                NASA_API_BASE,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            print(f"Error fetching APOD: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

**What's new:**
- `async def fetch_apod()` - asynchronous function for non-blocking I/O
- `httpx.AsyncClient()` - modern async HTTP client
- `Optional[str]` - type hint meaning date can be a string or None
- Try/except blocks - graceful error handling
- `response.raise_for_status()` - throws error for HTTP 4xx/5xx codes

**Why async?**
- Doesn't block while waiting for NASA's server
- Multiple tools can run concurrently
- Better performance for I/O operations

---

## Step 3: First Tool - Today's Photo

**Goal:** Add your first tool that an AI agent can call.

**Concepts:** `@mcp.tool()` decorator, docstrings, return formatting.

```python
"""
NASA APOD MCP Server - Step 3: First Tool
"""

from mcp.server.fastmcp import FastMCP
import httpx
from typing import Optional

mcp = FastMCP("nasa-apod")

NASA_API_BASE = "https://api.nasa.gov/planetary/apod"
API_KEY = "DEMO_KEY"


async def fetch_apod(date: Optional[str] = None) -> dict | None:
    """Fetch APOD data from NASA API."""
    params = {"api_key": API_KEY}
    if date:
        params["date"] = date
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(NASA_API_BASE, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None


# ========================================
# YOUR FIRST TOOL!
# ========================================

@mcp.tool()
async def get_todays_space_photo() -> str:
    """
    Get today's Astronomy Picture of the Day from NASA.
    
    Returns a beautiful space photo with detailed explanation from NASA astronomers.
    Perfect for learning about space, getting daily inspiration, or just seeing
    something amazing from the universe!
    """
    data = await fetch_apod()
    
    if not data:
        return "Unable to fetch today's space photo. NASA API might be temporarily unavailable."
    
    result = f"""**{data['title']}**
Date: {data['date']}

**What you're seeing:**
{data['explanation']}

**Media:** {data['media_type'].title()}
Link: {data['url']}
"""
    
    if 'copyright' in data:
        result += f"\nCopyright: {data['copyright']}"
    
    return result


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

**What's new:**
- `@mcp.tool()` - decorator that registers this function as a tool
- **Docstring is crucial!** - the AI agent reads this to understand when to use the tool
- `async def` - tool is async because it calls `fetch_apod()`
- `-> str` - type hint tells the agent this returns a string
- String formatting with f-strings for clean output

**How it works:**
1. The AI agent reads the docstring and decides when to call this tool
2. FastMCP handles all the JSON-RPC communication
3. Your function runs and returns a string
4. The agent shows the result to the user

---

## Step 4: Second Tool - Photo by Date

**Goal:** Add a tool that accepts parameters and validates input.

**Concepts:** Function parameters, input validation, date handling.

```python
"""
NASA APOD MCP Server - Step 4: Photo by Date Tool
"""

from mcp.server.fastmcp import FastMCP
import httpx
from datetime import datetime
from typing import Optional

mcp = FastMCP("nasa-apod")

NASA_API_BASE = "https://api.nasa.gov/planetary/apod"
API_KEY = "DEMO_KEY"


async def fetch_apod(date: Optional[str] = None) -> dict | None:
    """Fetch APOD data from NASA API."""
    params = {"api_key": API_KEY}
    if date:
        params["date"] = date
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(NASA_API_BASE, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None


@mcp.tool()
async def get_todays_space_photo() -> str:
    """Get today's Astronomy Picture of the Day from NASA."""
    data = await fetch_apod()
    if not data:
        return "Unable to fetch today's space photo."
    
    result = f"""**{data['title']}**
Date: {data['date']}

**What you're seeing:**
{data['explanation']}

**Media:** {data['media_type'].title()}
Link: {data['url']}
"""
    if 'copyright' in data:
        result += f"\nCopyright: {data['copyright']}"
    return result


# ========================================
# NEW TOOL: Photo by Date
# ========================================

@mcp.tool()
async def get_space_photo_by_date(date: str) -> str:
    """
    Get the Astronomy Picture of the Day for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format (e.g., "2024-01-15")
              Must be between 1995-06-16 (first APOD) and today.
    
    Perfect for exploring the NASA archives or finding photos from special dates
    like birthdays, anniversaries, or historical events!
    """
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        
        first_apod = datetime(1995, 6, 16)
        today = datetime.now()
        
        if parsed_date < first_apod:
            return f"Date must be after June 16, 1995 (the first APOD). You requested: {date}"
        
        if parsed_date > today:
            return f"Date cannot be in the future. Today is {today.strftime('%Y-%m-%d')}"
        
    except ValueError:
        return f"Invalid date format. Please use YYYY-MM-DD (e.g., '2024-01-15'). You provided: {date}"
    
    data = await fetch_apod(date)
    
    if not data:
        return f"Unable to fetch space photo for {date}. The date might be missing from NASA's archive."
    
    result = f"""**{data['title']}**
Date: {data['date']}

**What you're seeing:**
{data['explanation']}

**Media:** {data['media_type'].title()}
Link: {data['url']}
"""
    if 'copyright' in data:
        result += f"\nCopyright: {data['copyright']}"
    return result


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

**What's new:**
- `date: str` - function parameter that the AI agent will provide
- `datetime.strptime()` - parse and validate date format
- Date range validation - ensure date is between 1995-06-16 and today
- More specific docstring - tells the agent exactly what format to use

**How parameters work:**
1. The agent sees `date: str` in the function signature
2. The agent reads the docstring to understand what format to use
3. FastMCP automatically validates the type
4. Your function receives the validated parameter

---

## Step 5: Third Tool - Random Photo

**Goal:** Add a tool that generates random parameters.

**Concepts:** Random number generation, date arithmetic.

```python
"""
NASA APOD MCP Server - Step 5: Random Photo Tool
"""

from mcp.server.fastmcp import FastMCP
import httpx
from datetime import datetime, timedelta
from typing import Optional
import random

mcp = FastMCP("nasa-apod")

NASA_API_BASE = "https://api.nasa.gov/planetary/apod"
API_KEY = "DEMO_KEY"


async def fetch_apod(date: Optional[str] = None) -> dict | None:
    """Fetch APOD data from NASA API."""
    params = {"api_key": API_KEY}
    if date:
        params["date"] = date
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(NASA_API_BASE, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None


@mcp.tool()
async def get_todays_space_photo() -> str:
    """Get today's Astronomy Picture of the Day from NASA."""
    data = await fetch_apod()
    if not data:
        return "Unable to fetch today's space photo."
    
    result = f"""**{data['title']}**
Date: {data['date']}

**What you're seeing:**
{data['explanation']}

**Media:** {data['media_type'].title()}
Link: {data['url']}
"""
    if 'copyright' in data:
        result += f"\nCopyright: {data['copyright']}"
    return result


@mcp.tool()
async def get_space_photo_by_date(date: str) -> str:
    """
    Get the Astronomy Picture of the Day for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format (e.g., "2024-01-15")
    """
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        first_apod = datetime(1995, 6, 16)
        today = datetime.now()
        
        if parsed_date < first_apod or parsed_date > today:
            return f"Date must be between 1995-06-16 and today"
    except ValueError:
        return f"Invalid date format. Use YYYY-MM-DD"
    
    data = await fetch_apod(date)
    if not data:
        return f"Unable to fetch space photo for {date}"
    
    result = f"""**{data['title']}**
Date: {data['date']}

**What you're seeing:**
{data['explanation']}

**Media:** {data['media_type'].title()}
Link: {data['url']}
"""
    if 'copyright' in data:
        result += f"\nCopyright: {data['copyright']}"
    return result


# ========================================
# NEW TOOL: Random Photo
# ========================================

@mcp.tool()
async def get_random_space_photo() -> str:
    """
    Get a random Astronomy Picture of the Day from NASA's archives.
    
    Selects a random date between June 16, 1995 (first APOD) and today.
    Great for discovering amazing space photos you've never seen before!
    """
    first_apod = datetime(1995, 6, 16)
    today = datetime.now()
    
    days_diff = (today - first_apod).days
    
    random_days = random.randint(0, days_diff)
    random_date = first_apod + timedelta(days=random_days)
    random_date_str = random_date.strftime("%Y-%m-%d")
    
    data = await fetch_apod(random_date_str)
    
    if not data:
        return "Unable to fetch random space photo. Please try again."
    
    result = f"""**Random Space Photo Discovery!**

**{data['title']}**
Date: {data['date']}

**What you're seeing:**
{data['explanation']}

**Media:** {data['media_type'].title()}
Link: {data['url']}
"""
    if 'copyright' in data:
        result += f"\nCopyright: {data['copyright']}"
    return result


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

**What's new:**
- `import random` - Python's random module
- `timedelta(days=random_days)` - add days to a date
- `strftime("%Y-%m-%d")` - format date as string
- No parameters needed - tool generates its own data

**Date arithmetic:**
```python
first_apod = datetime(1995, 6, 16)       # June 16, 1995
today = datetime.now()                    # Today's date
days_diff = (today - first_apod).days    # Number of days between
random_days = random.randint(0, days_diff)  # Pick random day
random_date = first_apod + timedelta(days=random_days)  # Add to start date
```

---

## Step 6: Add a Resource

**Goal:** Add a read-only resource that an AI agent can access.

**Concepts:** `@mcp.resource()` decorator, resource URIs.

```python
"""
NASA APOD MCP Server - Step 6: Add Resource
"""

from mcp.server.fastmcp import FastMCP
import httpx
from datetime import datetime, timedelta
from typing import Optional
import random

mcp = FastMCP("nasa-apod")

NASA_API_BASE = "https://api.nasa.gov/planetary/apod"
API_KEY = "DEMO_KEY"


async def fetch_apod(date: Optional[str] = None) -> dict | None:
    """Fetch APOD data from NASA API."""
    params = {"api_key": API_KEY}
    if date:
        params["date"] = date
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(NASA_API_BASE, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None


@mcp.tool()
async def get_todays_space_photo() -> str:
    """Get today's Astronomy Picture of the Day from NASA."""
    data = await fetch_apod()
    if not data:
        return "Unable to fetch today's space photo."
    
    result = f"""**{data['title']}**
Date: {data['date']}

**What you're seeing:**
{data['explanation']}

**Media:** {data['media_type'].title()}
Link: {data['url']}
"""
    if 'copyright' in data:
        result += f"\nCopyright: {data['copyright']}"
    return result


@mcp.tool()
async def get_space_photo_by_date(date: str) -> str:
    """Get the Astronomy Picture of the Day for a specific date (YYYY-MM-DD)."""
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        first_apod = datetime(1995, 6, 16)
        today = datetime.now()
        
        if parsed_date < first_apod or parsed_date > today:
            return f"Date must be between 1995-06-16 and today"
    except ValueError:
        return f"Invalid date format. Use YYYY-MM-DD"
    
    data = await fetch_apod(date)
    if not data:
        return f"Unable to fetch space photo for {date}"
    
    result = f"""**{data['title']}**
Date: {data['date']}

**What you're seeing:**
{data['explanation']}

**Media:** {data['media_type'].title()}
Link: {data['url']}
"""
    if 'copyright' in data:
        result += f"\nCopyright: {data['copyright']}"
    return result


@mcp.tool()
async def get_random_space_photo() -> str:
    """Get a random Astronomy Picture of the Day from NASA's archives."""
    first_apod = datetime(1995, 6, 16)
    today = datetime.now()
    days_diff = (today - first_apod).days
    
    random_days = random.randint(0, days_diff)
    random_date = first_apod + timedelta(days=random_days)
    random_date_str = random_date.strftime("%Y-%m-%d")
    
    data = await fetch_apod(random_date_str)
    if not data:
        return "Unable to fetch random space photo. Please try again."
    
    result = f"""**Random Space Photo Discovery!**

**{data['title']}**
Date: {data['date']}

**What you're seeing:**
{data['explanation']}

**Media:** {data['media_type'].title()}
Link: {data['url']}
"""
    if 'copyright' in data:
        result += f"\nCopyright: {data['copyright']}"
    return result


# ========================================
# NEW: Resource (read-only data)
# ========================================

@mcp.resource("space://events/famous-dates")
def famous_space_dates() -> str:
    """
    List of famous space exploration dates to explore in APOD archives.
    
    The AI agent can access this resource to suggest interesting dates to users.
    """
    return """
Famous Space Dates to Explore:

First APOD: 1995-06-16
Moon Landing: 1969-07-20
Hubble Launch: 1990-04-24
Mars Rover Landing: 2021-02-18
First Image of Black Hole: 2019-04-10
Cassini Saturn Arrival: 2004-07-01
Rosetta Comet Landing: 2014-11-12
Voyager 1 Jupiter Flyby: 1979-03-05
Earth Day: 1970-04-22
James Webb First Image: 2022-07-12
"""


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

**What's new:**
- `@mcp.resource("space://events/famous-dates")` - creates a resource
- URI format: `scheme://path/to/resource`
- No parameters needed (resources are static)
- Returns a string that the AI agent can read

**Resources vs Tools:**
- **Tools** = the agent can CALL them (active, like function calls)
- **Resources** = the agent can READ them (passive, like reference data)

**When to use resources:**
- Configuration data
- Documentation
- Lists of valid values
- Reference information

---

## Step 7: Run and Test

### Complete Code

Here is your complete server with all components:

```python
"""
NASA APOD MCP Server - Complete
"""

from mcp.server.fastmcp import FastMCP
import httpx
from datetime import datetime, timedelta
from typing import Optional
import random

mcp = FastMCP("nasa-apod")

NASA_API_BASE = "https://api.nasa.gov/planetary/apod"
API_KEY = "DEMO_KEY"


async def fetch_apod(date: Optional[str] = None) -> dict | None:
    """Fetch APOD data from NASA API."""
    params = {"api_key": API_KEY}
    if date:
        params["date"] = date
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(NASA_API_BASE, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None


@mcp.tool()
async def get_todays_space_photo() -> str:
    """Get today's Astronomy Picture of the Day from NASA."""
    data = await fetch_apod()
    if not data:
        return "Unable to fetch today's space photo."
    
    result = f"""**{data['title']}**
Date: {data['date']}

**What you're seeing:**
{data['explanation']}

**Media:** {data['media_type'].title()}
Link: {data['url']}
"""
    if 'copyright' in data:
        result += f"\nCopyright: {data['copyright']}"
    return result


@mcp.tool()
async def get_space_photo_by_date(date: str) -> str:
    """Get the Astronomy Picture of the Day for a specific date (YYYY-MM-DD)."""
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        first_apod = datetime(1995, 6, 16)
        today = datetime.now()
        
        if parsed_date < first_apod or parsed_date > today:
            return f"Date must be between 1995-06-16 and today"
    except ValueError:
        return f"Invalid date format. Use YYYY-MM-DD"
    
    data = await fetch_apod(date)
    if not data:
        return f"Unable to fetch space photo for {date}"
    
    result = f"""**{data['title']}**
Date: {data['date']}

**What you're seeing:**
{data['explanation']}

**Media:** {data['media_type'].title()}
Link: {data['url']}
"""
    if 'copyright' in data:
        result += f"\nCopyright: {data['copyright']}"
    return result


@mcp.tool()
async def get_random_space_photo() -> str:
    """Get a random Astronomy Picture of the Day from NASA's archives."""
    first_apod = datetime(1995, 6, 16)
    today = datetime.now()
    days_diff = (today - first_apod).days
    
    random_days = random.randint(0, days_diff)
    random_date = first_apod + timedelta(days=random_days)
    random_date_str = random_date.strftime("%Y-%m-%d")
    
    data = await fetch_apod(random_date_str)
    if not data:
        return "Unable to fetch random space photo. Please try again."
    
    result = f"""**Random Space Photo Discovery!**

**{data['title']}**
Date: {data['date']}

**What you're seeing:**
{data['explanation']}

**Media:** {data['media_type'].title()}
Link: {data['url']}
"""
    if 'copyright' in data:
        result += f"\nCopyright: {data['copyright']}"
    return result


@mcp.resource("space://events/famous-dates")
def famous_space_dates() -> str:
    """List of famous space exploration dates to explore in APOD archives."""
    return """
Famous Space Dates to Explore:

First APOD: 1995-06-16
Moon Landing: 1969-07-20
Hubble Launch: 1990-04-24
Mars Rover Landing: 2021-02-18
First Image of Black Hole: 2019-04-10
Cassini Saturn Arrival: 2004-07-01
Rosetta Comet Landing: 2014-11-12
Voyager 1 Jupiter Flyby: 1979-03-05
Earth Day: 1970-04-22
James Webb First Image: 2022-07-12
"""


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

### Test Locally

```bash
python nasa_server.py
```

The server starts and waits for MCP client connections over stdio. Now connect it to your preferred client.

---

### Option A: Cursor IDE (Primary)

Cursor has built-in MCP support. This is the recommended way to test your server during development because the agent can call your tools directly from the chat panel.

#### 1. Add the MCP config

Create (or edit) the file `.cursor/mcp.json` in your **project root**:

**macOS / Linux:**
```json
{
  "mcpServers": {
    "nasa-apod": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/nasa-mcp",
        "main.py"
      ]
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "nasa-apod": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:\\Users\\YourName\\source\\repos\\nasa-mcp",
        "main.py"
      ]
    }
  }
}
```

> **Tip:** Replace the path with the actual absolute path to your `nasa-mcp` project directory on your machine.

#### 2. Verify the server is connected

1. Open Cursor and navigate to **Settings > MCP** (or open the Command Palette and search for "MCP").
2. You should see **nasa-apod** listed with a green status indicator showing it is connected.
3. If the status is red or missing, double-check your path and make sure `uv` is on your system PATH.

#### 3. Try it out

Open the Cursor **Agent** chat (Ctrl+I or Cmd+I) and try these prompts:

```
What's today's space photo from NASA?

Show me the NASA photo from July 20, 1969

Give me a random space photo

What famous space dates can I explore?

Show me the photo from my birthday: 1995-08-15
```

The agent will recognize the NASA-related intent, call your MCP tools, and return the results inline in the chat.

#### 4. (Optional) Add a Cursor rule for smarter tool usage

To help the Cursor agent always reach for your MCP tools (instead of searching the web or calling the API manually), create a rule file at `.cursor/rules/nasa-apod-mcp.mdc`:

```markdown
---
description: Use the nasa-apod MCP server tools for any NASA space photo requests
alwaysApply: true
---

# NASA APOD MCP Server Usage

When the user asks about NASA photos, space pictures, astronomy images, or anything
related to the Astronomy Picture of the Day, **always use the nasa-apod MCP tools**
instead of calling the API manually or searching the web.

## Available Tools

| Tool | When to use |
|------|-------------|
| `get_todays_space_photo` | User asks for today's photo, the current APOD, or "what's NASA showing today" |
| `get_space_photo_by_date` | User asks for a photo from a specific date (pass date as `YYYY-MM-DD`) |
| `get_random_space_photo` | User asks for a random photo, wants to explore, or says "surprise me" |
```

---

### Option B: Claude Code (Optional)

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) is Anthropic's CLI-based AI coding agent. If you prefer working in the terminal, you can connect your MCP server to Claude Code.

#### 1. Add the MCP server

Run the following command from your terminal:

**macOS / Linux:**
```bash
claude mcp add nasa-apod -- uv run --directory /absolute/path/to/nasa-mcp main.py
```

**Windows:**
```powershell
claude mcp add nasa-apod -- uv run --directory C:\Users\YourName\source\repos\nasa-mcp main.py
```

This registers the server in your Claude Code configuration. You can also add it manually by editing `~/.claude/mcp_servers.json`:

```json
{
  "nasa-apod": {
    "command": "uv",
    "args": [
      "run",
      "--directory",
      "/absolute/path/to/nasa-mcp",
      "main.py"
    ]
  }
}
```

#### 2. Verify the connection

```bash
claude mcp list
```

You should see `nasa-apod` in the output.

#### 3. Try it out

Start a Claude Code session and ask:

```
What's today's space photo from NASA?
```

Claude Code will discover the MCP tools and call them automatically.

---

### Option C: Claude Desktop (Optional)

[Claude Desktop](https://claude.ai/download) is Anthropic's desktop application that supports MCP servers natively. Use this option if you want a GUI-based chat experience outside of your code editor.

#### 1. Locate the config file

| OS | Config file location |
|----|---------------------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

#### 2. Add the MCP server

Open (or create) the config file and add the `nasa-apod` entry:

**macOS / Linux:**
```json
{
  "mcpServers": {
    "nasa-apod": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/nasa-mcp",
        "main.py"
      ]
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "nasa-apod": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:\\Users\\YourName\\nasa-mcp",
        "main.py"
      ]
    }
  }
}
```

#### 3. Restart Claude Desktop

Close and reopen Claude Desktop. The server will be detected on launch.

#### 4. Try it out

Start a new conversation and ask:

```
What's today's space photo from NASA?
```

You should see Claude call the `get_todays_space_photo` tool and return the result.

---

### Test Prompts (All Clients)

These prompts work the same way regardless of which client you use:

```
What's today's space photo from NASA?

Show me the NASA photo from July 20, 1969

Give me a random space photo

What famous space dates can I explore?

Show me the photo from my birthday: 1995-08-15
```

---

## Step 8: Extensions

### Extension A: Add Date Range Tool

```python
@mcp.tool()
async def get_space_photos_date_range(start_date: str, end_date: str) -> str:
    """
    Get multiple space photos from a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (max 7 days apart)
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        if (end - start).days > 7:
            return "Date range too large. Maximum 7 days."
        
        if (end - start).days < 0:
            return "Start date must be before end date."
    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD"
    
    params = {
        "api_key": API_KEY,
        "start_date": start_date,
        "end_date": end_date
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(NASA_API_BASE, params=params, timeout=30.0)
        data = response.json()
    
    if not isinstance(data, list):
        return "Error fetching date range"
    
    results = [f"**Space Photos from {start_date} to {end_date}**\n"]
    
    for item in data:
        results.append(f"""
**{item['title']}**
Date: {item['date']}
Link: {item['url']}
""")
    
    return "\n---\n".join(results)
```

### Extension B: Add Image Download Tool

```python
import os

@mcp.tool()
async def download_space_photo(date: str, save_directory: str) -> str:
    """
    Download a space photo to your local computer.
    
    Args:
        date: Date in YYYY-MM-DD format
        save_directory: Directory to save to (e.g., "/Users/me/Desktop")
    """
    if not os.path.exists(save_directory):
        return f"Directory does not exist: {save_directory}"
    
    data = await fetch_apod(date)
    if not data or data.get('media_type') != 'image':
        return "Not an image or date not found"
    
    image_url = data['url']
    filename = f"APOD_{date}.jpg"
    save_path = os.path.join(save_directory, filename)
    
    async with httpx.AsyncClient() as client:
        img_response = await client.get(image_url, timeout=60.0)
        
        with open(save_path, 'wb') as f:
            f.write(img_response.content)
        
        return f"Downloaded to: {save_path}"
```

### Extension C: Add Statistics Tool

```python
@mcp.tool()
async def get_apod_statistics() -> str:
    """Get interesting statistics about the APOD archive."""
    first_apod = datetime(1995, 6, 16)
    today = datetime.now()
    days_running = (today - first_apod).days
    estimated_photos = days_running - 100
    years_running = days_running / 365.25
    
    return f"""**APOD Archive Statistics**

**First APOD:** June 16, 1995
**Days Running:** {days_running:,} days ({years_running:.1f} years)
**Estimated Total Photos:** ~{estimated_photos:,}
**Coverage:** Nearly 3 decades of space imagery

Visit apod.nasa.gov to explore the full archive!
"""
```

### Extension D: Switch to HTTP Transport

For remote servers or sharing your MCP server across a network, switch from stdio to HTTP transport:

```python
def main():
    mcp.run(transport="sse", port=8000)
```

Then connect via URL. The config is the same for any client that supports URL-based MCP servers:

**Cursor (`.cursor/mcp.json`):**
```json
{
  "mcpServers": {
    "nasa-apod": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

**Claude Desktop (`claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "nasa-apod": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

**Claude Code (terminal):**
```bash
claude mcp add --transport sse nasa-apod http://localhost:8000/sse
```

---

## Summary: What You Built

**3 Tools:**
- Get today's space photo
- Get photo by specific date
- Get random photo from archives

**1 Resource:**
- List of famous space dates

**Key Concepts Learned:**
- MCP server initialization
- Async HTTP requests
- Tool decorators and docstrings
- Parameter validation
- Error handling
- Resources vs tools
- Type hints
- Date manipulation

**Skills Acquired:**
- Building MCP servers from scratch
- Connecting to external APIs
- Registering tools and resources
- Testing with Cursor, Claude Code, and Claude Desktop
- Extending with new features

---

## Next Steps

1. **Get your own NASA API key** at https://api.nasa.gov (500K requests/day!)
2. **Try other NASA APIs:**
   - Mars Rover Photos
   - Earth Imagery
   - Asteroids Near Earth Objects
3. **Build your own MCP server** with a different API
4. **Add more tools** like search, favorites, collections
5. **Deploy to production** with HTTP transport and share it with your team

**Congratulations!** You now know how to build MCP servers!
