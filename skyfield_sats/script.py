from skyfield.api import load
from skyfield.api import wgs84
import logging 
import time
import numpy as np
from hilbertcurve.hilbertcurve import HilbertCurve
import psycopg2
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the desired log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Log to stdout
    ]
)

# Create a logger instance
logger = logging.getLogger(__name__)

# Load TLE data
def get_starlink_satellites(url="https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"):
    logger.info("Loading TLE data...")
    satellites = load.tle_file(url)
    satellites = [{"sat":s} for s in satellites]
    logger.info(f"Loaded {len(satellites)} Starlink satellites.")
    return satellites

# Connect to the PostgreSQL database
def connect_to_db():
    conn = psycopg2.connect(
        dbname="minecraftindex",
        user="kyjohnso",
        password="Password",
        host='postgis',  # Use the service name from docker-compose.yml
        port=5432
    )
    return conn

# Compute ECEF XYZ positions
def compute_ecef_positions(satellites):
    ts = load.timescale()
    now = ts.now()

    for sat in satellites:
        try:
            geocentric = sat["sat"].at(now)
            subpoint = wgs84.subpoint(geocentric)

            # Get ECEF XYZ coordinates
            sat.update({
                "scc": sat["sat"].model.satnum,
                "name": sat["sat"].name,
                "ecef": geocentric.position.m,
                "timestamp": now.utc_datetime()
            })
        except Exception as e:
            logger.info(f"Error computing position for {sat.name}: {e}")

    return satellites

# Insert satellite data into the database
def ecef_points_to_hilbert(ecef,hilbert_dict):
    
    p=hilbert_dict.get("p",np.ceil(np.log2(hilbert_dict["world_size"]/hilbert_dict["cell_size"])))
    hilbert_dict["p"] = p
    ecef_scale = (
        ecef + hilbert_dict["world_size"]/2
    )/hilbert_dict["cell_size"]
    ecef_scale_int = ecef_scale.astype(np.int64)

    hilbert_curve = HilbertCurve(
        n=hilbert_dict.get("n",3),
        p=p
    )

    return hilbert_curve.distances_from_points(ecef_scale_int)

def hilbert_to_ecef_points(hilbert,hilbert_dict):
    p=hilbert_dict.get("p",np.ceil(np.log2(hilbert_dict["world_size"]/hilbert_dict["cell_size"])))
    
    hilbert_curve = HilbertCurve(
        n=hilbert_dict.get("n",3),
        p=p
    )
    
    ecef_scale = hilbert_curve.points_from_distances(hilbert)

    return np.array(ecef_scale) * hilbert_dict["cell_size"] - hilbert_dict["world_size"]/2

def add_hilbert_to_satellites(satellites,hilbert):
    for i in range(len(satellites)):
        satellites[i]["hilbert_index"]=hilbert[i]
    return satellites

def create_satellites_table(conn):
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS satellites (
            id SERIAL PRIMARY KEY,                   -- Auto-incrementing primary key
            satnum INT NOT NULL,                     -- Satellite number (cannot be NULL)
            ecef GEOMETRY(POINTZ, 4978) NOT NULL,    -- 3D ECEF coordinates (cannot be NULL)
            observation_time TIMESTAMP NOT NULL,     -- Observation timestamp (cannot be NULL)
            name TEXT NOT NULL,                      -- Satellite name (cannot be NULL)
            hilbert_index BIGINT NOT NULL,           -- Hilbert curve index (cannot be NULL),
            CONSTRAINT satnum_time_hilbert_unique UNIQUE (satnum, observation_time, hilbert_index) -- Optional uniqueness constraint
        );
    """)
    conn.commit()
    cursor.execute("""
            CREATE INDEX IF NOT EXISTS satnum_time_idx_compound
            ON satellites (satnum, observation_time, hilbert_index);
    """)
    conn.commit()
    cursor.execute("""
            CREATE INDEX IF NOT EXISTS time_idx_compound
            ON satellites (observation_time, hilbert_index);
    """)
    conn.commit()
    cursor.execute("""
            CREATE INDEX IF NOT EXISTS satnum_idx_compound
            ON satellites (satnum, hilbert_index);
    """)
    conn.commit()
    cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx
            ON satellites (hilbert_index);
    """)
    conn.commit()

def drop_satellites_table(connection):
    """
    Drops the satellites table if it exists in a PostgreSQL database.

    Args:
        connection (psycopg2.extensions.connection): Active database connection.

    Returns:
        None
    """
    drop_table_query = "DROP TABLE IF EXISTS satellites CASCADE;"
    
    try:
        with connection.cursor() as cursor:
            # Execute the drop table query
            cursor.execute(drop_table_query)
            # Commit the transaction
            connection.commit()
            logger.info("Satellites table dropped successfully.")
    except Exception as e:
        connection.rollback()
        logger.info(f"Error dropping satellites table: {e}")

