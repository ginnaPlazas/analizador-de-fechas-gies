const codigo = document.getElementById("codigo");
const botonEjecutar = document.getElementById("ejecutar");
const botonLimpiar = document.getElementById("limpiar");
const botonPdf = document.getElementById("descargar");

const resultado = document.getElementById("resultado");
const tokens = document.getElementById("tokens");

// Última ejecución exitosa (la usa el botón de PDF)
let ultimoCodigo = "";
let ultimoResultado = "";

// Historial de comandos (flecha arriba / abajo)
const historial = [];
let indiceHistorial = 0;


async function ejecutar() {

    const texto = codigo.value.trim();

    if (!texto) {
        resultado.textContent = "No se ingresó código.";
        tokens.textContent = "";
        botonPdf.disabled = true;
        return;
    }

    // Guardamos el comando en el historial (sin repetir el último)
    if (historial[historial.length - 1] !== texto) {
        historial.push(texto);
    }
    indiceHistorial = historial.length;

    resultado.textContent = "Ejecutando...";
    tokens.textContent = "";
    botonPdf.disabled = true;

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

        ultimoCodigo = texto;
        ultimoResultado = resultado.textContent;
        botonPdf.disabled = false;

    } catch (error) {

        resultado.textContent =
            "No fue posible conectarse con el servidor.";

        tokens.textContent = error.toString();
    }
}


async function descargarPdf() {

    botonPdf.disabled = true;

    try {

        const respuesta = await fetch("/pdf", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                codigo: ultimoCodigo,
                resultado: ultimoResultado
            })
        });

        if (!respuesta.ok) {
            throw new Error("El servidor no pudo generar el PDF.");
        }

        const archivo = await respuesta.blob();
        const url = URL.createObjectURL(archivo);

        const enlace = document.createElement("a");
        enlace.href = url;
        enlace.download = "resultado-gies.pdf";
        enlace.click();

        URL.revokeObjectURL(url);

    } catch (error) {

        resultado.textContent = "No se pudo descargar el PDF: " + error.message;

    } finally {

        botonPdf.disabled = false;
    }
}


botonEjecutar.addEventListener("click", ejecutar);

botonPdf.addEventListener("click", descargarPdf);

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


botonLimpiar.addEventListener("click", () => {

    codigo.value = "";

    resultado.textContent = "Aquí aparecerá el resultado.";

    tokens.textContent = "Aquí aparecerán los tokens.";

    botonPdf.disabled = true;
});