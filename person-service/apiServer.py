# FastAPI-сервер

from typing import List
from fastapi import FastAPI, Path, Body, Response, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn

from init_db.db_work import DB_Work
from apiModels import PersonRequest, PersonResponse, ErrorResponse, ValidationErrorResponse

app = FastAPI(title="Person Service", version="v1")
db = DB_Work()


# ---------- обработчики ошибок ----------

# 400 Bad Request - невалидное тело запроса
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for err in exc.errors():
        # loc = ("body", "age") => берётся только "age"
        field = ".".join(str(p) for p in err["loc"] if p != "body")
        errors[field] = err["msg"]

    return JSONResponse(
        status_code=400,
        content=ValidationErrorResponse(
            message="Validation failed",
            errors=errors,
        ).model_dump(),
    )


# 404 Not Found - person не найден
@app.exception_handler(RuntimeError)
async def not_found_handler(request: Request, exc: RuntimeError):
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(message=str(exc)).model_dump(),
    )


# ---------- вспомогательные ----------

def _row_to_person(row) -> PersonResponse:
    return PersonResponse(id=row[0], name=row[1], age=row[2], address=row[3], work=row[4])


# ---------- эндпоинты ----------

# получить список всех персон
@app.get("/api/v1/persons", response_model=List[PersonResponse])
async def list_persons() -> List[PersonResponse]:
    db.execute_sql_query("SELECT id, name, age, address, work FROM persons ORDER BY id")
    rows = db.fetch_all()
    return [_row_to_person(r) for r in rows]


# создать 1 персону
@app.post("/api/v1/persons",
          status_code=201,
          responses={400: {"model": ValidationErrorResponse}},
)
async def create_person(
    response: Response,
    body: PersonRequest = Body(...),
):
    db.execute_sql_query(
        "INSERT INTO persons (name, age, address, work) VALUES (%s, %s, %s, %s) RETURNING id",
        (body.name, body.age, body.address, body.work),
    )
    new_id = db.fetch_one()[0]
    response.headers["Location"] = f"/api/v1/persons/{new_id}"
    return None


# получить 1 персону
@app.get("/api/v1/persons/{id}",
         response_model=PersonResponse,
         responses={404: {"model": ErrorResponse}})
async def get_person(id: int = Path(..., ge=1)) -> PersonResponse:
    db.execute_sql_query(
        "SELECT id, name, age, address, work FROM persons WHERE id = %s",
        (id,),
    )
    row = db.fetch_one()
    if row is None:
        raise RuntimeError("Person not found")
    return _row_to_person(row)


# изменение 1 персоны
@app.patch("/api/v1/persons/{id}",
           response_model=PersonResponse,
           responses={
                400: {"model": ValidationErrorResponse},
                404: {"model": ErrorResponse},
            })
async def edit_person(
    id: int = Path(..., ge=1),
    body: PersonRequest = Body(...),
):
    # проверка существования персоны
    db.execute_sql_query("SELECT id FROM persons WHERE id = %s", (id,))
    if db.fetch_one() is None:
        raise RuntimeError("Person not found")

    # обновляем только переданные поля (patch-семантика)
    fields = body.model_dump(exclude_unset=True)
    if fields:
        set_clause = ", ".join(f"{k} = %s" for k in fields)
        params = list(fields.values()) + [id]
        db.execute_sql_query(
            f"UPDATE persons SET {set_clause} WHERE id = %s",
            params,
        )

    # получение обновлённой персоны
    db.execute_sql_query(
        "SELECT id, name, age, address, work FROM persons WHERE id = %s",
        (id,),
    )
    return _row_to_person(db.fetch_one())


# удаление 1 персоны
@app.delete("/api/v1/persons/{id}",
            status_code=204,
            responses={404: {"model": ErrorResponse}})
async def remove_person(id: int = Path(..., ge=1)):
    # проверка существования персоны
    db.execute_sql_query("SELECT id FROM persons WHERE id = %s", (id,))
    if db.fetch_one() is None:
        raise RuntimeError("Person not found")

    db.execute_sql_query("DELETE FROM persons WHERE id = %s", (id,))
    return None


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)