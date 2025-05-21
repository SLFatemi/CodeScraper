import math
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import pymysql
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

app = FastAPI()


class InputLink(BaseModel):
    link: str


class Listing(BaseModel):
    name: str
    percentage: int
    url: str


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sina.mhreza.ir"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FROM https://github.com/Amir-Sajedi/CodeScraper

def find_similar(id):
    try:

        db = pymysql.connect(
            host='sahand.liara.cloud',
            port=30896,
            user='root',
            password='3gsc2mpq4mY217f04ccMxncb',
            database='upbeat_hodgkin',
            charset='utf8mb4'
        )

        print("Successfully connected to the database!")

        # Create a cursor object to execute SQL queries
        cursor = db.cursor()

        # Execute SQL query to fetch data
        query = "SELECT id, name, price, area, room_count, year, url FROM listings"
        cursor.execute(query)

        # Fetch all records
        results = cursor.fetchall()

        # Get column names
        column_names = [desc[0] for desc in cursor.description]

        # Convert to pandas DataFrame
        df = pd.DataFrame(results, columns=column_names)

        # Close the database connection
        cursor.close()
        db.close()

        # Clean and convert price values
        df['price'] = df['price'].apply(clean_price)

        # Print column information for debugging
        print(f"DataFrame shape before cleaning: {df.shape}")
        print(f"Missing values in each column:")
        print(df.isna().sum())

        # Fill missing values with column means for numerical features
        for feature in ['price', 'area', 'room_count', 'year']:
            if df[feature].isna().sum() > 0:
                feature_mean = df[feature].mean()
                df[feature] = df[feature].fillna(feature_mean)
                print(f"Filled {feature} missing values with mean: {feature_mean}")

        print(f"DataFrame shape after cleaning: {df.shape}")

        # Specify features for similarity calculation
        features = ['price', 'area', 'room_count', 'year']
        X = df[features].values

        # Double check for any remaining NaNs
        if np.isnan(X).any():
            print("Warning: There are still NaN values in the data. Applying additional cleaning...")
            # Replace any remaining NaNs with column means
            for col_idx in range(X.shape[1]):
                mask = np.isnan(X[:, col_idx])
                X[mask, col_idx] = np.mean(X[~mask, col_idx])

        print("Feature data shape:", X.shape)
        print("NaN values remaining:", np.isnan(X).sum())

        # Normalize the features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Build KNN model
        model = NearestNeighbors(n_neighbors=11, metric='euclidean')  # Increased to 11 to account for self-match
        model.fit(X_scaled)

        # Get target house ID from user
        target_id = id

        if target_id in df['id'].values:
            target_index = df.index[df['id'] == target_id][0]
            target_vector_scaled = X_scaled[target_index].reshape(1, -1)

            # Find K nearest neighbors
            distances, indices = model.kneighbors(target_vector_scaled)

            # Remove the target house itself from results
            similar_indices = [idx for i, idx in enumerate(indices[0]) if idx != target_index][:10]
            similar_distances = [dist for i, dist in enumerate(distances[0]) if indices[0][i] != target_index][:10]

            # Get all pairwise distances for a more accurate scale calibration
            # This gives us a better idea of the true distance distribution in the dataset
            print("Calculating distance statistics for better similarity calibration...")

            # Calculate distances for 1000 random sample pairs (or fewer for smaller datasets)
            sample_size = min(1000, len(df))
            sample_indices = np.random.choice(len(df), size=sample_size, replace=False)
            sample_data = X_scaled[sample_indices]

            from scipy.spatial.distance import pdist

            sample_distances = pdist(sample_data)

            # Use these statistics to create a better-calibrated similarity scale
            min_dist = np.min(similar_distances)
            max_dist = np.max(sample_distances)

            # Define similarity bounds with specified range (25 to 99)
            min_similarity = 25
            max_similarity = 99

            # Add an exponential transformation factor to create more spread in the middle range
            # Higher value of alpha creates stronger exponential effect
            alpha = 50.0  # Tune this value: higher = more aggressive spread

            # Calculate similarity percentages
            similarity_percentages = []
            for dist in similar_distances:
                # Normalize distance between 0 and 1
                normalized_dist = (dist - min_dist) / (max_dist - min_dist)

                # Apply exponential transformation to create more spread
                transformed_dist = normalized_dist ** (1 / alpha)

                # Map to desired similarity range (inverted - smaller distance = higher similarity)
                similarity = max_similarity - (max_similarity - min_similarity) * transformed_dist

                # Ensure we stay within bounds
                similarity = max(min_similarity, min(max_similarity, similarity))

                similarity_percentages.append(similarity)

            # Create results with [name, percentage, url]
            similar_listings = []

            for i, idx in enumerate(similar_indices):
                name = df.loc[idx, 'name']
                similarity = similarity_percentages[i]
                url = df.loc[idx, 'url']

                # If URL is missing or empty, use the example URL format
                if pd.isna(url) or url == "":
                    url = f"https://example.com/house/{int(df.loc[idx, 'id'])}"

                similar_listings.append([f'{name}',f"{math.trunc(similarity)}",f"{url}"])

            # Print target house info
            print(f"\nTarget house ID = {target_id}, Name = {df.loc[target_index, 'name']}")

            # Print debug information
            print(f"\nDistance statistics:")
            print(f"Min distance in similar items: {min_dist:.4f}")
            print(f"Max distance in sample: {max_dist:.4f}")
            print(f"Similarity range: {min_similarity}% to {max_similarity}%")
            # Return as a properly formatted list for potential API usage
            return similar_listings

        else:
            print(f"There is no house with ID {target_id} in the database.")
            return []

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return []

def clean_price(price_str):
    if pd.isna(price_str) or price_str == "":
        return np.nan

    # If price contains a comma and a space (mortgage format like "90000000 ,8000000")
    if isinstance(price_str, str) and "," in price_str and " " in price_str:
        # Take only the first part (sale price)
        price_str = price_str.split(" ")[0]

    # Remove commas
    if isinstance(price_str, str):
        price_str = price_str.replace(",", "")

    try:
        return float(price_str)
    except (ValueError, TypeError):
        return np.nan

# ////////////////

def get_similar(url):
    db = pymysql.connect(
        host='sahand.liara.cloud',
        port=30896,
        user='root',
        password='3gsc2mpq4mY217f04ccMxncb',
        database='upbeat_hodgkin',
        charset='utf8mb4'
    )
    cursor = db.cursor()
    try:
        # /////////////////// TEMP
        query = "SELECT * FROM listings WHERE url = %s;"
        cursor.execute(query, (url.link,))
        row = cursor.fetchone()
        cursor.close()
        raw_return = find_similar(row[0])
        reponse = []
        for house in raw_return:
            reponse.append(Listing(name = house[0],percentage =house[1],url = house[2]))
        return reponse
    except:
        raise HTTPException(status_code=404)


@app.post('/link', response_model=list[Listing])
async def get_link(input_link: InputLink):
    time.sleep(2)
    return get_similar(input_link)
