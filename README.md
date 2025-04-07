# Code Search with LanceDB and Ollama

A semantic code search system that uses LanceDB for vector storage and Ollama for embeddings. This system provides a FastAPI server that can be integrated with the Continue extension for VS Code to enable semantic code search within your codebase.

## Features

- Semantic code search using embeddings
- Vector storage with LanceDB
- FastAPI server for easy integration
- Continue extension support
- Automatic code chunking and indexing
- Similarity-based search results

## Prerequisites

- Python 3.12 or later
- Rust (for LanceDB)
- Ollama with nomic-embed-text model

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <repo-name>
```

2. Create and activate a virtual environment:
```bash
python3.12 -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Ollama and the required model:
```bash
# Install Ollama (if not already installed)
curl https://ollama.ai/install.sh | sh

# Pull the embedding model
ollama pull nomic-embed-text
```

## Usage

1. Index your codebase:
```bash
python index.py
```

2. Start the server:
```bash
python server.py
```

3. Configure Continue extension:
Create a `.continue/config.yaml` file with:
```yaml
context:
  - provider: http
    params:
      url: http://0.0.0.0:8000/retrieve
```

## API Endpoints

### POST /retrieve
Accepts semantic search queries and returns relevant code chunks.

Request:
```json
{
  "query": "search query",
  "fullInput": "full input text"
}
```

Response:
```json
[
  {
    "name": "filename.py",
    "description": "Similarity: 0.95",
    "content": "code content"
  }
]
```

## Project Structure

- `server.py` - FastAPI server implementation
- `index.py` - Code indexing and database setup
- `requirements.txt` - Python dependencies
- `.continue/config.yaml` - Continue extension configuration

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 