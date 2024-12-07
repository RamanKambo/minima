# Minima

**Minima** is an open source fully local RAG, with ability to integrate with ChatGPT and MCP. 
Minima can also be used as a RAG on-premises.

Minima supports 3 modes right now. You can use fully local (minimal) installation, you can use Custom GPT to query your local documents via ChatGPT and use an Anthropic Claude for querying local files.

**For MCP usage, please be sure that your local machine's Python is >=3.10 and 'uv' installed.**

## Quick Start

1. Create a `.env` file in the project's root directory (where you'll find env.sample). Place `.env` in the same folder and copy all environment variables from env.sample to `.env`.

2. Ensure your `.env` file includes the following variables:
- `LOCAL_FILES_PATH` - Path to your documents directory
- `EMBEDDING_MODEL_ID` - Model to use for embeddings
- `EMBEDDING_SIZE` - Size of embeddings
- `SCAN_INTERVAL_MINUTES` - How often to scan for file changes (default: 5 minutes)
- `USER_ID` - Required for ChatGPT integration, use your email
- `PASSWORD` - Required for ChatGPT integration, use any password

3. Choose your installation method:
   - For fully local installation: `docker compose -f docker-compose-ollama.yml --env-file .env up --build`
   - For ChatGPT enabled installation: `docker compose -f docker-compose-chatgpt.yml --env-file .env up --build`
   - For MCP integration (Anthropic Desktop app): `docker compose -f docker-compose-mcp.yml --env-file .env up --build`

## Indexing System

Minima implements a robust file indexing system that automatically manages the indexing process of your documents. Here's how it works:

### Automatic File Tracking

The system maintains a status file that tracks:
- File metadata (name, extension, path)
- Indexing status (Pending, Running, Complete, Failed, DeletedFromStore)
- Last modified and indexed timestamps
- Error information if indexing fails

### How Indexing Works

1. **Initial Setup**
   - On first run, the system scans your `LOCAL_FILES_PATH` directory
   - Creates a status tracking file if none exists
   - Automatically begins indexing new files

2. **Periodic Scanning**
   - Configurable scan interval through `SCAN_INTERVAL_MINUTES` in .env file
   - Default scan interval is 5 minutes if not specified
   - Each scan checks for:
     - New files to be indexed
     - Modified files that need re-indexing
     - Files that have been deleted
   - Queue management ensures efficient processing
   - Scan times are logged for tracking and debugging

3. **Status Management**
   - Files are marked as:
     - "Pending" when first discovered or when modified
     - "Running" while being indexed
     - "Complete" after successful indexing
     - "Failed" if errors occur during indexing
     - "DeletedFromStore" if the file is removed

4. **Smart Indexing**
   - Only indexes new or modified files
   - Automatically resumes failed indexing attempts
   - Handles concurrent access safely
   - Maintains indexing history through the status file

## Configuration Variables

**LOCAL_FILES_PATH**: Specify the root folder for indexing. Indexing is recursive, including all documents within subfolders.

**EMBEDDING_MODEL_ID**: Specify the embedding model to use. Currently supports Sentence Transformer models (e.g., sentence-transformers/all-mpnet-base-v2).

**EMBEDDING_SIZE**: Define the embedding dimension provided by the model for Qdrant vector storage configuration.

**SCAN_INTERVAL_MINUTES**: How often the system should scan for file changes (in minutes). Default is 5 minutes if not specified. Examples:
```env
SCAN_INTERVAL_MINUTES=5  # Scan every 5 minutes (default)
SCAN_INTERVAL_MINUTES=15 # Scan every 15 minutes
SCAN_INTERVAL_MINUTES=60 # Scan every hour
```

**USER_ID**: Your email (required for ChatGPT integration).

**PASSWORD**: Authentication password for firebase account.

## Example Configurations

### Local or MCP Usage
```env
LOCAL_FILES_PATH=/Users/davidmayboroda/Downloads/PDFs/
EMBEDDING_MODEL_ID=sentence-transformers/all-mpnet-base-v2
EMBEDDING_SIZE=768
SCAN_INTERVAL_MINUTES=5  # Scan every 5 minutes
```

### ChatGPT Custom GPT Usage
```env
LOCAL_FILES_PATH=/Users/davidmayboroda/Downloads/PDFs/
EMBEDDING_MODEL_ID=sentence-transformers/all-mpnet-base-v2
EMBEDDING_SIZE=768
SCAN_INTERVAL_MINUTES=15  # Scan every 15 minutes
USER_ID=user@gmail.com
PASSWORD=yourpassword
```

## Models

- Chat Model: **qwen2:0.5b** (default for local installation)
- Rerank Model: **BAAI/bge-reranker-base** (used for both local and custom GPT configurations)

## User Interface

Access the chat UI at **http://localhost:3000**

## MCP Integration

To use with Anthropic Claude, add the following to `/Library/Application\ Support/Claude/claude_desktop_config.json`:

```json
{
    "mcpServers": {
      "minima": {
        "command": "uv",
        "args": [
          "--directory",
          "/path_to_cloned_minima_project/mcp-server",
          "run",
          "minima"
        ]
      }
    }
  }
```

## ChatGPT Integration

For ChatGPT enabled installation:
1. Start the service using the ChatGPT docker-compose file
2. Copy the OTP from the terminal
3. Use [Minima GPT](https://chatgpt.com/g/g-r1MNTSb0Q-minima-local-computer-search)

## Simplified Usage

You can also run Minima using the provided `run.sh` script.

## License

Minima (https://github.com/dmayboroda/minima) is licensed under the Mozilla Public License v2.0 (MPLv2).