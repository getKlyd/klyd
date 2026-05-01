import click
import subprocess
import json
import traceback
from .hooks import install_hooks
from .config import init_config, set_config, get_config, get_all_config
from .db import get_schema_path
import sqlite3
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.progress import Progress, SpinnerColumn, TextColumn
import rich.box

console = Console()

class KlydGroup(click.Group):
    def format_help(self, ctx, formatter):
        console.print()
        console.print(r"[cyan]888  /         888           Y88b    /       888~-_   [/cyan]")
        console.print(r"[cyan]888 /          888            Y88b  /        888   \  [/cyan]")
        console.print(r"[cyan]888/\          888             Y88b/         888    | [/cyan]")
        console.print(r"[cyan]888  \         888              Y8Y          888    | [/cyan]")
        console.print(r"[cyan]888   \        888               Y           888   /  [/cyan]")
        console.print(r"[cyan]888    \       888____          /            888_-~   [/cyan]")
        console.print(r"[dim]        (An open-source project, not affiliated with the Klyd SaaS)[/dim]")
        console.print()
        super().format_help(ctx, formatter)

@click.group(cls=KlydGroup)
def cli():
    """klyd: a CLI tool that wraps coding agents via git hooks to inject architectural memory."""
    pass

def echo_brand(msg, bold=False):
    console.print(f"[cyan bold]klyd[/cyan bold] | {msg}")

@cli.command()
def init():
    """Initialize klyd in the current git repository."""
    console.print()
    console.print(r"[cyan bold]8 8888     ,88'           8 8888                   `8.`8888.      ,8'           8 888888888o.      [/cyan bold]")
    console.print(r"[cyan bold]8 8888    ,88'            8 8888                    `8.`8888.    ,8'            8 8888    `^888.   [/cyan bold]")
    console.print(r"[cyan bold]8 8888   ,88'             8 8888                     `8.`8888.  ,8'             8 8888        `88. [/cyan bold]")
    console.print(r"[cyan bold]8 8888  ,88'              8 8888                      `8.`8888.,8'              8 8888         `88 [/cyan bold]")
    console.print(r"[cyan bold]8 8888 ,88'               8 8888                       `8.`88888'               8 8888          88 [/cyan bold]")
    console.print(r"[cyan bold]8 8888 88'                8 8888                        `8. 8888                8 8888          88 [/cyan bold]")
    console.print(r"[cyan bold]8 888888<                 8 8888                         `8 8888                8 8888         ,88 [/cyan bold]")
    console.print(r"[cyan bold]8 8888 `Y8.               8 8888                          8 8888                8 8888        ,88' [/cyan bold]")
    console.print(r"[cyan bold]8 8888   `Y8.             8 8888                          8 8888                8 8888    ,o88P'   [/cyan bold]")
    console.print(r"[cyan bold]8 8888     `Y8.           8 888888888888                  8 8888                8 888888888P'      [/cyan bold]")
    console.print(r"                   [dim](An open-source project, not affiliated with the Klyd SaaS)[/dim]")
    console.print()
    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True, console=console) as progress:
            progress.add_task(description="Creating .klyd directory, database, and hooks...", total=None)
            install_hooks()
            init_config()
            # Init DB as well
            klyd_dir = Path('.klyd')
            db_path = klyd_dir / 'memory.db'
            from .db import init_db
            init_db(str(db_path))
            
        console.print(Panel(
            "✓ Klyd harness initialised in [cyan].klyd[/cyan]\n\n[dim]Installed git hooks for automatic extraction.[/dim]\n[dim]Errors are logged to .klyd/errors.log[/dim]",
            title="Success", border_style="green"
        ))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()

@cli.command()
@click.option('--api-key', help='Anthropic API key')
@click.option('--openai-key', help='OpenAI API key')
@click.option('--openrouter-key', help='OpenRouter API key')
@click.option('--gemini-key', help='Gemini API key')
@click.option('--groq-key', help='Groq API key')
@click.option('--model', help='Model to use (default: claude-sonnet-4-6)')
@click.option('--show', is_flag=True, help='Show current configuration')
def config(api_key, openai_key, openrouter_key, gemini_key, groq_key, model, show):
    """Set klyd configuration."""
    if show:
        cfg = get_all_config()
        table = Table(title="Klyd Configuration", box=rich.box.SIMPLE)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        for k, v in cfg.items():
            if 'key' in k and v:
                v = v[:4] + '*' * (len(v) - 8) + v[-4:] if len(v) > 8 else '*' * len(v)
            table.add_row(k, v)
        console.print(table)
        return

    changes = False
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True, console=console) as progress:
        task = progress.add_task(description="Saving configuration...", total=None)
        if api_key:
            set_config('api_key', api_key)
            changes = True
        if openai_key:
            set_config('openai_key', openai_key)
            changes = True
        if openrouter_key:
            set_config('openrouter_key', openrouter_key)
            changes = True
        if gemini_key:
            set_config('gemini_key', gemini_key)
            changes = True
        if groq_key:
            set_config('groq_key', groq_key)
            changes = True
        if model:
            set_config('model', model)
            changes = True
            
    if changes:
        console.print(Panel("✓ Configuration saved.", border_style="green"))
    else:
        console.print("[yellow]Usage:[/yellow] klyd config --api-key ... --openai-key ... --model ...\nOr use --show to display current configuration.")

