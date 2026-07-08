"""
Script de compilação com PyInstaller
Permite customizar caminhos de saída da compilação
"""
import PyInstaller.__main__
import os
import shutil
from pathlib import Path

# Configurações
OUTPUT_DIR = "dist"  # Caminho da saída executável
BUILD_DIR = "build"  # Caminho da pasta de build
SPEC_DIR = "specs"   # Caminho para salvar arquivo .spec

# Criar diretórios se não existirem
Path(OUTPUT_DIR).mkdir(exist_ok=True)
Path(BUILD_DIR).mkdir(exist_ok=True)
Path(SPEC_DIR).mkdir(exist_ok=True)

# Executar PyInstaller com caminhos personalizados
PyInstaller.__main__.run([
    'Tarefas.pyw',
    '--onefile',
    '--noconsole',
    '--icon=icone.ico',
    '--add-data=img_ico;img_ico',
    f'--distpath={OUTPUT_DIR}',      # Define pasta de saída
    f'--buildpath={BUILD_DIR}',      # Define pasta de build
    f'--specpath={SPEC_DIR}',        # Define pasta do arquivo spec
    '--clean',                        # Limpa antes de compilar
])

print(f"\n✓ Compilação concluída!")
print(f"  Executável em: {os.path.abspath(OUTPUT_DIR)}")
print(f"  Build em: {os.path.abspath(BUILD_DIR)}")
