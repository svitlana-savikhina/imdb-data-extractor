import pandas as pd

# Loading data from a file
input_file = "movies_and_actors_with_rating.csv"
output_file = "actor_analysis.csv"

df = pd.read_csv(input_file)

# Splitting actors and creating a separate entry for each actor
df = df.assign(Actors=df["Actors"].str.split(", ")).explode("Actors")

# Counting the number of movies and calculating the average rating for each actor
actor_stats = (
    df.groupby("Actors")
    .agg(film_count=("Movie Title", "count"), average_rating=("Rating", "mean"))
    .reset_index()
)

# Rounding the average rating to one decimal place
actor_stats["average_rating"] = actor_stats["average_rating"].round(1)

# Filtering actors who appear in more than one movie
actor_stats = actor_stats[actor_stats["film_count"] > 1]

# Writing results to a new CSV file
actor_stats.to_csv(output_file, index=False)

print(f"Data successfully saved to {output_file}")
