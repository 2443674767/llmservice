from flask import Flask, request, jsonify
from query_service.query_handler import QueryService

# app = Flask(__name__)
query_service = QueryService(db_uri="sqlite:///D:/zy/code/Testdata/LData.db", model_name="llama3.1:8b")


# @app.route('/query', methods=['POST'])
# def query():
#     question = request.json.get("question")
#     if not question:
#         return jsonify({"error": "No question provided"}), 400
#     response = query_service.process_query(question)
#     return jsonify({"response": response})
#
#
# if __name__ == '__main__':
#     app.run(debug=True)