@cli.command(context_settings={"ignore_unknown_options": True})
@click.option('--no-inject', is_flag=True, help='Skip generating injection file')
@click.argument('cmd', nargs=-1, type=click.UNPROCESSED)
def run(no_inject, cmd):
    """Run an agent with injected architectural memory."""
    if not cmd:
        console.print("Usage: klyd run <agent> [args...]")
        return
        
    klyd_dir = Path('.klyd')
    inj_path = klyd_dir / 'injection.txt'
    
    if not no_inject:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True, console=console) as progress:
            progress.add_task(description="Preparing injection context...", total=None)
            try:
                ctx = click.get_current_context()
                ctx.invoke(prepare_injection)
            except Exception as e:
                pass
            
    run_cmd = list(cmd)
    agent_name = run_cmd[0].lower()
    
    if inj_path.exists() and inj_path.stat().st_size > 0:
        if agent_name == 'aider':
            run_cmd.extend(['--message-file', str(inj_path)])
        elif agent_name == 'opencode':
            run_cmd.extend(['-m', inj_path.read_text()])
            
    console.print(Panel(f"Launching {agent_name}...", border_style="blue", expand=False))
    
    try:
        subprocess.run(run_cmd)
        console.print(Panel("Agent session ended.", border_style="green", expand=False))
    except FileNotFoundError:
        console.print(f"[red]Command not found: {cmd[0]}[/red]")

@cli.command()
def extract_commit():
    """Extract decisions from the last commit."""
    from .extractor import extract_decisions
    from .db import get_decisions_for_files, store_decision, reinforce_decision, flag_decision
    
    klyd_dir = Path('.klyd')
    if not (klyd_dir / 'memory.db').exists():
        return
        
    try:
        # Get git info
        try:
            diff = subprocess.check_output(['git', 'diff', 'HEAD~1', 'HEAD'], text=True)
            msg = subprocess.check_output(['git', 'log', '-1', '--format=%B'], text=True)
            files_out = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'], text=True)
            files = [f for f in files_out.strip().split('\n') if f]
            commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        except subprocess.CalledProcessError:
            # Initial commit fallback
            diff = subprocess.check_output(['git', 'show', 'HEAD'], text=True)
            msg = subprocess.check_output(['git', 'log', '-1', '--format=%B'], text=True)
            files_out = subprocess.check_output(['git', 'show', '--name-only', '--format=', 'HEAD'], text=True)
            files = [f for f in files_out.strip().split('\n') if f]
            commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()

        if not files:
            return

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True, console=console) as progress:
            progress.add_task(description="Extracting decisions...", total=None)
            
            db_path = str(klyd_dir / 'memory.db')
            existing = get_decisions_for_files(db_path, files, top_k=20)
            existing_json = json.dumps(existing, indent=2)

            config_data = get_all_config()
            model = config_data.get('model', 'claude-sonnet-4-6')
            
            decisions = extract_decisions(diff, msg, existing_json, config_data, model)

            new_count = 0
            reinforced_count = 0

            for d in decisions:
                event = d.get('event_type')
                
                if event == 'REINFORCE':
                    # Find matching decision to reinforce
                    match = next((e for e in existing if e['module'] == d['module'] and e['decision'] == d['decision']), None)
                    if match:
                        reinforce_decision(db_path, match['id'], commit_hash)
                        reinforced_count += 1
                    else:
                        d['event_type'] = 'NEW'
                        store_decision(db_path, d)
                        new_count += 1
                elif event == 'CONTRADICT':
                    did = store_decision(db_path, d)
                    flag_decision(db_path, did)
                    new_count += 1
                else:
                    store_decision(db_path, d)
                    new_count += 1
                    
        console.print(f"[green]Decisions extracted: {new_count} new, {reinforced_count} reinforced[/green]")

    except Exception as e:
        err_log = klyd_dir / 'errors.log'
        with open(err_log, 'a') as f:
            f.write(f"Error extracting commit:\n{traceback.format_exc()}\n")
        return

@cli.command()
def prepare_injection():
    """Prepare injection file for agent sessions."""
    from .db import get_decisions_for_files
    from .injector import format_injection
    
    klyd_dir = Path('.klyd')
    if not (klyd_dir / 'memory.db').exists():
        return
        
    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True, console=console) as progress:
            progress.add_task(description="Preparing injection context...", total=None)
            files_out = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], text=True)
            files = [f for f in files_out.strip().split('\n') if f]
            
            if not files:
                with open(klyd_dir / 'injection.txt', 'w') as f:
                    f.write('')
                return
                
            db_path = str(klyd_dir / 'memory.db')
            decisions = get_decisions_for_files(db_path, files, top_k=20)
            
            injection = format_injection(decisions)
            with open(klyd_dir / 'injection.txt', 'w') as f:
                f.write(injection)
                
        console.print("[green]Injection written to .klyd/injection.txt[/green]")
            
    except Exception as e:
        with open(klyd_dir / 'errors.log', 'a') as f:
            f.write(f"Error preparing injection:\n{traceback.format_exc()}\n")
        return

