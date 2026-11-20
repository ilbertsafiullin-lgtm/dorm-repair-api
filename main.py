"""
Сервис заявок на ремонт в общежитии — учебное API на FastAPI.

Данные хранятся в обычном списке Python (без базы данных),
поэтому после перезапуска сервера добавленные заявки пропадают.
"""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="Сервис заявок на ремонт в общежитии",
    description="Студенты оставляют заявки на ремонт, сотрудники их просматривают.",
    version="1.0.0",
)


# ---------- Pydantic-модели ----------

class RepairRequestCreate(BaseModel):
    """Данные, которые присылает пользователь при создании заявки."""

    title: str = Field(..., min_length=3, max_length=100,
                       description="Краткое название проблемы",
                       examples=["Течёт кран в ванной"])
    description: str = Field(..., min_length=10, max_length=500,
                             description="Подробное описание неисправности",
                             examples=["Из-под крана капает вода, на полу лужа"])
    category: str = Field(..., min_length=3, max_length=30,
                          description="Категория: plumbing, electricity, furniture, windows и т. п.",
                          examples=["plumbing"])
    room: int = Field(..., ge=1, le=9999,
                      description="Номер комнаты", examples=[512])


class RepairRequest(RepairRequestCreate):
    """Заявка целиком — то, что возвращает сервер."""

    id: int
    status: str
    created_at: str


# ---------- Начальные данные (вместо базы данных) ----------

repair_requests: list[dict] = [
    {
        "id": 1,
        "title": "Течёт кран в ванной",
        "description": "Из-под крана капает вода, на полу образуется лужа",
        "category": "plumbing",
        "room": 512,
        "status": "new",
        "created_at": "2026-11-18T21:40:00",
    },
    {
        "id": 2,
        "title": "Не работает розетка",
        "description": "Розетка у письменного стола не подаёт ток уже два дня",
        "category": "electricity",
        "room": 314,
        "status": "in_progress",
        "created_at": "2026-11-17T10:15:00",
    },
    {
        "id": 3,
        "title": "Сломана дверца шкафа",
        "description": "Верхняя петля дверцы шкафа оторвалась, дверца не закрывается",
        "category": "furniture",
        "room": 207,
        "status": "done",
        "created_at": "2026-11-12T16:05:00",
    },
    {
        "id": 4,
        "title": "Дует из окна",
        "description": "Окно плохо закрывается, из щели сильно дует, в комнате холодно",
        "category": "windows",
        "room": 512,
        "status": "new",
        "created_at": "2026-11-19T08:30:00",
    },
    {
        "id": 5,
        "title": "Засор в раковине",
        "description": "Вода в раковине на кухне этажа уходит очень медленно",
        "category": "plumbing",
        "room": 401,
        "status": "in_progress",
        "created_at": "2026-11-16T19:20:00",
    },
]

# Счётчик для выдачи уникальных id новым заявкам
next_id = len(repair_requests) + 1


# ---------- Эндпоинты ----------

@app.get("/")
def root():
    return {"message": "Сервис заявок на ремонт работает. Документация: /docs"}


@app.get("/requests", response_model=list[RepairRequest], status_code=status.HTTP_200_OK)
def get_requests(
    category: Optional[str] = Query(
        None, description="Фильтр по категории (например, plumbing)"),
    limit: Optional[int] = Query(
        None, ge=1, description="Сколько заявок вернуть максимум"),
):
    """Список заявок с необязательным фильтром по категории и ограничением limit."""
    result = repair_requests

    if category is not None:
        result = [r for r in result if r["category"].lower() == category.lower()]

    if limit is not None:
        result = result[:limit]

    return result


@app.get("/requests/{request_id}", response_model=RepairRequest, status_code=status.HTTP_200_OK)
def get_request(request_id: int):
    """Одна заявка по id. Если такой нет — 404."""
    for r in repair_requests:
        if r["id"] == request_id:
            return r
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Заявка с id={request_id} не найдена")


@app.post("/requests", response_model=RepairRequest, status_code=status.HTTP_201_CREATED)
def create_request(data: RepairRequestCreate):
    """Создание заявки. id, статус и дату создания сервер ставит сам."""
    global next_id

    new_request = data.model_dump()
    new_request["id"] = next_id
    new_request["status"] = "new"
    new_request["created_at"] = datetime.now().isoformat(timespec="seconds")

    repair_requests.append(new_request)
    next_id += 1
    return new_request
