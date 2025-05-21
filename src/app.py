"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from pymongo import MongoClient
from bson.json_util import dumps, loads
import json

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Configuração do MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mergington_high_school']
activities_collection = db['activities']

# Dados iniciais das atividades
initial_activities = {
    "Clube de Xadrez": {
        "description": "Aprenda estratégias e participe de torneios de xadrez",
        "schedule": "Sextas, 15h30 - 17h",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Aula de Programação": {
        "description": "Aprenda fundamentos de programação e desenvolva projetos de software",
        "schedule": "Terças e quintas, 15h30 - 16h30",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Educação Física": {
        "description": "Educação física e atividades esportivas",
        "schedule": "Segundas, quartas e sextas, 14h - 15h",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    # Esportivas
    "Futebol": {
        "description": "Participe do time de futebol da escola e jogue campeonatos",
        "schedule": "Terças e quintas, 16h - 17h30",
        "max_participants": 22,
        "participants": ["lucas@mergington.edu", "marcos@mergington.edu"]
    },
    "Vôlei": {
        "description": "Aulas e treinos de vôlei para todos os níveis",
        "schedule": "Quartas e sextas, 15h - 16h30",
        "max_participants": 18,
        "participants": ["ana@mergington.edu", "carla@mergington.edu"]
    },
    # Artísticas
    "Teatro": {
        "description": "Oficina de teatro com apresentações semestrais",
        "schedule": "Segundas e quartas, 16h - 17h30",
        "max_participants": 15,
        "participants": ["bruno@mergington.edu", "lara@mergington.edu"]
    },
    "Clube de Música": {
        "description": "Aprenda instrumentos e participe da banda escolar",
        "schedule": "Sextas, 14h - 15h30",
        "max_participants": 12,
        "participants": ["rafael@mergington.edu", "juliana@mergington.edu"]
    },
    # Intelectuais
    "Olimpíada de Matemática": {
        "description": "Prepare-se para olimpíadas de matemática com aulas e desafios",
        "schedule": "Terças, 17h - 18h",
        "max_participants": 25,
        "participants": ["paulo@mergington.edu", "camila@mergington.edu"]
    },
    "Clube de Leitura": {
        "description": "Leitura e discussão de livros clássicos e contemporâneos",
        "schedule": "Quintas, 16h - 17h",
        "max_participants": 20,
        "participants": ["aline@mergington.edu", "fernando@mergington.edu"]
    }
}

# Função para inicializar o banco de dados com as atividades
def initialize_db():
    # Limpa a coleção existente
    activities_collection.delete_many({})
    
    # Insere cada atividade como um documento separado
    for name, details in initial_activities.items():
        activity_doc = details.copy()
        activity_doc["name"] = name  # Adicionando o nome como um campo
        activities_collection.insert_one(activity_doc)
    
    print("Banco de dados inicializado com as atividades")

# Inicializa o banco de dados na inicialização do aplicativo
#initialize_db()


@app.on_event("startup")
async def startup_db_client():
    """Evento que é executado na inicialização da aplicação"""
    try:
        # Verificar se a conexão com o MongoDB está funcionando
        client.admin.command('ping')
        print("Conexão com o MongoDB estabelecida com sucesso!")
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB: {e}")
        print("Certifique-se de que o servidor MongoDB está em execução")


@app.on_event("shutdown")
async def shutdown_db_client():
    """Evento que é executado no desligamento da aplicação"""
    client.close()
    print("Conexão com o MongoDB fechada")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    """Obter todas as atividades do banco de dados"""
    cursor = activities_collection.find({})
    activities_list = list(cursor)
    
    # Convertemos para um formato similar ao dicionário original
    result = {}
    for activity in activities_list:
        name = activity.pop("name")  # Removemos o nome do objeto e usamos como chave
        activity.pop("_id", None)    # Removemos o ID do MongoDB
        result[name] = activity
    
    return result


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    activity = activities_collection.find_one({"name": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")

    # Validar se o estudante já está inscrito
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Estudante já inscrito nesta atividade")
    
    # Add student to the activity in the database
    activities_collection.update_one(
        {"name": activity_name},
        {"$push": {"participants": email}}
    )
    
    return {"message": f"{email} inscrito(a) em {activity_name} com sucesso"}


@app.post("/activities/{activity_name}/remove")
def remove_participant(activity_name: str, email: str):
    """Remove um participante de uma atividade"""
    # Validate activity exists
    activity = activities_collection.find_one({"name": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")
    
    # Validate participant exists in the activity
    if email not in activity["participants"]:
        raise HTTPException(status_code=404, detail="Participante não encontrado nesta atividade")
    
    # Remove participant from the activity
    activities_collection.update_one(
        {"name": activity_name},
        {"$pull": {"participants": email}}
    )
    
    return {"message": f"{email} removido(a) de {activity_name} com sucesso"}
