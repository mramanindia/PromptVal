from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .api import validate_directory, apply_fixes, analyze_prompt, PromptValConfig
 


app = typer.Typer(help="Validate and optionally fix prompt .txt files.")
console = Console()


@app.command()
def scan(
    directory: str = typer.Argument(..., help="Directory containing .txt prompt files"),
    report_json: Optional[str] = typer.Option(None, "--report-json", help="Write JSON report to path"),
    fix: bool = typer.Option(False, "--fix", help="Apply fixes to files"),
    out_dir: Optional[str] = typer.Option("corrected", "--out-dir", help="Directory to write corrected files"),
    in_place: bool = typer.Option(False, "--in-place", help="Overwrite files in place with .bak backups"),
    provider: Optional[str] = typer.Option(None, "--provider", help="LLM provider (openai, anthropic, gemini, xai, openai_compatible)"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name for the provider"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Base URL for OpenAI-compatible providers"),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="Request timeout (seconds)"),
    temperature: Optional[float] = typer.Option(None, "--temperature", help="Sampling temperature"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
) -> None:
	"""Run validation across all `.txt` files in a directory.

	Emits a rich CLI table and optionally writes a JSON report. With `--fix`, appends
	LLM-fixed prompts to the outputs (or to the original files with `--in-place`).
	"""
	directory_path = Path(directory)
	if not directory_path.exists() or not directory_path.is_dir():
		typer.echo(f"Directory not found: {directory}")
		raise typer.Exit(code=2)

	_apply_llm_env(provider, model, base_url, timeout, temperature)
	results = validate_directory(str(directory_path), use_llm=True)

	# CLI table summary
	table = Table(title=f"PromptVal Report: {directory_path}")
	table.add_column("File")
	table.add_column("Issues")
	table.add_column("Errors")
	table.add_column("Warnings")

	total_issues = 0
	for res in results:
		errs = sum(1 for i in res.issues if i.severity == "error")
		warns = sum(1 for i in res.issues if i.severity == "warning")
		total = len(res.issues)
		total_issues += total
		table.add_row(Path(res.file_path).name, str(total), str(errs), str(warns))
	console.print(table)

	if verbose:
		for res in results:
			if not res.issues:
				continue
			console.print(f"\n[bold]{res.file_path}[/bold]")
			for issue in res.issues:
				console.print(f"- [{issue.severity}] {issue.issue_type}: {issue.message}")
				if issue.suggestion:
					console.print(f"  Suggestion: {issue.suggestion}")

	if report_json:
		report_path = Path(report_json)
		report_path.parent.mkdir(parents=True, exist_ok=True)
		with report_path.open("w", encoding="utf-8") as f:
			json.dump([res.model_dump() for res in results], f, indent=2)
		console.print(f"JSON report written to {report_path}")

	if fix:
		if in_place:
			# create backups
			for res in results:
				src = Path(res.file_path)
				if src.exists():
					shutil.copy2(src, src.with_suffix(src.suffix + ".bak"))
		apply_fixes(results, out_dir=None if in_place else out_dir)
		console.print("Applied fixes.")

	raise typer.Exit(code=0 if total_issues == 0 else 1)


@app.command("validate")
def validate(
    directory: str = typer.Argument(..., help="Directory containing .txt prompt files"),
    report_json: Optional[str] = typer.Option(None, "--report-json", help="Write JSON report to path"),
    provider: Optional[str] = typer.Option(None, "--provider", help="LLM provider (openai, anthropic, gemini, xai, openai_compatible)"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name for the provider"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Base URL for OpenAI-compatible providers"),
    timeout: Optional[float] = typer.Option(None, "--timeout", help="Request timeout (seconds)"),
    temperature: Optional[float] = typer.Option(None, "--temperature", help="Sampling temperature"),
    apply_after_prompt: bool = typer.Option(False, "--yes", help="Auto-apply fixes without interactive prompt"),
) -> None:
	"""Generate a report and optionally apply fixes upon confirmation."""
	path = Path(directory)
	if not path.exists() or not path.is_dir():
		typer.echo(f"Directory not found: {directory}")
		raise typer.Exit(code=2)

	_apply_llm_env(provider, model, base_url, timeout, temperature)
	results = validate_directory(str(path), use_llm=True)

	table = Table(title=f"PromptVal Report: {path}")
	table.add_column("File")
	table.add_column("Issues")
	table.add_column("Errors")
	table.add_column("Warnings")
	for res in results:
		errs = sum(1 for i in res.issues if i.severity == "error")
		warns = sum(1 for i in res.issues if i.severity == "warning")
		table.add_row(Path(res.file_path).name, str(len(res.issues)), str(errs), str(warns))
	console.print(table)

	if report_json:
		report_path = Path(report_json)
		report_path.parent.mkdir(parents=True, exist_ok=True)
		report_path.write_text(json.dumps([r.model_dump() for r in results], indent=2), encoding="utf-8")
		console.print(f"JSON report written to {report_path}")

	proceed = apply_after_prompt or typer.confirm("Apply LLM-corrected prompts to output directory?", default=False)
	if proceed:
		out_dir = Path("corrected")
		out_dir.mkdir(parents=True, exist_ok=True)
		apply_fixes(results, out_dir=str(out_dir))
		console.print(f"Applied fixes to {out_dir}")


def _apply_llm_env(provider: Optional[str], model: Optional[str], base_url: Optional[str], timeout: Optional[float], temperature: Optional[float]) -> None:
    if provider:
        os.environ["PROMPTVAL_PROVIDER"] = provider
    if model:
        os.environ["PROMPTVAL_MODEL"] = model
    if base_url:
        os.environ["PROMPTVAL_BASE_URL"] = base_url
    if timeout is not None:
        os.environ["PROMPTVAL_TIMEOUT"] = str(timeout)
    if temperature is not None:
        os.environ["PROMPTVAL_TEMPERATURE"] = str(temperature)


@app.command("prompt")
def prompt(
	text: Optional[str] = typer.Option(None, "--text", help="Prompt text to analyze"),
	file: Optional[str] = typer.Option(None, "--file", help="Path to a file containing the prompt"),
	provider: Optional[str] = typer.Option(None, "--provider", help="LLM provider (openai, anthropic, gemini, xai, openai_compatible)"),
	model: Optional[str] = typer.Option(None, "--model", help="Model name for the provider"),
	base_url: Optional[str] = typer.Option(None, "--base-url", help="Base URL for OpenAI-compatible providers"),
	timeout: Optional[float] = typer.Option(None, "--timeout", help="Request timeout (seconds)"),
	temperature: Optional[float] = typer.Option(None, "--temperature", help="Sampling temperature"),
) -> None:
	"""Analyze a single prompt and print JSON to stdout."""
	if not text and not file:
		typer.echo("Provide --text or --file")
		raise typer.Exit(code=2)
	if file and not Path(file).exists():
		typer.echo(f"File not found: {file}")
		raise typer.Exit(code=2)
	content = text if text is not None else Path(file or "").read_text(encoding="utf-8")
	_apply_llm_env(provider, model, base_url, timeout, temperature)
	cfg = PromptValConfig(provider=provider, model=model, base_url=base_url, timeout=timeout, temperature=temperature)
	result = analyze_prompt(content, config=cfg)
	typer.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
	app()

