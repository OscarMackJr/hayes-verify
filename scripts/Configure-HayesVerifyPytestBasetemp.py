from pathlib import Path
import tomllib

p=Path("pyproject.toml")
text=p.read_text(encoding="utf-8")

marker='[tool.pytest.ini_options]'
if marker not in text:
    raise SystemExit("Missing [tool.pytest.ini_options]")

lines=text.splitlines()
out=[]
inside=False
saw_addopts=False
for line in lines:
    if line.startswith("[") and line.endswith("]"):
        if inside and not saw_addopts:
            out.append('addopts = "--basetemp=.pytest-temp"')
        inside=(line.strip()==marker)
        saw_addopts=False
        out.append(line)
        continue
    if inside and line.strip().startswith("addopts"):
        out.append('addopts = "--basetemp=.pytest-temp"')
        saw_addopts=True
    else:
        out.append(line)

if inside and not saw_addopts:
    out.append('addopts = "--basetemp=.pytest-temp"')

p.write_text("\n".join(out)+"\n",encoding="utf-8")
print("PASS: pyproject.toml configured with repo-local pytest basetemp.")
