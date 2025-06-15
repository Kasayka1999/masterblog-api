import json
import os
from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask, jsonify, request
from flask_cors import CORS



app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

posts_url = "data/posts_data.json"

SWAGGER_URL="/api/docs"  # (1) swagger endpoint e.g. HTTP://localhost:5002/api/docs
API_URL="/static/masterblog.json" # (2) ensure you create this dir and file

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Masterblog API' # (3) You can change this if you like
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)


def load_file():
    if not os.path.exists(posts_url):
        # Create the file if it doesn't exist
        with open(posts_url, "w") as f:
            json.dump([], f)

    try:
        with open(posts_url, "r") as post_data:
            return json.load(post_data)
    except json.JSONDecodeError:
        # File exists but is not valid JSON
        return []
    except Exception as e:
        print(f"Error reading from {posts_url}: {e}")
        return []

def save_file(posts):
    try:
        with open(posts_url, "w") as post_data:
            json.dump(posts, post_data, indent=2)
    except Exception as e:
        print(f"Error writing to {posts_url}: {e}")

def validate_post_data(new_data):
    if "title" not in new_data or "content" not in new_data:
        return False
    return True

def delete_post(post_id):
    posts = load_file()
    for index, post in enumerate(posts):
        if post["id"] == post_id:
            posts.pop(index)
            save_file(posts)
            break

def validate_post_id(post_id):
    posts = load_file()
    post_ids = {post["id"] for post in posts}
    if post_id not in post_ids:
        return False
    return True

def update_post(post_id, new_data):
    posts = load_file()
    if "title" in new_data:
        for post in posts:
            if post["id"] == post_id:
                post["title"] = new_data["title"]
    if "content" in new_data:
        for post in posts:
            if post["id"] == post_id:
                post["content"] = new_data["content"]
    save_file(posts)


@app.route('/api/posts', methods=['GET'])
def get_posts():
    posts = load_file()
    sort = request.args.get('sort')
    direction = request.args.get('direction', 'asc')

    allowed_fields = ["content", "title"]

    sorted_posts = posts

    if sort:
        if sort not in allowed_fields:
            return jsonify({'error': f"Sorting by '{sort}' is not allowed. Use 'title' or 'content'."}), 400

        reverse = direction == 'desc'

        sorted_posts.sort(key=lambda post: post.get(sort, '').lower(), reverse=reverse)

        return jsonify(sorted_posts)

    if not sort:
        return jsonify(posts)

@app.route('/api/posts', methods=['POST'])
def add():
    posts = load_file()
    if request.method == "POST":
        new_post = request.get_json()

        title = new_post.get('title')
        content = new_post.get('content')

        if not validate_post_data(new_post):
            return jsonify({"error": "missing or wrong data"}), 401

        post_ids = {post["id"] for post in posts}
        unique_id = 0

        while unique_id in post_ids:
            unique_id += 1

        new_data = {
            "id": unique_id,
            "title": title,
            "content": content
        }

        posts.append(new_data)
        save_file(posts)
        return jsonify(new_data), 201

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete(post_id):
    if request.method == "DELETE":
        if not validate_post_id(post_id):
            return jsonify({"error": f"There is no post with id: {post_id}"}), 404
        delete_post(post_id)
        return jsonify({"message": f"Post with id {post_id} has been deleted successfully."}), 200

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update(post_id):
    if request.method == "PUT":
        if not validate_post_id(post_id):
            return jsonify({"error": f"There is no post with id: {post_id}"}), 404
        new_data = request.get_json()
        update_post(post_id, new_data)
        return jsonify({"message": f"Post with id {post_id} has been updated successfully."}), 200


@app.route('/api/posts/search', methods=['GET'])
def search():
    posts = load_file()
    if request.method == "GET":
        title = request.args.get('title')
        content = request.args.get('content')

        filtered = []

        for post in posts:
            post_title = post.get('title', '').lower() # case-sensetive
            post_content = post.get('content', '').lower()

            if title:
                title_search = title.lower() # case-sensetive
                if title_search not in post_title:
                    continue  # skip

            if content:
                content_search = content.lower()
                if content_search not in post_content:
                    continue # skip

            filtered.append(post)

        return jsonify(filtered)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
