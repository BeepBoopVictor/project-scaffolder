# Project Scaffolder

Genera carpetas y archivos (vacíos) a partir de una estructura tipo árbol con indentación (como la que genera ChatGPT).

## Uso (binario recomendado)

### Windows
```powershell
.\scaffold.exe --spec examples\notion-janitor.txt --out .
```

### macOS / Linux

```bash
chmod +x ./scaffold
./scaffold --spec examples/notion-janitor.txt --out .
```

### Opciones útiles

Simular (no crea nada):

```powershell
./scaffold --spec examples/notion-janitor.txt --out . --dry-run
```

### Solo carpetas (sin archivos):

```powershell
./scaffold --spec examples/notion-janitor.txt --out . --no-files
```

### Indentación 4 espacios:

```powershell
./scaffold --spec examples/notion-janitor.txt --out . --indent 4
```

### Formato del spec

- Carpetas: terminan en /

- Archivos: no terminan en /

- Se ignoran comentarios con #

Ejemplo:

```
my-project/
  src/
    main.py
  README.md
```
