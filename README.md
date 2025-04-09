# **WARD MANAGEMENT SYSTEM**
A web-based application that allows for the management of ward-related hospital operations, accessed by different roles.

## **PREREQUISITES AND PACKAGES**
Python\
Flask\
Flask-login\
SQLAlchemy 

How to run:
run by python app.py then access the link given in console

## **ARCHITECTURE**
### **FRONT END**
Works by having html templates for each page, where information is dynamically rendered by Flask. Provides interface for CRUD operations, handled by form submissions and buttons that trigger API calls to the backend.

HTML/CSS
JavaScript\
Jinja2 Template Engine - for rendering dynamic content\
AJAX - for asynchronous requests

### **BACKEND**
Works by powering the front-end via API endpoints where it receives requests from the front end, and processes that data and interacts and pushes changes within the database, then returning a response to the front end. Includes different modules for initializing the Flask application, database, handling api and logic, and mapping classes to database entities.

Flask - for python-based web framework\
Flask-login - is used for authentication\
SQLAlchemy - as ORM for database interactions

### **DATABASE**
SQLite

## **PAGES**
Login\
Dashboard\
Patient Page\
Ward Page\
Medical Records Page\
Admin Dashboard\
Users Page\
Audit Logs

## **SECURITY**
Supports password hashing, check constraints for CRUD operations, role-based permissions, and audit logs.

**ROLE-BASED ACCESS**
Admin - has access to every feature\
Doctor - view, admit, discharge, update patient and medical records\
Nurse - admit, view, update patients, view medical records, update




