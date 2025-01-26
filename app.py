from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

def get_subtasks(maintask):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        store=True,
        messages=[
            {
            "role": "user", 
            "content": f"Write a sublist or subtask list for this task in the to-do list: {maintask}. Output in html in an checkmarkable list with numbers of the subtasks. Limit the subtask list to only the title of the subtasks and to 500 characters total. Output without markdown the markdown syntax. Always output the subtasks in an ordered numbered list with checkmarkable boxes."
            }
        ]
    )
    return completion.choices[0].message.content

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    subtask = db.Column(db.String(9999), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

#with app.app_context():
#   db.create_all()

@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Todo(content=task_content)

        try: 
            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue adding your task'
    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template("index.html", tasks=tasks)


@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was a problem deleting that task'
    
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']
        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'There was an issue updating your task'
    else: 
        return render_template('update.html', task=task)
    
@app.route('/subtask/<int:id>', methods=['GET', 'POST'])
def subtask(id):
    task = Todo.query.get_or_404(id)
    if request.method == 'POST':
        task.subtask = get_subtasks(task.content)            
        try:
            db.session.commit()
            return render_template('subtask.html', task=task)
        except:
            return 'There was an issue generating your subtasks'
    else: 
        return render_template('subtask.html', task=task)

if __name__ == "__main__":
    app.run(debug=True)