@cli.command()
def review():
    """Review flagged conflicting decisions."""
    from .db import get_flagged_decisions, get_active_decisions_by_module, resolve_decision
    
    klyd_dir = Path('.klyd')
    db_path = klyd_dir / 'memory.db'
    if not db_path.exists():
        console.print("[red]klyd is not initialized. Run `klyd init`.[/red]")
        return

    db_str = str(db_path)
    flagged = get_flagged_decisions(db_str)
    
    if not flagged:
        console.print("[green bold]✓ No conflicts to review.[/green bold]")
        return

    for d in flagged:
        console.print()
        console.print(Panel(f"Module: [cyan bold]{d['module']}[/cyan bold]", title="[bold red]! CONFLICT DETECTED[/bold red]", border_style="red"))
        
        commit_ref = d.get('last_seen_commit') or "unknown commit"
        new_panel = Panel(f"{d['decision']}\n\n[dim cyan](from commit {commit_ref[:7]})[/dim cyan]", title="New", border_style="cyan")
        
        active = get_active_decisions_by_module(db_str, d['module'])
        old_id = None
        if active:
            old = active[0]
            old_id = old['id']
            old_panel = Panel(f"{old['decision']}\n\n[dim cyan]({old['confidence']} confidence, x{old['reinforcement_count']})[/dim cyan]", title="Existing", border_style="white")
        else:
            old_panel = Panel("(none)", title="Existing", border_style="white")

        console.print(old_panel)
        console.print(new_panel)
        
        console.print(Rule(style="dim"))
        console.print("[green bold][a][/green bold] Accept new decision (archive old)")
        console.print("[red bold][r][/red bold] Reject new decision (keep old, discard this finding)")
        console.print("[yellow bold][e][/yellow bold] Edit decision manually")
        console.print("[blue bold][s][/blue bold] Skip for now")
        
        while True:
            choice = click.prompt("Choice", type=click.Choice(['a', 'r', 'e', 's']), show_choices=False).lower()
            if choice == 's':
                console.print("[dim cyan]Skipped.[/dim cyan]")
                break
            elif choice == 'a':
                resolve_decision(db_str, d['id'], 'accept', old_id=old_id)
                console.print("[green bold]Accepted new decision.[/green bold]")
                break
            elif choice == 'r':
                resolve_decision(db_str, d['id'], 'reject')
                console.print("[red bold]Rejected new decision.[/red bold]")
                break
            elif choice == 'e':
                new_text = click.edit(d['decision'])
                if new_text is not None:
                    new_text = new_text.strip()
                    resolve_decision(db_str, d['id'], 'edit', old_id=old_id, new_text=new_text)
                    console.print("[yellow bold]Saved edited decision.[/yellow bold]")
                    break
                else:
                    console.print("[red]Edit cancelled. Please choose an option.[/red]")

@cli.command()
def status():
    """Show the current memory store status."""
    klyd_dir = Path('.klyd')
    db_path = klyd_dir / 'memory.db'
    if not db_path.exists():
        console.print("[red]klyd is not initialized. Run `klyd init`.[/red]")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM decisions WHERE archived = 0")
    all_decisions = [dict(r) for r in cur.fetchall()]
    conn.close()

    active = [d for d in all_decisions if d['flagged'] == 0]
    flagged = [d for d in all_decisions if d['flagged'] == 1]

    table = Table(title="Decision Status", box=rich.box.SIMPLE, header_style="bold cyan")
    table.add_column("ID", style="dim", max_width=8)
    table.add_column("Decision", style="white")
    table.add_column("Module", style="blue")
    table.add_column("Confidence")
    table.add_column("Event")
    table.add_column("Reinforcements", justify="right")
    table.add_column("Flagged", justify="center")

    all_display = active + flagged
    
    # Sort active by count desc, then put flagged at bottom or top.
    # Let's just sort active by reinforcements and keep flagged at the top maybe? 
    # Or just active first, then flagged.
    active.sort(key=lambda x: x['reinforcement_count'], reverse=True)
    all_display = active + flagged

    for d in all_display:
        conf_color = "green" if d['confidence'] == 'HIGH' else ("yellow" if d['confidence'] == 'MEDIUM' else "red")
        conf_styled = f"[{conf_color}]{d['confidence']}[/{conf_color}]"
        
        is_flagged = d['flagged'] == 1
        flag_styled = "[bold yellow]YES[/bold yellow]" if is_flagged else ""
        
        row_style = "bold yellow" if is_flagged else None
        
        table.add_row(
            str(d['id'])[:8],
            d['decision'],
            d['module'],
            conf_styled,
            d.get('event_type', 'NEW'),
            f"x{d['reinforcement_count']}",
            flag_styled,
            style=row_style
        )

    console.print(table)
    console.print(f"[cyan]Summary:[/cyan] {len(all_decisions)} decisions, [yellow]{len(flagged)} flagged[/yellow].")

