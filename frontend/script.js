const codigo = document.getElementById("codigo");
const botonEjecutar = document.getElementById("ejecutar");
const botonLimpiar = document.getElementById("limpiar");
const botonInforme = document.getElementById("descargar");

const resultado = document.getElementById("resultado");
const tokens = document.getElementById("tokens");

// Elementos del diálogo del informe
const dialogo = document.getElementById("dialogo-informe");
const listaOps = document.getElementById("lista-ops");
const infError = document.getElementById("inf-error");
const campos = {
    nombre: document.getElementById("inf-nombre"),
    tipo_documento: document.getElementById("inf-tipo"),
    numero_documento: document.getElementById("inf-documento"),
    cargo: document.getElementById("inf-cargo"),
    empresa: document.getElementById("inf-empresa"),
    nit: document.getElementById("inf-nit")
};

// Operaciones exitosas de la sesión: es lo que se incluye en el informe
const sesion = [];

// Historial de comandos (flecha arriba / abajo)
const historial = [];
let indiceHistorial = 0;


function actualizarBotonInforme() {

    botonInforme.disabled = sesion.length === 0;

    botonInforme.textContent = sesion.length > 0
        ? "📄 Generar informe (" + sesion.length + ")"
        : "📄 Generar informe";
}


async function ejecutar() {

    const texto = codigo.value.trim();

    if (!texto) {
        resultado.textContent = "No se ingresó código.";
        tokens.textContent = "";
        return;
    }

    // Guardamos el comando en el historial (sin repetir el último)
    if (historial[historial.length - 1] !== texto) {
        historial.push(texto);
    }
    indiceHistorial = historial.length;

    resultado.textContent = "Ejecutando...";
    tokens.textContent = "";

    try {

        const respuesta = await fetch("/iniciar", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                codigo: texto
            })
        });

        const datos = await respuesta.json();

        if (datos.error) {

            resultado.textContent = "Error: " + String(datos.error).trim();

            if (datos.tokens) {
                tokens.textContent =
                    JSON.stringify(datos.tokens, null, 2);
            }
            return;
        }

        resultado.textContent = String(datos.resultado).trim();

        tokens.textContent =
            JSON.stringify(datos.tokens, null, 2);

        // Se agrega a la sesión (sin repetir exactamente la misma operación seguida)
        const ultima = sesion[sesion.length - 1];
        if (!ultima || ultima.codigo !== texto || ultima.resultado !== resultado.textContent) {
            sesion.push({ codigo: texto, resultado: resultado.textContent });
        }
        actualizarBotonInforme();

    } catch (error) {

        resultado.textContent =
            "No fue posible conectarse con el servidor.";

        tokens.textContent = error.toString();
    }
}


// ------------------------------------------------------------
// Informe PDF
// ------------------------------------------------------------

function leerDatosGuardados() {
    try {
        return JSON.parse(localStorage.getItem("gies_empleado")) || {};
    } catch (error) {
        return {};
    }
}

function guardarDatos(datos) {
    try {
        localStorage.setItem("gies_empleado", JSON.stringify(datos));
    } catch (error) {
        // Sin almacenamiento disponible: simplemente no se recuerdan los datos
    }
}

function dibujarListaOperaciones() {

    listaOps.textContent = "";

    if (sesion.length === 0) {
        const vacio = document.createElement("div");
        vacio.className = "op-item";
        vacio.textContent = "Todavía no hay operaciones. Ejecuta alguna y vuelve a abrir el informe.";
        listaOps.appendChild(vacio);
        return;
    }

    sesion.forEach((op, indice) => {

        const fila = document.createElement("label");
        fila.className = "op-item";

        const marca = document.createElement("input");
        marca.type = "checkbox";
        marca.checked = true;
        marca.dataset.indice = String(indice);

        const comando = document.createElement("span");
        comando.className = "op-codigo";
        comando.textContent = (indice + 1) + ". " + op.codigo;
        comando.title = op.codigo;

        const resumen = document.createElement("span");
        resumen.className = "op-resumen";
        resumen.textContent = op.resultado.split("\n")[0].slice(0, 28);

        fila.append(marca, comando, resumen);
        listaOps.appendChild(fila);
    });
}

