from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from TokenizarFechas import tokenizar
from Sintactico import AnalizadorSintactico
from GeneradorPDF import generar_pdf


app = FastAPI(
    title="GIES Language",
    description="API para ejecutar programas del lenguaje GIES",
    version="1"
)


class CodigoRequest(BaseModel):
    codigo: str


class Empleado(BaseModel):
    nombre: str
    tipo_documento: str = "CC"
    numero_documento: str
    cargo: str = ""
    empresa: str = ""
    nit: str = ""


class Operacion(BaseModel):
    codigo: str
    resultado: str


class InformeRequest(BaseModel):
    empleado: Empleado
    operaciones: list[Operacion]


ruta_frontend = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "frontend"
)

app.mount(
    "/static",
    StaticFiles(directory=ruta_frontend),
    name="static"
)


# GET para el navegador y HEAD para los chequeos de salud de Render
@app.api_route("/", methods=["GET", "HEAD"])
def inicio():

    ruta_html = os.path.join(
        ruta_frontend,
        "index.html"
    )

    return FileResponse(ruta_html)


@app.post("/iniciar")
def ejecutar_codigo(request: CodigoRequest):

    try:

        codigo = request.codigo.strip()

        if not codigo:
            return {
                "error": "No se ingreso codigo"
            }

        tokens = tokenizar(codigo)

        analizador = AnalizadorSintactico(tokens)

        resultado = analizador.revisarSintaxis()

        return {
            "exito": True,
            "resultado": resultado,
            "tokens": [
                token.to_json()
                for token in tokens
            ]
        }

    except SyntaxError as error:

        return {
            "error": str(error)
        }

    except Exception as error:

        return {
            "error": str(error)
        }


@app.post("/pdf")
def descargar_informe(request: InformeRequest):

    if not request.empleado.nombre.strip():
        raise HTTPException(status_code=400, detail="Falta el nombre del empleado")

    if not request.empleado.numero_documento.strip():
        raise HTTPException(status_code=400, detail="Falta el numero de documento")

    if not request.operaciones:
        raise HTTPException(status_code=400, detail="No hay operaciones para el informe")

    if len(request.operaciones) > 100:
        raise HTTPException(status_code=400, detail="Maximo 100 operaciones por informe")

    contenido = generar_pdf(
        request.empleado.model_dump(),
        [operacion.model_dump() for operacion in request.operaciones]
    )

    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="informe-gies.pdf"'
        }
    )