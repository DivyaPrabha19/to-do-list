from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from bson.objectid import ObjectId
from datetime import datetime
import re
import os

from config import get_collection, check_connection, SECRET_KEY

app = Flask(__name__, static_folder='.')
app.secret_key = SECRET_KEY
CORS(app)


@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')


def serialize_doc(doc):
    if doc is None:
        return None
    doc['_id'] = str(doc['_id'])
    return doc


def serialize_docs(docs):
    return [serialize_doc(doc) for doc in docs]


# ==================== TASKS ====================

@app.route('/api/tasks/stats', methods=['GET'])
def get_task_stats():
    try:
        tasks_col = get_collection('tasks')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    total = tasks_col.count_documents({'deleted': {'$ne': True}, 'archived': {'$ne': True}})
    active = tasks_col.count_documents({'completed': False, 'deleted': {'$ne': True}, 'archived': {'$ne': True}})
    completed = tasks_col.count_documents({'completed': True, 'deleted': {'$ne': True}, 'archived': {'$ne': True}})
    return jsonify({'total': total, 'active': active, 'completed': completed})


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        tasks_col = get_collection('tasks')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    filter_type = request.args.get('filter', 'all')
    search_query = request.args.get('q', '').strip()

    query = {'deleted': {'$ne': True}}

    if filter_type == 'active':
        query['completed'] = False
    elif filter_type == 'completed':
        query['completed'] = True
    elif filter_type == 'high':
        query['priority'] = 'high'
    elif filter_type == 'archived':
        query = {'archived': True, 'deleted': {'$ne': True}}
    elif filter_type == 'deleted':
        query = {'deleted': True}

    if search_query:
        query['text'] = {'$regex': re.escape(search_query), '$options': 'i'}

    tasks = list(tasks_col.find(query).sort('created_at', -1))
    return jsonify(serialize_docs(tasks))


@app.route('/api/tasks', methods=['POST'])
def create_task():
    try:
        tasks_col = get_collection('tasks')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    data = request.get_json()
    if not data or not data.get('text', '').strip():
        return jsonify({'error': 'Task text is required'}), 400

    task_date = data.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    
    task = {
        'text': data['text'].strip(),
        'priority': data.get('priority', 'medium'),
        'completed': False,
        'archived': False,
        'deleted': False,
        'labels': data.get('labels', []),
        'reminder': data.get('reminder'),
        'date': task_date,
        'created_at': datetime.utcnow().isoformat(),
        'completed_at': None
    }
    result = tasks_col.insert_one(task)
    task['_id'] = result.inserted_id
    return jsonify(serialize_doc(task)), 201


@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        tasks_col = get_collection('tasks')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    update_fields = {}
    if 'text' in data:
        update_fields['text'] = data['text'].strip()
    if 'priority' in data:
        update_fields['priority'] = data['priority']
    if 'completed' in data:
        update_fields['completed'] = data['completed']
        update_fields['completed_at'] = datetime.utcnow().isoformat() if data['completed'] else None
    if 'archived' in data:
        update_fields['archived'] = data['archived']
    if 'deleted' in data:
        update_fields['deleted'] = data['deleted']
    if 'labels' in data:
        update_fields['labels'] = data['labels']
    if 'reminder' in data:
        update_fields['reminder'] = data['reminder']

    if not update_fields:
        return jsonify({'error': 'No valid fields to update'}), 400

    tasks_col.update_one({'_id': ObjectId(task_id)}, {'$set': update_fields})
    task = tasks_col.find_one({'_id': ObjectId(task_id)})
    return jsonify(serialize_doc(task))


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        tasks_col = get_collection('tasks')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    tasks_col.update_one(
        {'_id': ObjectId(task_id)},
        {'$set': {'deleted': True}}
    )
    return jsonify({'message': 'Task moved to deleted'})


@app.route('/api/tasks/<task_id>/archive', methods=['POST'])
def archive_task(task_id):
    try:
        tasks_col = get_collection('tasks')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    tasks_col.update_one(
        {'_id': ObjectId(task_id)},
        {'$set': {'archived': True}}
    )
    return jsonify({'message': 'Task archived'})


@app.route('/api/tasks/<task_id>/restore', methods=['POST'])
def restore_task(task_id):
    try:
        tasks_col = get_collection('tasks')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    tasks_col.update_one(
        {'_id': ObjectId(task_id)},
        {'$set': {'archived': False, 'deleted': False}}
    )
    return jsonify({'message': 'Task restored'})


@app.route('/api/tasks/<task_id>/permanent', methods=['DELETE'])
def permanent_delete_task(task_id):
    try:
        tasks_col = get_collection('tasks')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    tasks_col.delete_one({'_id': ObjectId(task_id)})
    return jsonify({'message': 'Task permanently deleted'})


# ==================== NOTES ====================

@app.route('/api/notes', methods=['GET'])
def get_notes():
    try:
        notes_col = get_collection('notes')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    search_query = request.args.get('q', '').strip()
    query = {}
    if search_query:
        query['$or'] = [
            {'title': {'$regex': re.escape(search_query), '$options': 'i'}},
            {'content': {'$regex': re.escape(search_query), '$options': 'i'}}
        ]
    notes = list(notes_col.find(query).sort('updated_at', -1))
    return jsonify(serialize_docs(notes))


