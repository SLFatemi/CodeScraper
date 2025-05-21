# CodeScraper


For development Only

A modular platform for real estate data collection, processing, and analysis. CodeScraper scrapes real estate listings from multiple sources, processes and stores them in a MySQL database, and exposes a REST API (via FastAPI) for querying and analysis. It also includes a modern web front-end for user interaction.

---

## Security Notice

**I'm aware that database connection details are present, This project is temporary and will be shut down (Development only)**  

## Features

- **Multi-source Data Scraping:** Collects real estate listings from MelkRadar.com and Maskan-file.ir.
- **Queue-Based Processing:** Publishes scraped data to RabbitMQ for scalable, decoupled processing.
- **Database Integration:** Stores listing data in a MySQL database with robust error handling.
- **REST API:** FastAPI backend provides endpoints to fetch and analyze listings.
- **Interactive Web Front-End:** User-facing UI for submitting links and viewing similar listings.
- **Containerized Deployment:** Easily run everything using Docker.

---

## Project Structure

```
.
├── Melkradar/
│   └── detector_scrapper/
│       └── new_scrapper.py        # Scrapes MelkRadar.com, publishes to RabbitMQ
├── Maskan-file/
│   └── scrapper/
│       └── scrapper.py            # Scrapes Maskan-file.ir (example process)
├── Server-side/
│   └── main.py                    # FastAPI backend serving listing data
├── Front-end/
│   ├── js/
│   │   └── script.js              # Web app logic for searching and result display
│   └── css/
│       └── styles.css             # Styles for web UI
├── sql_script.py                  # Consumes RabbitMQ, inserts listings into MySQL
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Build & run all Python services
└── README.md                      # You are here!
```

---

## Prerequisites

- **Docker** (recommended)
  or
- Python 3.11+
- MySQL database (with the `listings` table)
- RabbitMQ server (local or accessible)
- Python dependencies from `requirements.txt`

---

## Setup & Usage

### 1. Clone the repository

```bash
git clone https://github.com/SLFatemi/CodeScraper.git
cd CodeScraper
```

### 2. Build and Run with Docker (Recommended)

```bash
docker build -t codescraper .
docker run -p 8000:8000 codescraper
```

*This will:*
- Scrape new data from MelkRadar and Maskan-file (see their scrapper scripts), publishing to RabbitMQ
- Consume data from RabbitMQ and store in MySQL (`sql_script.py`)
- Start FastAPI backend on port 8000

### 3. Manual Run (Advanced / Development)

Start dependencies (RabbitMQ, MySQL), then in three terminals:

- **Data Scraper:**  
  `python Melkradar/detector_scrapper/new_scrapper.py`
- **Maskan-file Scraper (optional):**  
  `python Maskan-file/scrapper/scrapper.py`
- **Consumer:**  
  `python sql_script.py`
- **API Server:**  
  `uvicorn Server-side.main:app --reload`

### 4. Front-end

The web client is in `Front-end/`. Open `index.html` in your browser, or deploy the folder as a static website. It communicates with the FastAPI backend.

---

## Environment Variables & Configuration

Update database and RabbitMQ connection parameters as needed in:
- `sql_script.py` (MySQL and RabbitMQ)
- `Server-side/main.py` (MySQL)

---

## API Usage

After starting the server, access the FastAPI docs at:  
`http://localhost:8000/docs`

#### Example endpoint

- `POST /link`  
  **Body:**  
  ```json
  { "link": "URL of the listing" }
  ```
  **Returns:**  
  Top 10 similar listings (by similarity score).

---

## Database Schema

Create this table in your MySQL database:

```sql
CREATE TABLE listings (
    id VARCHAR(255) PRIMARY KEY,
    url TEXT,
    name TEXT,
    address TEXT,
    price TEXT,
    area INT,
    room_count INT,
    year INT,
    feats JSON,
    images JSON
);
```

---

## Front-end Usage

- Input a listing URL in the search bar.
- View top similar listings (with similarity percentage and details).
- All logic for fetching, sorting, and displaying results is in `Front-end/js/script.js` and styled by `Front-end/css/styles.css`.

---

## Contributing

Contributions are welcome! Please open issues or pull requests for bug fixes, new features, or improvements.

---

## License

MIT License

---

## Acknowledgments

- [MelkRadar.com](https://melkradar.com) and [Maskan-file.ir](https://maskan-file.ir) for data sources
- [FastAPI](https://fastapi.tiangolo.com/)
- [RabbitMQ](https://www.rabbitmq.com/)
- [PyMySQL](https://pymysql.readthedocs.io/)

---

