# -*- coding: utf-8 -*-
with open('create_document.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_save = """# Guardar documento
doc_output_path = "2do-Parcial-Informe-grupo-46.docx"
doc.save(doc_output_path)
print(f"Documento guardado exitosamente en: {doc_output_path}")"""

new_save = """# Guardar documento
doc_output_path = "2do-Parcial-Informe-grupo-46.docx"
try:
    doc.save(doc_output_path)
    print(f"Documento guardado exitosamente en: {doc_output_path}")
except PermissionError:
    doc_output_path = "2do-Parcial-Informe-grupo-46-actualizado.docx"
    doc.save(doc_output_path)
    print(f"Nota: El archivo original estaba abierto en Word. Se guardó exitosamente en: {doc_output_path}")"""

if old_save in code:
    code = code.replace(old_save, new_save)
    with open('create_document.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Manejador de guardado actualizado.")
else:
    print("No se encontró old_save.")