def create_hilbert_points_table(connection):
    """
    Creates the hilbert_points table with hilbert_index as the primary key
    and a corresponding 3D point entry.

    Args:
        connection (psycopg2.extensions.connection): Active database connection.

    Returns:
        None
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS hilbert_points (
        hilbert_index BIGINT PRIMARY KEY,       -- Hilbert index as the primary key
        point GEOMETRY(POINTZ, 4978) NOT NULL  -- 3D point (ECEF coordinates) with SRID 4978
    );
    """
    try:
        with connection.cursor() as cursor:
            # Execute the create table query
            cursor.execute(create_table_query)
            # Commit the transaction
            connection.commit()
            logger.info("Hilbert points table created successfully.")
    except Exception as e:
        connection.rollback()
        logger.info(f"Error creating hilbert points table: {e}")

def drop_hilbert_points_table(connection):
    """
    Drops the hilbert_points table if it exists in the database.

    Args:
        connection (psycopg2.extensions.connection): Active database connection.

    Returns:
        None
    """
    drop_table_query = "DROP TABLE IF EXISTS hilbert_points CASCADE;"
    
    try:
        with connection.cursor() as cursor:
            # Execute the drop table query
            cursor.execute(drop_table_query)
            # Commit the transaction
            connection.commit()
            logger.info("Hilbert points table dropped successfully.")
    except Exception as e:
        connection.rollback()
        logger.info(f"Error dropping hilbert points table: {e}")

def insert_hilbert_points(hilbert_points, connection):
    """
    Inserts a list of hilbert points into the hilbert_points table.

    Args:
        connection (psycopg2.extensions.connection): Active database connection.
        hilbert_points (list of dict): List of dictionaries containing:
            - hilbert (int): Hilbert index.
            - ecef (tuple): Tuple of ECEF coordinates (x, y, z) in meters.

    Returns:
        None
    """
    insert_query = """
    INSERT INTO hilbert_points (hilbert_index, point)
    VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s, %s), 4978))
    ON CONFLICT (hilbert_index) DO NOTHING;
    """
    try:
        with connection.cursor() as cursor:
            # Prepare data for batch insertion
            data = [
                (
                    point["hilbert"], 
                    str(point["ecef"][0]), 
                    str(point["ecef"][1]), 
                    str(point["ecef"][2]),
                )
                for point in hilbert_points
            ]
            # Execute batch insertion
            cursor.executemany(insert_query, data)
            # Commit the transaction
            connection.commit()
            logger.info(f"{len(hilbert_points)} hilbert points inserted successfully.")
    except Exception as e:
        connection.rollback()
        logger.info(f"Error inserting hilbert points: {e}")


def insert_satellites(satellites, connection):

    with connection.cursor() as cursor:
        # Insert the data
        for sat in satellites:
            insert_query = """
                INSERT INTO satellites (satnum, ecef, observation_time, name, hilbert_index)
                VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s, %s), 4978), %s, %s, %s);
                """
            cursor.execute(
                insert_query, 
                (
                    sat["scc"], 
                    str(sat["ecef"][0]), 
                    str(sat["ecef"][1]), 
                    str(sat["ecef"][2]), 
                    sat["timestamp"], 
                    sat["name"], 
                    sat["hilbert_index"],
                )
            )
        connection.commit()
    cursor.close()
    logger.info("Satellite data inserted into the database.")

def main():
    # Load satellite data
    sats = get_starlink_satellites()

    # Compute ECEF positions
    sats = compute_ecef_positions(sats)

    # compute hilbert index
    world_size = 80_000_000
    cell_size= 10_000
    
    hilbert_dict = {
        "world_size":world_size,
        "cell_size":cell_size,
        "n":3,
    }
    hilbert = ecef_points_to_hilbert(np.array([s["ecef"] for s in sats]),hilbert_dict)
    sats = add_hilbert_to_satellites(sats,hilbert)

    hilbert_ecef = hilbert_to_ecef_points(hilbert,hilbert_dict)
    hilbert_points = [{"hilbert":hilbert[i],"ecef":hilbert_ecef[i]} for i in range(len(hilbert))]
    
    # Connect to the database
    conn = connect_to_db()

    # Insert hilbert index into the database
    insert_hilbert_points(hilbert_points,conn)
    
    # Insert data into the database
    insert_satellites(sats, conn)

    # Close the connection
    conn.close()


if __name__ == "__main__":
    while True:
        main()
        time.sleep(10)