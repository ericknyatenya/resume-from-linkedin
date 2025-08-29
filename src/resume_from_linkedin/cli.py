from __future__ import annotations
import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich import print as rprint
from .parser import extract_text_from_pdf, parse_resume

def render_markdown(data, template_dir: Path, out_path: Path) -> None:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape()
    )
    tpl = env.get_template("resume.md.j2")
    md = tpl.render(**data.__dict__)
    out_path.write_text(md, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser(description="Generate Markdown resume from LinkedIn PDF export.")
    ap.add_argument("pdf", type=Path, help="Path to LinkedIn PDF (Download your data → Resume)")
    ap.add_argument("-o", "--out", type=Path, default=Path("resume.md"), help="Output Markdown path")
    ap.add_argument("-t", "--templates", type=Path, default=Path("templates"), help="Templates directory")
    args = ap.parse_args()

    if not args.pdf.exists():
        raise SystemExit(f"PDF not found: {args.pdf}")

    rprint(f"[bold green]Reading[/] {args.pdf} …")
    txt = extract_text_from_pdf(str(args.pdf))
    rprint(f"[bold green]Parsing[/] sections …")
    data = parse_resume(txt)
    rprint(f"[bold green]Rendering[/] markdown → {args.out}")
    render_markdown(data, args.templates, args.out)
    rprint("[bold cyan]Done.[/]")

if __name__ == "__main__":
    main()

