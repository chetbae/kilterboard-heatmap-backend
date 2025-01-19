# Kilterboard Hold Usage Analysis 🧗

A web application for visualizing hold usage patterns on the Kilterboard.

## Setup

1. Clone the repository

```bash
git clone <your-repository-url>
cd <repository-name>
```

2. Create and activate virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Unix/MacOS
# or
venv\Scripts\activate     # Windows
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment variables

- Copy `.env.example` to `.env`
- Update variables as needed

5. Run the application

```bash
uvicorn src.main:app --reload
```
