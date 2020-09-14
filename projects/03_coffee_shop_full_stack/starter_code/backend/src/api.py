import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
import sys
from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)

# Set up CORS. Allow '*' for origins.
cors = CORS(app)

'''
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''

db_drop_and_create_all()

# ROUTES
'''
GET /drinks
    A public endpoint
    Contains only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
'''


@app.route("/drinks")
def get_drinks():
    try:

        drink_selection = Drink.query.all()
        drinks = [drink.short() for drink in drink_selection]
        print(len(drinks))
        return (jsonify({"success": True, "drinks": drinks}), 200)
    except:
        abort(422)


'''
GET /drinks-detail
    requires the 'get:drinks-detail' permission
    contains the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
'''


@app.route("/drinks-detail")
@requires_auth("get:drinks-detail")
def get_drinks_detail(jwt):

    try:
        drink_selection = Drink.query.all()
        drinks = [drink.long() for drink in drink_selection]

        return (jsonify({"success": True,
                         "drinks": drinks}), 200)
    except:
        abort(422)


'''
POST /drinks
    creates a new row in the drinks table
    requires the 'post:drinks' permission
    contains the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
'''


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def post_drink(jwt):
    try:
        if "title" not in request.json:
            abort(400)

        title = request.json["title"]

        existing_count = Drink.query.filter(Drink.title == title).count()

        if existing_count > 0:
            abort(409)

        recipe = request.json["recipe"]

        new_drink = Drink(title=title, recipe=json.dumps(recipe))

        new_drink.insert()

        return (jsonify({"success": True,
                         "drinks": [new_drink.long()]}), 200)

    except:
        print(sys.exc_info())
        abort(422)


'''
PATCH /drinks/<id>
    where <id> is the existing model id
    responds with a 404 error if <id> is not found
    updates the corresponding row for <id>
    requires the 'patch:drinks' permission
    contains the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
'''


@app.route("/drinks/<id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drink(jwt, id=id):

    drink = Drink.query.filter(Drink.id == id).first()

    if not drink:
        abort(404)

    if "title" in request.json:
        title = request.json["title"]

        existing_count = Drink.query.filter(
            Drink.title == title, Drink.id != id).count()
        if existing_count > 0:
            print("Title repeated")
            abort(409)

        drink.title = title

    if "recipe" in request.json:
        recipe = request.json["recipe"]
        drink.recipe = json.dumps(recipe)

    try:

        drink.update()
        return (jsonify({"success": True,
                         "drinks": [drink.long()]}), 200)

    except:
        print(sys.exc_info())
        abort(422)


'''
DELETE /drinks/<id>
    where <id> is the existing model id
    responds with a 404 error if <id> is not found
    deletes the corresponding row for <id>
    requires the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
'''


@app.route("/drinks/<id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(jwt, id=id):

    drink = Drink.query.filter(Drink.id == id).first()

    if not drink:
        abort(404)

    try:
        drink.delete()
        return (jsonify({"success": True,
                         "delete": id}), 200)

    except:
        abort(422)


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "not found"
    }), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400


@app.errorhandler(409)
def conflict(error):
    return (jsonify({"success": False,
                     "error": 409,
                     "message": "A drink with the same title already exists"}),
            409)


@app.errorhandler(AuthError)
def auth_error(error):
    return (jsonify({
                    "success": False,
                    "error": error.status_code,
                    "message": error.error,
                    }), error.status_code)
