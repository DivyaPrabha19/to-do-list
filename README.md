# TaskMaster Pro - Smart To-Do List

A full-stack todo list application built with **Python Flask** backend and **MongoDB Atlas** database.

## Features

- Task management with priorities (Low, Medium, High)
- Voice input support
- Real-time search across tasks
- Hamburger menu with:
  - Notes
  - Reminders
  - Custom Labels
  - Archive
  - Deleted tasks
  - Settings
  - Help
- Calendar view with task previews visible directly on dates
- Study timer with motivational quotes
- MongoDB Atlas cloud database

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure MongoDB Atlas

1. Create a MongoDB Atlas account at https://www.mongodb.com/cloud/atlas
2. Create a cluster (free tier available)
3. Create a database user
4. Get your connection string from Atlas
5. Update the `.env` file with your connection string:

```
MONGODB_URI=mongodb+srv://your-username:your-password@cluster0.xxxxx.mongodb.net/todoapp?retryWrites=true&w=majority
SECRET_KEY=your-random-secret-key
```

### 3. Run the Backend Server

```bash
python app.py
```

The Flask server will start on `http://localhost:5000`

### 4. Open the Frontend

Open `index.html` in your web browser.

## API Endpoints

### Tasks
- `GET /api/tasks` - Get all tasks (supports `?filter=` and `?q=` parameters)
- `POST /api/tasks` - Create a new task
- `PUT /api/tasks/<id>` - Update a task
- `DELETE /api/tasks/<id>` - Soft delete a task
- `POST /api/tasks/<id>/archive` - Archive a task
- `POST /api/tasks/<id>/restore` - Restore a task
- `DELETE /api/tasks/<id>/permanent` - Permanently delete a task
- `GET /api/tasks/stats` - Get task statistics

### Notes
- `GET /api/notes` - Get all notes
- `POST /api/notes` - Create a note
- `PUT /api/notes/<id>` - Update a note
- `DELETE /api/notes/<id>` - Delete a note

### Reminders
- `GET /api/reminders` - Get all reminders
- `POST /api/reminders` - Create a reminder
- `PUT /api/reminders/<id>` - Update a reminder
- `DELETE /api/reminders/<id>` - Delete a reminder

### Labels
- `GET /api/labels` - Get all labels
- `POST /api/labels` - Create a label
- `DELETE /api/labels/<id>` - Delete a label

### Search
- `GET /api/search?q=query` - Search across tasks and notes

## Tech Stack

- **Backend**: Python Flask
- **Database**: MongoDB Atlas (PyMongo driver)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **API**: RESTful JSON API

## File Structure

```
todo-list/
├── app.py              # Flask backend with all API endpoints
├── config.py           # MongoDB connection configuration
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (MongoDB URI)
├── .gitignore          # Git ignore rules
├── index.html          # Frontend application
└── README.md           # This file
```
