
# Hilbert Curve Index for Satellite Locations

![Blender Render](assets/images/index_concept.png)

This repository explores the use of **Hilbert Curves** to index geospatial satellite locations, including applications to visability analysis.

## Overview

Satellites in Earth's orbit generate massive amounts of positional data that require efficient management and querying. **[Hilbert Curves](https://en.wikipedia.org/wiki/Hilbert_curve)** are fractal space-filling curves that enable spatial locality, making them ideal for indexing multidimensional data like geospatial coordinates.

![Hilbert Curve](https://en.wikipedia.org/wiki/Hilbert_curve#/media/File:Hilbert3d-step3.png)

Image source: https://en.wikipedia.org/wiki/Hilbert_curve#/media/File:Hilbert3d-step3.png 

This repository is an experiment to:
- Explore Hilbert Curves as an indexing technique for geospatial data,
- Demonstrate their potential fast geometric based indexing into massive datasets (>1e9 records),
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
   git clone git@github.com:kyjohnso/hilbert_sats.git
   cd hilbert_sats
   ```

2. Install Docker and Docker Compose (if not already installed)

3. Build and run the Docker containers and run the postgis:
   ```bash
   docker-compose build
   docker-compose up -d
   ```
4. Create a virtual environment (optional, but recommended) install jupyer and run notebook:
    ```bash
    python -m venv venv
    source env/bin/activate
    pip install -r requirements.txt
    pip install jupyterlab
    jupyter lab
    ```
    Open the notebook in the browser window, you should be able to interact with the database that should have satellite locations being populated. 

More functions and data visualization to come soon

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

This project was inspired by the challenges of managing satellite positional data efficiently. Special thanks to the developers of tools and libraries like `skyfield` and `hilbertcurve` and to my friends and coleagues (you know who you are).

---
