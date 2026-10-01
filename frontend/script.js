const codigo = document.getElementById("codigo");
const botonEjecutar = document.getElementById("ejecutar");
const botonLimpiar = document.getElementById("limpiar");

const resultado = document.getElementById("resultado");
const tokens = document.getElementById("tokens");

botonEjecutar.addEventListener("click", async () => {

    const texto = codigo.value.trim();

    if (!texto) {
        resultado.textContent = "No se ingresó código.";
        tokens.textContent = "";
        return;
    }

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

    } catch (error) {

        resultado.textContent =
            "No fue posible conectarse con el servidor.";

        tokens.textContent = error.toString();
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
           
            codigo.setSelectionRange(inicioParentesis + 1, finParentesis);
        } else {
            const idxNombre = plantilla.indexOf("nombre");
            if (idxNombre !== -1) {
                codigo.setSelectionRange(idxNombre, idxNombre + "nombre".length);
            } else {
                codigo.setSelectionRange(plantilla.length, plantilla.length);
            }
        }
    });
});

botonLimpiar.addEventListener("click", () => {

    codigo.value = "";

    resultado.textContent = "Aquí aparecerá el resultado.";

    tokens.textContent = "Aquí aparecerán los tokens.";
});