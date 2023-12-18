import json

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("iasa_hl_lab5").getOrCreate()
data_file = "data.txt"
df = spark.sparkContext.textFile(data_file, minPartitions=100).map(lambda x: eval(x))

longest_comments = df.map(
        lambda x: (x['driver_comment'], len(x['driver_comment'])) if x['driver_comment'] is not None else ('', 0) # Reduce by key to find the max length
    ).reduceByKey(
        lambda x, y: x  # Reduce by key to find the max length
    ).sortBy(
        lambda x: x[1], ascending=False  # Sort by length in descending order
    ).take(10) 
    
with open("longest_comments.json", "w") as f:
   json.dump(longest_comments, f, indent=4)
      