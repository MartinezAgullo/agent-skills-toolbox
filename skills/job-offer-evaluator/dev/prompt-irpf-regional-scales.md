# Prompt: regional IRPF scales for the Spanish tax module

Paste everything below the line into a NEW chat opened in `~/.claude/skills/job-offer-evaluator`.

---

Trabajo en el skill `job-offer-evaluator` (carpeta actual). Calcula el sueldo neto de una oferta frente al actual. Quiero que el cálculo del IRPF español use la **escala autonómica real** de cada comunidad, en vez de la aproximación actual. Lee primero `SKILL.md`, `scripts/net_compare.py`, `scripts/tax/es.py`, `scripts/tax/base.py`, `data/tax_es.json` y `references/terminology.md`.

## Situación actual
- `data/tax_es.json` tiene UNA escala combinada (estatal + autonómica por defecto, que es la escala estatal duplicada) y `scripts/tax/es.py` aplica un desplazamiento manual `--irpf-shift` (puntos porcentuales sobre todos los tramos) para aproximar la comunidad. Esos desplazamientos eran estimaciones mías, sin verificar. Hay que sustituirlos por datos oficiales.

## Objetivo
Soportar estas cinco comunidades, con la escala autonómica del ejercicio 2026: **Madrid, Cataluña, Comunitat Valenciana, Andalucía y Cantabria**.

## Reglas de fiabilidad (lo más importante)
1. Todo dato sale de **documentos oficiales**: Agencia Tributaria (AEAT, manuales y algoritmo de retenciones 2026), BOE (Ley 35/2006 y leyes de presupuestos/medidas fiscales) y el boletín oficial de cada comunidad (BOCM, DOGC, DOGV, BOJA, BOC de Cantabria) o su consejería de Hacienda. No uses blogs, asesorías ni agregadores como fuente de los números. Pueden servir solo para saber dónde buscar.
2. Lee el texto real de la norma o de la tabla oficial. Si una fuente solo te llega como resumen o el texto sale cortado, dilo y marca el dato como NO verificado. No rellenes de memoria.
3. Para cada comunidad guarda: tramos y tipos de la escala autonómica general, ejercicio, URL de la fuente exacta, fecha de verificación y qué parte se leyó textualmente.
4. Contrasta cada escala con un cálculo de ejemplo: calcula la cuota total (estatal + autonómica) para 3 bases (por ejemplo 20.000, 46.000 y 80.000 €) y compárala con una fuente independiente oficial (el ejemplo práctico del manual de la AEAT o el simulador/algoritmo de retenciones de la AEAT). Si no coincide, investiga antes de seguir.
5. La comunidad que cuenta es la de **residencia fiscal** (donde se reside a 31 de diciembre), no la del lugar de trabajo ni la de la sede de la empresa. Refléjalo en la documentación y en lo que el skill pregunta.

## Diseño que quiero
- Nuevo fichero `data/tax_es_regions.json`: un objeto por comunidad con `name`, `tax_year`, `scale` (misma forma que `irpf_scale`), `verified_on`, `verified_by`, `sources`, `unverified` (lista) y `notes`. Usa un identificador en minúsculas sin tildes (`madrid`, `cataluna`, `comunitat_valenciana`, `andalucia`, `cantabria`) y acepta alias habituales ("Cataluña", "Catalunya", "Comunidad Valenciana", "Valencia", etc.).
- La escala estatal (art. 63 Ley 35/2006) debe estar separada de la autonómica en los datos. El IRPF total es estatal + autonómica. No dupliques datos: una única fuente de verdad por cosa.
- `scripts/tax/es.py`: el módulo recibe la comunidad (`--region madrid` en `net_compare.py`, con `--offer-region` para la oferta si difiere) y calcula estatal + autonómica. Mantén `--irpf-shift` solo como ajuste manual opcional, documentado como tal. Mantén el código modular, con funciones pequeñas y docstrings como las actuales; un módulo por responsabilidad.
- **Comunidad sin datos** (cualquiera que no sea de las cinco): el cálculo no debe fallar. Usa como aproximación la escala combinada actual, derivada de la escala estatal, y muestra un aviso visible, por ejemplo: "No hay datos de la comunidad '<X>'. Se usa la escala estatal sin los detalles específicos de la comunidad (tramos, tipos y deducciones autonómicas); el resultado es una aproximación." El aviso debe aparecer en la salida de `net_compare.py` y estar documentado en `SKILL.md`.
- Regímenes forales (País Vasco, Navarra), Ceuta y Melilla quedan fuera: si se piden, avisar de que no están modelados y usar el mismo fallback con el aviso.
- No modeles deducciones autonómicas (alquiler, hijos, etc.) ni mínimos personales autonómicos distintos del estatal salvo que la fuente oficial los fije para la escala general y sea sencillo. Lista en `notes` de cada comunidad lo que NO se modela.
- Actualiza `SKILL.md` (el paso que pregunta la residencia fiscal y cómo pasa la comunidad), `references/` si hace falta, y `staleness()` para que avise cuando falte verificar algo de una comunidad.

## Pruebas y entrega
- Añade un script o test pequeño (`scripts/tests/` o similar) que compruebe, para cada comunidad, la cuota de las 3 bases de ejemplo contra los valores oficiales que hayas obtenido, y que compruebe el fallback y su aviso.
- Verifica que sin `--region` los resultados actuales no cambian salvo por el aviso nuevo.
- No hagas commit. Cuando termines, dame: (1) una tabla por comunidad con los tramos y la fuente exacta, (2) qué se leyó textualmente y qué quedó sin verificar, (3) el resultado de las pruebas, (4) mensajes de commit convencionales sugeridos y el `git add` explícito de los ficheros afectados.
- Los comentarios y docstrings del código, en inglés. Tus respuestas a mí, en español.
