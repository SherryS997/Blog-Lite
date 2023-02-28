# Blog-Lite

## Description:
Blog-Lite is a multi-user app where users can post blog-entries (Posts that reflect and discuss opinions) with appropriate
images to spread their ideas in the form of text. The app has features to follow and search other users, and also voice
opinions through comments on their posts. A Rest API has also been developed, following the OpenAPI Specifications,
which can be used to access and modify the database for the app.

## Technologies Used:
* Python: Develop the controllers and serve as the host programming language for the app
* HTML: Develop the required web-pages
* CSS: Style the web-pages
* Bootstrap: To make the frontend appealing and easy to navigate
* SQLite: Serves as the database for the app
* Flask: Serves as the web-framework for the app
    * Flask-Restful: Used to develop the RESTful API for the app
    * Flask-SQLAlchemy: Used to access and modify the app's SQLite database
    * Flask-CORS: Used to enable CORS for the app
* Swagger OpenAPI: Used to create the documentation for the API developed for the app
* Matplotlib: To create the charts to view the clicks on a post.
* CSV: To create the CSV files for the user about their posts
* Secrets: To create the token for a user
* Git: Version Control

## API Design:
The RESTful API was created using the Flask-Restful library for Python according to the OpenAPI Specifications. All the
database tables have CRUD operations available through the API. The API uses tokens for authentication for certain
requests that require them. The token for a user can only be obtained from the account page of the user that is signed-in.
For more information, please refer to the openapi.yaml file.

## Architecture and Features:
The application follows the standard MVC architecture. The View of the application is created using HTML, CSS, and
Bootstrap. The Controller is created using Python and Flask. The Model is created using SQLite.

The features of the application are as follows:
* Signup and Login for users
* Ability to view user’s posts, followers, and follows
* Navigate and view other’s posts, followers, and follows
* Generate API tokens to use user specific requests
* See chart showing the clicks on a post
* Download the user’s posts and their data as a CSV file
* Ability to search, follow, and unfollow other users
* User specific feed according to the follows of the user
* Create, View, Edit, and Delete posts
* Create, View, Edit, and Delete user accounts
* Comment to express user’s opinions on posts
* RESTful API for the posts, users, comments, and follows available

## Instructions to Run the App
* Open terminal
* cd into the directory of the project
* Run ```python app.py```
* If an error occurs regarding python dependencies, run ```pip install -r requirements.txt``` and then repeat the above step.
* For further details regarding the app, refer to ```Project Report``` from the docs folder and for details regarding the API, refer to ```openapi.yaml```.

**Live Demo**: [here](https://sherrys997.github.io/blog-lite.github.io/). Please note that the demo site is static, and hence, certain things won't work.

**Video Demo**: [here](https://youtu.be/qKDkoAXw8gY)