function abrirDialogo() {

    const guardados = leerDatosGuardados();

    Object.keys(campos).forEach((clave) => {
        if (guardados[clave]) {
            campos[clave].value = guardados[clave];
        }
    });

    infError.textContent = "";
    dibujarListaOperaciones();
    dialogo.showModal();
}

async function descargarInforme() {

    const empleado = {};
    Object.keys(campos).forEach((clave) => {
        empleado[clave] = campos[clave].value.trim();
    });

    if (!empleado.nombre) {
        infError.textContent = "Escribe el nombre completo del empleado.";
        campos.nombre.focus();
        return;
    }

    if (!empleado.numero_documento) {
        infError.textContent = "Escribe el número de documento.";
        campos.numero_documento.focus();
        return;
    }

    const seleccionadas = Array.from(
        listaOps.querySelectorAll("input[type=checkbox]:checked")
    ).map((marca) => sesion[Number(marca.dataset.indice)]);

    if (seleccionadas.length === 0) {
        infError.textContent = "Selecciona al menos una operación para el informe.";
        return;
    }

    infError.textContent = "";
    guardarDatos(empleado);

    try {

        const respuesta = await fetch("/pdf", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                empleado: empleado,
                operaciones: seleccionadas
            })
        });

        if (!respuesta.ok) {
            const detalle = await respuesta.json().catch(() => ({}));
            throw new Error(detalle.detail || "El servidor no pudo generar el informe.");
        }

        const archivo = await respuesta.blob();
        const url = URL.createObjectURL(archivo);

        const enlace = document.createElement("a");
        enlace.href = url;
        enlace.download = "informe-gies.pdf";
        enlace.click();

        URL.revokeObjectURL(url);

        dialogo.close();

    } catch (error) {

        infError.textContent = "No se pudo generar el informe: " + error.message;
    }
}


botonEjecutar.addEventListener("click", ejecutar);

botonInforme.addEventListener("click", abrirDialogo);
document.getElementById("inf-descargar").addEventListener("click", descargarInforme);
document.getElementById("inf-cancelar").addEventListener("click", () => dialogo.close());

document.getElementById("vaciar-sesion").addEventListener("click", () => {
    sesion.length = 0;
    actualizarBotonInforme();
    dibujarListaOperaciones();
});

// Enter ejecuta (Shift+Enter hace salto de línea).
// Flechas ↑/↓ recorren el historial cuando el comando es de una sola línea.
codigo.addEventListener("keydown", (evento) => {

    if (evento.key === "Enter" && !evento.shiftKey) {
        evento.preventDefault();
        ejecutar();
        return;
    }

    const esUnaLinea = !codigo.value.includes("\n");

    if (evento.key === "ArrowUp" && esUnaLinea && historial.length > 0) {
        evento.preventDefault();
        indiceHistorial = Math.max(0, indiceHistorial - 1);
        codigo.value = historial[indiceHistorial];
    }

    if (evento.key === "ArrowDown" && esUnaLinea && historial.length > 0) {
        evento.preventDefault();
        indiceHistorial = Math.min(historial.length, indiceHistorial + 1);
        codigo.value = historial[indiceHistorial] || "";
    }
});


document.querySelectorAll(".hint-chip").forEach((chip) => {

    chip.addEventListener("click", () => {

        const plantilla = chip.dataset.template || chip.textContent;

        codigo.value = plantilla;
        codigo.focus();

        const inicioParentesis = plantilla.indexOf("(");
        const finParentesis = plantilla.lastIndexOf(")");

        if (inicioParentesis !== -1 && finParentesis > inicioParentesis + 1) {
            // Selecciona todo lo que está dentro de los paréntesis,
            // para que al escribir se reemplacen los parámetros de una vez.
            codigo.setSelectionRange(inicioParentesis + 1, finParentesis);
        } else {
            codigo.setSelectionRange(plantilla.length, plantilla.length);
        }
    });
});


// "Limpiar" limpia la pantalla, pero NO borra la sesión del informe
// (para no perder las operaciones por accidente; eso se hace con "Vaciar historial").
botonLimpiar.addEventListener("click", () => {

    codigo.value = "";

    resultado.textContent = "Aquí aparecerá el resultado.";

    tokens.textContent = "Aquí aparecerán los tokens.";
});