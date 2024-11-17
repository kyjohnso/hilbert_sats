
# Hilbert Curve Index for Satellite Locations

This repository explores the use of **Hilbert Curves** to index geospatial satellite locations, including applications for proximity queries and spatial clustering. The project applies these concepts to datasets such as Starlink satellite positions, offering tools for visualization and analysis.

## Overview

Satellites in Earth's orbit generate massive amounts of positional data that require efficient management and querying. **Hilbert Curves** are fractal space-filling curves that enable spatial locality, making them ideal for indexing multidimensional data like geospatial coordinates.

This repository is an experiment to:
- Explore Hilbert Curves as an indexing technique for geospatial data.
- Demonstrate their potential in proximity queries and spatial clustering.
- Explore the use of postgis' computational queries for dot product calculations.

---

## Features

- **Hilbert Curve Mapping**: Converts satellite geospatial data into Hilbert curve indices.
- **Geospatial Querying**: Enables querying by dot product to quickly calculate and query which cells are above the horizon for a local position
- **Dockerized Environment**: Simple docker-compose files for deployment

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/minecraft_index.git
   cd minecraft_index
   ```

2. Install Docker and Docker Compose (if not already installed)

3. Build and run the Docker containers and run the postgis:
   ```bash
   docker-compose build
   docker-compose up -d postgis
   ```
4. Create a virtual environment (optional, but recommended) install jupyer and run notebook:
    ```bash
    python -m venv venv
    source env/bin/activate
    pip install -r requirements.txt
    pip install jupyterlab
    jupyter lab
    ```

5. Run the automatic starlink script to populate the database with starlink data

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

This project was inspired by the challenges of managing satellite positional data efficiently. Special thanks to the developers of tools and libraries like `hilbertcurve` and `numpy` and to my friends and coleagues (you know who you are).

---
