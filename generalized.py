from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient,errors
import time
from bson import json_util

app = Flask(__name__)
app.secret_key = 'secretivekey'
"""client = MongoClient("mongodb://localhost:27017/")
db = client["school"]  # Replace with your database name
collection = db["student"]  # Replace with your collection name
"""

# Attempt to connect to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017/")
    # Test the connection
    client.admin.command('ping')  # This sends a ping to the server
    print("Connected to MongoDB successfully.")
except errors.ConnectionFailure as e:
    print(f"Could not connect to MongoDB: {e}")
    exit(1)  # Exit the application if the connection fails

db = client["practical2"]  # Replace with your database name
collection = db["order"]  # Replace with your collection name
print("connection with database is also done")

@app.route('/')
def index():
    return render_template('dashboardtwo.html')


# Function to optimize the query
def optimize_query(operation, query, pipeline=None):
    optimization_suggestions = []

    if operation == 'find':
        # Check if query uses an index (MongoDB's explain feature can help check this in production)
        optimization_suggestions.append("Ensure indexes exist on the fields being queried for faster retrieval.")

        # Projection optimization
        if not query.get('projection'):
            optimization_suggestions.append("Use projections to limit the amount of data returned by the query.")

        # Query limits
        optimization_suggestions.append("Use limit() to minimize the number of documents returned.")

    elif operation == 'insert':
        optimization_suggestions.append("Batch inserts if inserting multiple documents for efficiency.")

    elif operation == 'update':
        optimization_suggestions.append("Ensure the update query is covered by indexes for better performance.")

        # Only update required fields
        optimization_suggestions.append("Update only the necessary fields using $set.")

    elif operation == 'aggregate':
        # Sorting and matching stages should come early in aggregation pipelines
        optimization_suggestions.append(
            "Place $match and $sort stages early in the pipeline to reduce documents early.")

        # Ensure indexes on fields used in $lookup or $group
        optimization_suggestions.append(
            "Ensure indexes exist on fields used in $group for faster aggregation.")

    else:
        optimization_suggestions.append("Unsupported operation or optimization not applicable.")

    return optimization_suggestions


@app.route('/run_query2', methods=['GET', 'POST'])
def run_query2():
    start_time = time.time()

    operation = request.json.get('operation', '').lower()
    queryy = request.json.get('query', {})
    data = request.json.get('data', {})
    pipeline = request.json.get('pipeline', [])
    updateType = request.json.get('updateType', '')

    try:
        if operation == 'find':
            results_ = list(collection.find(queryy))
            results_ = json_util.dumps(results_)

        elif operation == 'insert':
            result = collection.insert_one(data)
            results_ = {
                "message": "Data inserted successfully.",
                "inserted_id": str(result.inserted_id)
            }


        elif operation == 'update':
            if updateType == 'updateOne':
                result = collection.update_one(queryy, {'$set': data})

                results_ = {
                    "message": "Data updated successfully.",
                    "matched_count": result.matched_count,
                    "modified_count": result.modified_count
                }
            elif updateType == 'updateMany':
                result = collection.update_many(queryy, {'$set': data})
                results_ = {
                    "message": "Data updated successfully.",
                    "matched_count": result.matched_count,
                    "modified_count": result.modified_count
                }

        elif operation == 'aggregate':
            results_ = list(collection.aggregate(pipeline))
            results_ = json_util.dumps(results_)

        else:

            return jsonify({"error": "Unsupported operation", "execution_time": time.time() - start_time}), 400

        optimization_suggestions = optimize_query(operation, queryy, pipeline)

    except Exception as e:
        return jsonify({"error": str(e), "execution_time": time.time() - start_time}), 400

    execution_time = time.time() - start_time
    return jsonify({
        "results": results_,
        "execution_time": execution_time,
        "optimizations": optimization_suggestions})




if __name__ == '__main__':
    app.run(debug=True)