@app.route('/api/notes', methods=['POST'])
def create_note():
    try:
        notes_col = get_collection('notes')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    data = request.get_json()
    if not data or not data.get('title', '').strip():
        return jsonify({'error': 'Note title is required'}), 400

    note = {
        'title': data['title'].strip(),
        'content': data.get('content', '').strip(),
        'date': data.get('date', datetime.utcnow().strftime('%Y-%m-%d')),
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    result = notes_col.insert_one(note)
    note['_id'] = result.inserted_id
    return jsonify(serialize_doc(note)), 201


@app.route('/api/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    try:
        notes_col = get_collection('notes')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    data = request.get_json()
    update_fields = {'updated_at': datetime.utcnow().isoformat()}
    if 'title' in data:
        update_fields['title'] = data['title'].strip()
    if 'content' in data:
        update_fields['content'] = data['content'].strip()

    notes_col.update_one({'_id': ObjectId(note_id)}, {'$set': update_fields})
    note = notes_col.find_one({'_id': ObjectId(note_id)})
    return jsonify(serialize_doc(note))


@app.route('/api/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    try:
        notes_col = get_collection('notes')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    notes_col.delete_one({'_id': ObjectId(note_id)})
    return jsonify({'message': 'Note deleted'})


# ==================== REMINDERS ====================

@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    try:
        reminders_col = get_collection('reminders')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    reminders = list(reminders_col.find({}).sort('reminder_at', 1))
    return jsonify(serialize_docs(reminders))


@app.route('/api/reminders', methods=['POST'])
def create_reminder():
    try:
        reminders_col = get_collection('reminders')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    data = request.get_json()
    if not data or not data.get('text', '').strip():
        return jsonify({'error': 'Reminder text is required'}), 400
    if not data.get('reminder_at'):
        return jsonify({'error': 'Reminder time is required'}), 400

    reminder = {
        'text': data['text'].strip(),
        'reminder_at': data['reminder_at'],
        'completed': False,
        'created_at': datetime.utcnow().isoformat()
    }
    result = reminders_col.insert_one(reminder)
    reminder['_id'] = result.inserted_id
    return jsonify(serialize_doc(reminder)), 201


@app.route('/api/reminders/<reminder_id>', methods=['PUT'])
def update_reminder(reminder_id):
    try:
        reminders_col = get_collection('reminders')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    data = request.get_json()
    update_fields = {}
    if 'text' in data:
        update_fields['text'] = data['text'].strip()
    if 'reminder_at' in data:
        update_fields['reminder_at'] = data['reminder_at']
    if 'completed' in data:
        update_fields['completed'] = data['completed']

    reminders_col.update_one({'_id': ObjectId(reminder_id)}, {'$set': update_fields})
    reminder = reminders_col.find_one({'_id': ObjectId(reminder_id)})
    return jsonify(serialize_doc(reminder))


@app.route('/api/reminders/<reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    try:
        reminders_col = get_collection('reminders')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    reminders_col.delete_one({'_id': ObjectId(reminder_id)})
    return jsonify({'message': 'Reminder deleted'})


# ==================== LABELS ====================

@app.route('/api/labels', methods=['GET'])
def get_labels():
    try:
        labels_col = get_collection('labels')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    labels = list(labels_col.find({}).sort('created_at', -1))
    return jsonify(serialize_docs(labels))


@app.route('/api/labels', methods=['POST'])
def create_label():
    try:
        labels_col = get_collection('labels')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    data = request.get_json()
    if not data or not data.get('name', '').strip():
        return jsonify({'error': 'Label name is required'}), 400

    label = {
        'name': data['name'].strip(),
        'color': data.get('color', '#667eea'),
        'created_at': datetime.utcnow().isoformat()
    }
    result = labels_col.insert_one(label)
    label['_id'] = result.inserted_id
    return jsonify(serialize_doc(label)), 201


@app.route('/api/labels/<label_id>', methods=['DELETE'])
def delete_label(label_id):
    try:
        labels_col = get_collection('labels')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    labels_col.delete_one({'_id': ObjectId(label_id)})
    return jsonify({'message': 'Label deleted'})


# ==================== SEARCH ====================

@app.route('/api/search', methods=['GET'])
def search_all():
    try:
        tasks_col = get_collection('tasks')
        notes_col = get_collection('notes')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'tasks': [], 'notes': []})

    regex = {'$regex': re.escape(query), '$options': 'i'}
    tasks = list(tasks_col.find(
        {'text': regex, 'deleted': {'$ne': True}}
    ).limit(20))
    notes = list(notes_col.find(
        {'$or': [{'title': regex}, {'content': regex}]}
    ).limit(20))

    return jsonify({
        'tasks': serialize_docs(tasks),
        'notes': serialize_docs(notes)
    })


# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    connected = check_connection()
    return jsonify({
        'status': 'ok' if connected else 'db_error',
        'database': 'connected' if connected else 'disconnected'
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
